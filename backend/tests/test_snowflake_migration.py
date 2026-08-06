"""Tests verifying the SQLAlchemy-to-Snowflake migration is correct."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.models.claim import ClaimModel, AuditLogModel
from app.workflow.context import WorkflowContext
from app.workflow.state_machine import ClaimState, HUMAN_REVIEW_STATES, TERMINAL_STATES


# --- Model tests ---

class TestClaimModel:
    def test_creates_with_defaults(self):
        claim = ClaimModel(
            claim_number="CLM-1234",
            policy_number="POL-5678",
            claimant_name="John Doe",
            claim_type="Auto",
            claimed_amount=5000.0,
            incident_description="Car accident on highway",
        )
        assert claim.id  # UUID generated
        assert claim.status == "SUBMITTED"
        assert claim.risk_score == 0.0
        assert claim.copilot_recommendation == "PENDING"
        assert claim.approved_amount == 0.0
        assert claim.privacy_flags == []
        assert claim.documents == []
        assert claim.workflow_history == []
        assert claim.ai_analysis_result == {}
        assert claim.customer_communication == {}
        assert isinstance(claim.created_at, datetime)
        assert isinstance(claim.updated_at, datetime)

    def test_all_fields_assignable(self):
        claim = ClaimModel(
            id="test-id",
            claim_number="CLM-1234",
            policy_number="POL-5678",
            claimant_name="Jane",
            claim_type="Home",
            claimed_amount=10000.0,
            approved_amount=8000.0,
            status="COMPLETED",
            risk_score=0.2,
            copilot_recommendation="AUTO_APPROVE",
            incident_description="Water damage",
            redacted_description="Water damage [REDACTED]",
            privacy_flags=["SSN"],
            documents=[{"name": "report.pdf"}],
            adjuster_notes="Approved",
            customer_explanation="Your claim is approved.",
            customer_communication={"email_sent": True},
            workflow_history=[{"from_state": "SUBMITTED", "to_state": "COMPLETED"}],
            ai_analysis_result={"confidence": 0.95},
        )
        assert claim.id == "test-id"
        assert claim.approved_amount == 8000.0
        assert claim.privacy_flags == ["SSN"]


class TestAuditLogModel:
    def test_creates_with_defaults(self):
        log = AuditLogModel(claim_id="c1", action="CREATE")
        assert log.id
        assert log.performed_by == "SYSTEM_COPILOT"
        assert log.details == {}
        assert isinstance(log.timestamp, datetime)


# --- WorkflowContext tests ---

class TestWorkflowContext:
    def test_default_values(self):
        ctx = WorkflowContext(claim_id="c1", current_state="SUBMITTED")
        assert ctx.previous_state is None
        assert ctx.structured_claim == {}
        assert ctx.intermediate_outputs == {}
        assert ctx.retry_count == 0
        assert isinstance(ctx.started_at, datetime)

    def test_mutable_fields(self):
        ctx = WorkflowContext(claim_id="c1", current_state="SUBMITTED")
        ctx.current_state = "DOCUMENT_INTAKE"
        ctx.previous_state = "SUBMITTED"
        ctx.retry_count = 2
        assert ctx.current_state == "DOCUMENT_INTAKE"
        assert ctx.retry_count == 2


# --- State machine tests ---

class TestStateMachine:
    def test_human_review_states(self):
        assert ClaimState.FRAUD_REVIEW in HUMAN_REVIEW_STATES
        assert ClaimState.ADJUSTER_REVIEW in HUMAN_REVIEW_STATES
        assert ClaimState.SUBMITTED not in HUMAN_REVIEW_STATES

    def test_terminal_states(self):
        assert ClaimState.COMPLETED in TERMINAL_STATES
        assert ClaimState.REJECTED in TERMINAL_STATES
        assert ClaimState.CLAIM_ANALYSIS not in TERMINAL_STATES


# --- Database layer tests (mocked) ---

class TestDatabaseSession:
    @pytest.mark.asyncio
    async def test_execute_query_calls_sync_in_thread(self):
        with patch("app.database.session._execute_query_sync") as mock_sync:
            mock_sync.return_value = [{"id": "1"}]
            from app.database.session import execute_query
            result = await execute_query("SELECT 1")
            mock_sync.assert_called_once_with("SELECT 1", None)
            assert result == [{"id": "1"}]

    @pytest.mark.asyncio
    async def test_fetch_one_calls_sync_in_thread(self):
        with patch("app.database.session._fetch_one_sync") as mock_sync:
            mock_sync.return_value = {"id": "1", "name": "test"}
            from app.database.session import fetch_one
            result = await fetch_one("SELECT * FROM t WHERE id = %s", ("1",))
            mock_sync.assert_called_once_with("SELECT * FROM t WHERE id = %s", ("1",))
            assert result == {"id": "1", "name": "test"}

    @pytest.mark.asyncio
    async def test_fetch_all_calls_sync_in_thread(self):
        with patch("app.database.session._fetch_all_sync") as mock_sync:
            mock_sync.return_value = [{"id": "1"}, {"id": "2"}]
            from app.database.session import fetch_all
            result = await fetch_all("SELECT * FROM t")
            mock_sync.assert_called_once_with("SELECT * FROM t", None)
            assert len(result) == 2


# --- ClaimRepository tests (mocked DB) ---

class TestClaimRepository:
    @pytest.mark.asyncio
    async def test_create_claim(self):
        with patch("app.database.claim_repository.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.database.claim_repository import ClaimRepository
            repo = ClaimRepository()
            claim = ClaimModel(
                claim_number="CLM-TEST",
                policy_number="POL-TEST",
                claimant_name="Test User",
                claim_type="Auto",
                claimed_amount=1000.0,
                incident_description="Test incident",
            )
            result = await repo.create_claim(claim)
            assert result.id == claim.id
            mock_exec.assert_called_once()
            sql_arg = mock_exec.call_args[0][0]
            assert "INSERT INTO CLAIMS" in sql_arg

    @pytest.mark.asyncio
    async def test_get_claim_found(self):
        row = {
            "ID": "test-id",
            "CLAIM_NUMBER": "CLM-1",
            "POLICY_NUMBER": "POL-1",
            "CLAIMANT_NAME": "Alice",
            "CLAIM_TYPE": "Home",
            "CLAIMED_AMOUNT": 2000.0,
            "APPROVED_AMOUNT": 0.0,
            "STATUS": "SUBMITTED",
            "RISK_SCORE": 0.0,
            "COPILOT_RECOMMENDATION": "PENDING",
            "INCIDENT_DESCRIPTION": "Fire",
            "REDACTED_DESCRIPTION": "",
            "PRIVACY_FLAGS": "[]",
            "DOCUMENTS": "[]",
            "ADJUSTER_NOTES": "",
            "CUSTOMER_EXPLANATION": "",
            "CUSTOMER_COMMUNICATION": "{}",
            "WORKFLOW_HISTORY": "[]",
            "AI_ANALYSIS_RESULT": "{}",
            "CREATED_AT": "2026-01-01T00:00:00",
            "UPDATED_AT": "2026-01-01T00:00:00",
        }
        with patch("app.database.claim_repository.fetch_one", new_callable=AsyncMock, return_value=row):
            from app.database.claim_repository import ClaimRepository
            repo = ClaimRepository()
            claim = await repo.get_claim("test-id")
            assert claim is not None
            assert claim.id == "test-id"
            assert claim.claimant_name == "Alice"
            assert claim.privacy_flags == []

    @pytest.mark.asyncio
    async def test_get_claim_not_found(self):
        with patch("app.database.claim_repository.fetch_one", new_callable=AsyncMock, return_value=None):
            from app.database.claim_repository import ClaimRepository
            repo = ClaimRepository()
            claim = await repo.get_claim("nonexistent")
            assert claim is None

    @pytest.mark.asyncio
    async def test_update_claim(self):
        row = {
            "ID": "test-id",
            "CLAIM_NUMBER": "CLM-1",
            "POLICY_NUMBER": "POL-1",
            "CLAIMANT_NAME": "Alice",
            "CLAIM_TYPE": "Home",
            "CLAIMED_AMOUNT": 2000.0,
            "APPROVED_AMOUNT": 1500.0,
            "STATUS": "COMPLETED",
            "RISK_SCORE": 0.1,
            "COPILOT_RECOMMENDATION": "AUTO_APPROVE",
            "INCIDENT_DESCRIPTION": "Fire",
            "REDACTED_DESCRIPTION": "",
            "PRIVACY_FLAGS": "[]",
            "DOCUMENTS": "[]",
            "ADJUSTER_NOTES": "OK",
            "CUSTOMER_EXPLANATION": "",
            "CUSTOMER_COMMUNICATION": "{}",
            "WORKFLOW_HISTORY": "[]",
            "AI_ANALYSIS_RESULT": "{}",
            "CREATED_AT": "2026-01-01T00:00:00",
            "UPDATED_AT": "2026-01-01T00:00:00",
        }
        with patch("app.database.claim_repository.execute_query", new_callable=AsyncMock) as mock_exec, \
             patch("app.database.claim_repository.fetch_one", new_callable=AsyncMock, return_value=row):
            from app.database.claim_repository import ClaimRepository
            repo = ClaimRepository()
            result = await repo.update_claim("test-id", {"status": "COMPLETED", "approved_amount": 1500.0})
            assert result is not None
            assert result.approved_amount == 1500.0
            sql_arg = mock_exec.call_args[0][0]
            assert "UPDATE CLAIMS SET" in sql_arg


# --- StateManager tests (mocked DB) ---

class TestStateManager:
    @pytest.mark.asyncio
    async def test_load_workflow_state_initializes_new(self):
        with patch("app.services.state_manager.fetch_one", new_callable=AsyncMock, return_value=None) as mock_fetch, \
             patch("app.services.state_manager.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.services.state_manager import StateManager
            sm = StateManager()
            ctx = await sm.load_workflow_state("claim-1")
            assert ctx.claim_id == "claim-1"
            assert ctx.current_state == "SUBMITTED"
            assert ctx.retry_count == 0
            # Should have inserted initial workflow
            mock_exec.assert_called_once()
            sql_arg = mock_exec.call_args[0][0]
            assert "INSERT INTO CLAIM_WORKFLOW" in sql_arg

    @pytest.mark.asyncio
    async def test_load_workflow_state_from_existing(self):
        row = {
            "CURRENT_STATE": "FRAUD_DETECTION",
            "PREVIOUS_STATE": "PRIVACY_GUARD",
            "RETRY_COUNT": 1,
            "STARTED_AT": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }
        with patch("app.services.state_manager.fetch_one", new_callable=AsyncMock, return_value=row):
            from app.services.state_manager import StateManager
            sm = StateManager()
            ctx = await sm.load_workflow_state("claim-2")
            assert ctx.current_state == "FRAUD_DETECTION"
            assert ctx.previous_state == "PRIVACY_GUARD"
            assert ctx.retry_count == 1

    @pytest.mark.asyncio
    async def test_transition_updates_state(self):
        with patch("app.services.state_manager.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.services.state_manager import StateManager
            sm = StateManager()
            ctx = WorkflowContext(claim_id="c1", current_state="SUBMITTED")
            await sm.transition(ctx, "DOCUMENT_INTAKE", actor="ENGINE")
            assert ctx.current_state == "DOCUMENT_INTAKE"
            assert ctx.previous_state == "SUBMITTED"
            # Should have called save (MERGE) and record_event (INSERT)
            assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_mark_failed_increments_retry(self):
        with patch("app.services.state_manager.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.services.state_manager import StateManager
            sm = StateManager()
            ctx = WorkflowContext(claim_id="c1", current_state="FRAUD_DETECTION", retry_count=0)
            await sm.mark_failed(ctx, "Some error")
            assert ctx.retry_count == 1
            mock_exec.assert_called_once()
            sql_arg = mock_exec.call_args[0][0]
            assert "workflow_status = 'FAILED'" in sql_arg

    @pytest.mark.asyncio
    async def test_record_event_inserts_row(self):
        with patch("app.services.state_manager.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.services.state_manager import StateManager
            sm = StateManager()
            await sm.record_event("c1", "SUBMITTED", "DOCUMENT_INTAKE", actor="ENGINE", metadata={"key": "val"})
            mock_exec.assert_called_once()
            sql_arg = mock_exec.call_args[0][0]
            assert "INSERT INTO WORKFLOW_EVENTS" in sql_arg
            params = mock_exec.call_args[0][1]
            # metadata should be serialized JSON
            assert '"key": "val"' in params[-1]


# --- Snowflake init tests ---

class TestSnowflakeInit:
    @pytest.mark.asyncio
    async def test_init_creates_four_tables(self):
        with patch("app.database.snowflake_init.execute_query", new_callable=AsyncMock) as mock_exec:
            from app.database.snowflake_init import init_snowflake_tables
            await init_snowflake_tables()
            assert mock_exec.call_count == 4
            calls = [c[0][0] for c in mock_exec.call_args_list]
            assert any("CLAIMS" in c for c in calls)
            assert any("CLAIM_WORKFLOW" in c for c in calls)
            assert any("WORKFLOW_EVENTS" in c for c in calls)
            assert any("AUDIT_LOGS" in c for c in calls)


# --- API endpoint tests (no DB dependency) ---

class TestClaimsAPINoDbDependency:
    """Verify no endpoints require a db session parameter."""

    def test_no_db_session_in_claims_router(self):
        from app.api.v1.endpoints.claims import router
        import inspect
        for route in router.routes:
            if hasattr(route, "dependant"):
                for dep in route.dependant.dependencies:
                    # No dependency should reference get_db_session
                    assert "get_db_session" not in str(dep.call)

    def test_no_db_session_in_health_router(self):
        from app.api.v1.endpoints.health import router
        import inspect
        for route in router.routes:
            if hasattr(route, "dependant"):
                for dep in route.dependant.dependencies:
                    assert "get_db_session" not in str(dep.call)


# --- No SQLAlchemy references test ---

class TestNoSQLAlchemy:
    def test_no_sqlalchemy_in_pyproject(self):
        import pathlib
        pyproject = pathlib.Path("pyproject.toml").read_text()
        assert "sqlalchemy" not in pyproject.lower()
        assert "aiosqlite" not in pyproject.lower()

    def test_no_sqlalchemy_imports_in_app(self):
        import pathlib
        app_dir = pathlib.Path("app")
        for py_file in app_dir.rglob("*.py"):
            content = py_file.read_text()
            # Allow mention in comments/docstrings (like "replacing SQLAlchemy")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if "import" in stripped and "sqlalchemy" in stripped.lower():
                    pytest.fail(f"SQLAlchemy import found in {py_file}: {stripped}")
