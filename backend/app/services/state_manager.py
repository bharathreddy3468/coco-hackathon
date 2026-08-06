"""StateManager — central workflow persistence abstraction backed by Snowflake."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.database.session import execute_query, fetch_one
from app.workflow.context import WorkflowContext

logger = logging.getLogger(__name__)


class StateManager:
    """Manages workflow state persistence in CLAIM_WORKFLOW and WORKFLOW_EVENTS tables."""

    async def load_workflow_state(self, claim_id: str) -> WorkflowContext:
        """Load or initialize workflow state for a claim."""
        sql = "SELECT * FROM CLAIM_WORKFLOW WHERE claim_id = %s"
        row = await fetch_one(sql, (claim_id,))

        if row is None:
            ctx = WorkflowContext(claim_id=claim_id, current_state="SUBMITTED")
            await self._initialize_workflow(ctx)
            logger.info("state_loaded", extra={"claim_id": claim_id, "event": "state_loaded", "state": "SUBMITTED", "source": "initialized"})
            return ctx

        ctx = WorkflowContext(
            claim_id=claim_id,
            current_state=row.get("CURRENT_STATE") or row.get("current_state", "SUBMITTED"),
            previous_state=row.get("PREVIOUS_STATE") or row.get("previous_state"),
            retry_count=row.get("RETRY_COUNT") or row.get("retry_count", 0),
            started_at=row.get("STARTED_AT") or row.get("started_at", datetime.now(timezone.utc)),
        )
        logger.info("state_loaded", extra={"claim_id": claim_id, "event": "state_loaded", "state": ctx.current_state, "source": "persisted"})
        return ctx

    async def _initialize_workflow(self, ctx: WorkflowContext) -> None:
        """Insert initial workflow state."""
        sql = """
        INSERT INTO CLAIM_WORKFLOW (claim_id, current_state, workflow_status, retry_count, started_at, updated_at)
        VALUES (%s, %s, 'ACTIVE', 0, %s, %s)
        """
        now = ctx.started_at.isoformat()
        await execute_query(sql, (ctx.claim_id, ctx.current_state, now, now))

    async def save_workflow_state(self, ctx: WorkflowContext) -> None:
        """Persist current workflow state using MERGE."""
        now = datetime.now(timezone.utc).isoformat()
        sql = """
        MERGE INTO CLAIM_WORKFLOW AS target
        USING (SELECT %s AS claim_id) AS src
        ON target.claim_id = src.claim_id
        WHEN MATCHED THEN UPDATE SET
            current_state = %s,
            previous_state = %s,
            retry_count = %s,
            updated_at = %s
        WHEN NOT MATCHED THEN INSERT (claim_id, current_state, previous_state, workflow_status, retry_count, started_at, updated_at)
            VALUES (%s, %s, %s, 'ACTIVE', %s, %s, %s)
        """
        params = (
            ctx.claim_id,
            ctx.current_state,
            ctx.previous_state,
            ctx.retry_count,
            now,
            ctx.claim_id,
            ctx.current_state,
            ctx.previous_state,
            ctx.retry_count,
            ctx.started_at.isoformat(),
            now,
        )
        await execute_query(sql, params)
        logger.info("state_persisted", extra={"claim_id": ctx.claim_id, "event": "state_persisted", "state": ctx.current_state})

    async def transition(self, ctx: WorkflowContext, new_state: str, actor: str = "SYSTEM") -> None:
        """Transition to a new state, persist, and record event."""
        old_state = ctx.current_state
        ctx.previous_state = old_state
        ctx.current_state = new_state
        await self.save_workflow_state(ctx)
        await self.record_event(ctx.claim_id, old_state, new_state, actor)
        logger.info("state_transition", extra={
            "claim_id": ctx.claim_id,
            "event": "state_transition",
            "from_state": old_state,
            "to_state": new_state,
            "actor": actor,
        })

    async def mark_failed(self, ctx: WorkflowContext, error_message: str) -> None:
        """Mark workflow as failed, increment retry count."""
        ctx.retry_count += 1
        now = datetime.now(timezone.utc).isoformat()
        sql = """
        UPDATE CLAIM_WORKFLOW
        SET workflow_status = 'FAILED',
            retry_count = %s,
            error_message = %s,
            updated_at = %s
        WHERE claim_id = %s
        """
        await execute_query(sql, (ctx.retry_count, error_message, now, ctx.claim_id))
        logger.warning("workflow_failure", extra={
            "claim_id": ctx.claim_id,
            "event": "workflow_failure",
            "error": error_message,
            "retry_count": ctx.retry_count,
        })

    async def record_event(
        self,
        claim_id: str,
        from_state: Optional[str],
        to_state: str,
        actor: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a workflow event record."""
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else "{}"
        sql = """
        INSERT INTO WORKFLOW_EVENTS (event_id, claim_id, from_state, to_state, actor, timestamp, metadata)
        SELECT %s, %s, %s, %s, %s, %s, PARSE_JSON(%s)
        """
        await execute_query(sql, (event_id, claim_id, from_state, to_state, actor, now, meta_json))
        logger.info("workflow_event_created", extra={
            "claim_id": claim_id,
            "event": "workflow_event_created",
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
        })


# Singleton instance
state_manager = StateManager()
