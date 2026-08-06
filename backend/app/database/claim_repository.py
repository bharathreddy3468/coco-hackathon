"""Data access layer for claims and audit logs backed by Snowflake."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.session import execute_query, fetch_all, fetch_one
from app.models.claim import AuditLogModel, ClaimModel, WorkflowEventModel


# JSON/VARIANT columns that need serialization
_JSON_COLUMNS = [
    "privacy_flags",
    "documents",
    "customer_communication",
    "workflow_history",
    "ai_analysis_result",
]


from enum import Enum


def _to_primitive(val: Any) -> Any:
    """Convert Enum instances or non-standard types to Python primitives."""
    if isinstance(val, Enum):
        return val.value
    return val


def _json_default(obj: Any) -> Any:
    """JSON serializer fallback for Enum instances and custom objects."""
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def _serialize_json(value: Any) -> str:
    """Serialize a Python value to a JSON string for Snowflake VARIANT."""
    return json.dumps(value, default=_json_default) if value is not None else "null"


def _deserialize_json(value: Any) -> Any:
    """Deserialize a Snowflake VARIANT value back to Python."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _row_to_claim(row: Dict[str, Any]) -> ClaimModel:
    """Map a Snowflake row dict to a ClaimModel."""
    data = {}
    for key, value in row.items():
        lower_key = key.lower()
        if lower_key in _JSON_COLUMNS:
            data[lower_key] = _deserialize_json(value)
        elif lower_key in ("created_at", "updated_at") and isinstance(value, str):
            data[lower_key] = datetime.fromisoformat(value)
        else:
            data[lower_key] = value
    return ClaimModel(**data)


def _row_to_workflow_event(row: Dict[str, Any]) -> WorkflowEventModel:
    """Map a Snowflake row dict to a WorkflowEventModel."""
    data = {}
    for key, value in row.items():
        lower_key = key.lower()
        if lower_key == "metadata":
            data[lower_key] = _deserialize_json(value)
        elif lower_key == "timestamp" and isinstance(value, str):
            data[lower_key] = datetime.fromisoformat(value)
        else:
            data[lower_key] = value
    return WorkflowEventModel(**data)


class ClaimRepository:
    """Async data access layer for CLAIMS, CLAIM_WORKFLOW, and WORKFLOW_EVENTS tables."""

    async def create_claim(self, model: ClaimModel) -> ClaimModel:
        sql = """
        INSERT INTO CLAIMS (
            id, claim_number, policy_number, claimant_name, claim_type,
            claimed_amount, approved_amount, status, risk_score, copilot_recommendation,
            incident_description, redacted_description, privacy_flags, documents,
            adjuster_notes, customer_explanation, customer_communication,
            workflow_history, ai_analysis_result, created_at, updated_at
        )
        SELECT
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, PARSE_JSON(%s), PARSE_JSON(%s),
            %s, %s, PARSE_JSON(%s),
            PARSE_JSON(%s), PARSE_JSON(%s), %s, %s
        """
        params = (
            _to_primitive(model.id),
            _to_primitive(model.claim_number),
            _to_primitive(model.policy_number),
            _to_primitive(model.claimant_name),
            _to_primitive(model.claim_type),
            model.claimed_amount,
            model.approved_amount,
            _to_primitive(model.status),
            model.risk_score,
            _to_primitive(model.copilot_recommendation),
            model.incident_description,
            model.redacted_description,
            _serialize_json(model.privacy_flags),
            _serialize_json(model.documents),
            model.adjuster_notes,
            model.customer_explanation,
            _serialize_json(model.customer_communication),
            _serialize_json(model.workflow_history),
            _serialize_json(model.ai_analysis_result),
            model.created_at.isoformat(),
            model.updated_at.isoformat(),
        )
        await execute_query(sql, params)
        return model

    async def get_claim(self, claim_id: str) -> Optional[ClaimModel]:
        sql = "SELECT * FROM CLAIMS WHERE id = %s"
        row = await fetch_one(sql, (claim_id,))
        if row is None:
            return None
        return _row_to_claim(row)

    async def list_claims(self, limit: int = 100) -> List[ClaimModel]:
        sql = "SELECT * FROM CLAIMS ORDER BY created_at DESC LIMIT %s"
        rows = await fetch_all(sql, (limit,))
        return [_row_to_claim(r) for r in rows]

    async def update_claim(self, claim_id: str, fields: Dict[str, Any]) -> Optional[ClaimModel]:
        if not fields:
            return await self.get_claim(claim_id)

        fields["updated_at"] = datetime.now(timezone.utc).isoformat()

        set_clauses = []
        params: list = []
        for key, value in fields.items():
            if key in _JSON_COLUMNS:
                set_clauses.append(f"{key} = PARSE_JSON(%s)")
                params.append(_serialize_json(value))
            else:
                set_clauses.append(f"{key} = %s")
                params.append(_to_primitive(value))

        params.append(claim_id)
        sql = f"UPDATE CLAIMS SET {', '.join(set_clauses)} WHERE id = %s"
        await execute_query(sql, tuple(params))
        return await self.get_claim(claim_id)

    async def create_workflow_event(self, event: WorkflowEventModel) -> WorkflowEventModel:
        """Insert an event into WORKFLOW_EVENTS table."""
        sql = """
        INSERT INTO WORKFLOW_EVENTS (event_id, claim_id, event_type, from_state, to_state, actor, timestamp, metadata)
        SELECT %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s)
        """
        params = (
            _to_primitive(event.event_id),
            _to_primitive(event.claim_id),
            _to_primitive(event.event_type),
            _to_primitive(event.from_state),
            _to_primitive(event.to_state),
            _to_primitive(event.actor),
            event.timestamp.isoformat(),
            _serialize_json(event.metadata),
        )
        await execute_query(sql, params)
        return event


    async def create_audit_log(self, model: AuditLogModel) -> AuditLogModel:
        """Backward-compatible audit log recorder, maps directly into WORKFLOW_EVENTS table."""
        event = WorkflowEventModel(
            event_id=model.id,
            claim_id=model.claim_id,
            event_type=model.action,
            actor=model.performed_by,
            timestamp=model.timestamp,
            metadata=model.details,
        )
        await self.create_workflow_event(event)
        return model


# Singleton instance
claim_repository = ClaimRepository()

