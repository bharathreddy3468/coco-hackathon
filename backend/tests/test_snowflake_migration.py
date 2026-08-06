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


# --- Document Extraction Integration Tests ---

class TestDocumentExtractionIntegration:
    @pytest.mark.asyncio
    async def test_document_intake_skill_extracts_text(self):
        from app.skills.document_intake import DocumentIntakeSkill
        from app.schemas.document import DocumentContent, PageContent
        from app.services.document_extractor import UnsupportedFileTypeError

        mock_content = DocumentContent(
            document_type="pdf",
            pages=[PageContent(page=1, text="Police Incident Report 2026")],
            raw_text="Police Incident Report 2026"
        )

        skill = DocumentIntakeSkill()
        with patch("os.path.exists", return_value=True), \
             patch("app.skills.document_intake.document_extractor.extract", return_value=mock_content):

            result = await skill.run({
                "incident_description": "Car accident on main street",
                "claimed_amount": 5000.0,
                "documents": [{"name": "police_report.pdf", "path": "/tmp/police_report.pdf"}],
            })

            assert result.success is True
            out = result.output
            assert "updated_documents" in out
            updated_docs = out["updated_documents"]
            assert len(updated_docs) == 1
            assert updated_docs[0]["raw_text"] == "Police Incident Report 2026"
            assert updated_docs[0]["extraction_status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_workflow_engine_persists_extracted_documents(self):
        from app.workflow.engine import WorkflowEngine
        from app.models.claim import ClaimModel
        from app.schemas.document import DocumentContent, PageContent

        mock_content = DocumentContent(
            document_type="image",
            pages=[PageContent(page=1, text="Damage photo text")],
            raw_text="Damage photo text"
        )

        engine = WorkflowEngine()
        claim = ClaimModel(
            claim_number="CLM-DOC-1",
            policy_number="POL-1",
            claimant_name="Alice",
            claim_type="Auto",
            claimed_amount=3000.0,
            incident_description="Rear ended",
            documents=[{"name": "photo.png", "path": "/tmp/photo.png"}],
        )

        with patch("os.path.exists", return_value=True), \
             patch("app.services.document_extractor.document_extractor.extract", return_value=mock_content), \
             patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):

            next_state = await engine._run_intake_step(claim)
            assert next_state == "PRIVACY_GUARD"
            assert claim.documents[0]["raw_text"] == "Damage photo text"
            assert claim.documents[0]["extraction_status"] == "SUCCESS"


# --- Claim Parser Snowflake Cortex Tests ---

class TestClaimParserCortexIntegration:
    @pytest.mark.asyncio
    async def test_claim_parser_cortex_success(self):
        from app.skills.claim_extractor import ClaimExtractorSkill

        cortex_json = {
            "patient_name": "John Doe",
            "hospital": "City Memorial Hospital",
            "policy_number": "POL-9999",
            "diagnosis": "Acute Whiplash",
            "admission_date": "2026-02-01",
            "discharge_date": "2026-02-03",
            "procedures": ["X-Ray", "MRI Scan"],
            "billing_items": [{"description": "ER Care", "amount": 2500.0}],
            "total_claimed_amount": 2500.0
        }

        mock_db_row = {"RESPONSE": json.dumps(cortex_json)}
        skill = ClaimExtractorSkill()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_db_row):

            res = await skill.run({
                "incident_description": "Rear end collision near hospital: City Memorial Hospital. Patient: John Doe.",
                "claimant_name": "John Doe",
                "policy_number": "POL-9999",
                "claimed_amount": 2500.0
            })

            assert res.success is True
            out = res.output
            assert out["extraction_method"] == "SNOWFLAKE_CORTEX"
            structured = out["structured_claim_json"]
            assert structured["patient_name"] == "John Doe"
            assert structured["hospital"] == "City Memorial Hospital"
            assert structured["total_claimed_amount"] == 2500.0
            assert "extraction_timestamp" in out

    @pytest.mark.asyncio
    async def test_claim_parser_fallback_on_mock_or_error(self):
        from app.skills.claim_extractor import ClaimExtractorSkill

        skill = ClaimExtractorSkill()
        res = await skill.run({
            "incident_description": "Patient: Jane Smith at Hospital: Saint Jude Medical Center. Diagnosis: Fracture.",
            "claimant_name": "Jane Smith",
            "policy_number": "POL-8888",
            "claimed_amount": 4200.0
        })

        assert res.success is True
        out = res.output
        assert out["extraction_method"] == "FALLBACK_PARSER"
        structured = out["structured_claim_json"]
        assert structured["patient_name"] == "Jane Smith"
        assert structured["hospital"] == "Saint Jude Medical Center"
        assert structured["policy_number"] == "POL-8888"
        assert structured["total_claimed_amount"] == 4200.0

    @pytest.mark.asyncio
    async def test_workflow_engine_stores_cortex_parsed_claim(self):
        from app.workflow.engine import WorkflowEngine
        from app.models.claim import ClaimModel

        engine = WorkflowEngine()
        claim = ClaimModel(
            claim_number="CLM-PARSER-1",
            policy_number="POL-777",
            claimant_name="Bob Vance",
            claim_type="Health",
            claimed_amount=1500.0,
            incident_description="Medical emergency at General Hospital",
            documents=[],
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            next_state = await engine._run_intake_step(claim)
            assert next_state == "PRIVACY_GUARD"
            assert "structured_claim_json" in claim.ai_analysis_result
            structured = claim.ai_analysis_result["structured_claim_json"]
            assert structured["patient_name"] == "Bob Vance"
            assert "extraction_timestamp" in claim.ai_analysis_result


# --- Fraud Detector Snowflake Cortex Tests ---

class TestFraudDetectionCortexIntegration:
    @pytest.mark.asyncio
    async def test_fraud_detector_cortex_success(self):
        from app.skills.fraud_detector import FraudDetectorSkill

        cortex_json = {
            "fraud_confidence_score": 0.85,
            "risk_level": "HIGH",
            "fraud_reasoning": ["Unwitnessed accident", "Discrepancy in billing amount"],
            "recommendation": "SIU_INVESTIGATION"
        }
        mock_db_row = {"RESPONSE": json.dumps(cortex_json)}
        skill = FraudDetectorSkill()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_db_row):

            res = await skill.run({
                "incident_description": "Unwitnessed crash at 3 AM",
                "claimed_amount": 15000.0,
                "policy_number": "POL-FRAUD-1",
                "structured_claim": {"patient_name": "Suspicious Claim"}
            })

            assert res.success is True
            out = res.output
            assert out["fraud_confidence_score"] == 0.85
            assert out["risk_level"] == "HIGH"
            assert out["recommendation"] == "SIU_INVESTIGATION"
            assert out["exceeds_threshold"] is True

    @pytest.mark.asyncio
    async def test_fraud_detector_handles_model_failure_gracefully(self):
        from app.skills.fraud_detector import FraudDetectorSkill

        skill = FraudDetectorSkill()
        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, side_effect=Exception("Snowflake Cortex timeout")):

            res = await skill.run({
                "incident_description": "Unwitnessed incident late report",
                "claimed_amount": 12000.0,
                "policy_number": "POL-FAIL-1",
            })

            assert res.success is True
            out = res.output
            assert out["evaluation_method"] == "FALLBACK_EVALUATOR"
            assert out["fraud_confidence_score"] >= 0.50

    @pytest.mark.asyncio
    async def test_workflow_engine_fraud_step_threshold_routing(self):
        from app.workflow.engine import WorkflowEngine
        from app.models.claim import ClaimModel

        engine = WorkflowEngine()

        # Test High Risk -> FRAUD_REVIEW
        high_risk_claim = ClaimModel(
            claim_number="CLM-HIGH-1",
            policy_number="POL-HIGH",
            claimant_name="High Risk User",
            claim_type="Auto",
            claimed_amount=25000.0,
            incident_description="Unwitnessed crash late report cash payout",
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            state1 = await engine._run_fraud_step(high_risk_claim)
            assert state1 == "FRAUD_REVIEW"
            assert high_risk_claim.copilot_recommendation == "MANUAL_REVIEW"
            assert "fraud_detection" in high_risk_claim.ai_analysis_result

        # Test Low Risk -> CLAIM_ANALYSIS
        low_risk_claim = ClaimModel(
            claim_number="CLM-LOW-1",
            policy_number="POL-LOW",
            claimant_name="Low Risk User",
            claim_type="Auto",
            claimed_amount=500.0,
            incident_description="Minor fender bender witnessed by police",
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            state2 = await engine._run_fraud_step(low_risk_claim)
            assert state2 == "CLAIM_ANALYSIS"
            assert low_risk_claim.copilot_recommendation == "AUTO_APPROVE"
            assert "fraud_detection" in low_risk_claim.ai_analysis_result


# --- Shared Cortex Service Tests ---

class TestCortexService:
    @pytest.mark.asyncio
    async def test_cortex_service_returns_none_when_mock(self):
        from app.services.cortex_service import CortexService
        svc = CortexService()
        result = await svc.complete_json("test prompt", caller="test")
        # LLM_PROVIDER_MOCK is True by default in tests
        assert result is None

    @pytest.mark.asyncio
    async def test_cortex_service_parses_json_response(self):
        from app.services.cortex_service import CortexService
        svc = CortexService()

        mock_row = {"RESPONSE": json.dumps({"key": "value", "score": 0.95})}
        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_row):
            result = await svc.complete_json("test prompt", caller="test")
            assert result is not None
            assert result["key"] == "value"
            assert result["score"] == 0.95

    @pytest.mark.asyncio
    async def test_cortex_service_handles_markdown_code_blocks(self):
        from app.services.cortex_service import CortexService
        svc = CortexService()

        raw_response = '```json\n{"key": "value"}\n```'
        mock_row = {"RESPONSE": raw_response}
        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_row):
            result = await svc.complete_json("test prompt", caller="test")
            assert result is not None
            assert result["key"] == "value"

    @pytest.mark.asyncio
    async def test_cortex_service_retries_on_failure(self):
        from app.services.cortex_service import CortexService
        svc = CortexService()

        call_count = 0
        async def failing_then_success(sql, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return {"RESPONSE": json.dumps({"result": "success"})}

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", side_effect=failing_then_success):
            result = await svc.complete_json("test prompt", caller="test")
            assert result is not None
            assert result["result"] == "success"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_cortex_service_returns_none_after_all_retries_fail(self):
        from app.services.cortex_service import CortexService
        svc = CortexService()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, side_effect=Exception("Permanent failure")):
            result = await svc.complete_json("test prompt", caller="test")
            assert result is None


# --- Claim Analysis Cortex Tests ---

class TestClaimAnalysisCortexIntegration:
    @pytest.mark.asyncio
    async def test_claim_analysis_cortex_success(self):
        from app.skills.claim_analysis import ClaimAnalysisSkill

        cortex_json = {
            "recommended_amount": 4500.0,
            "confidence": 0.92,
            "covered_items": ["Emergency Room Visit", "X-Ray"],
            "excluded_items": ["Cosmetic procedure"],
            "coverage_summary": "Claim approved with standard deductible applied.",
            "policy_clauses": ["Section 4.1", "Section 5.2"],
            "internal_reasoning": ["All procedures within coverage limits."]
        }
        mock_row = {"RESPONSE": json.dumps(cortex_json)}
        skill = ClaimAnalysisSkill()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_row):

            res = await skill.run({
                "claimed_amount": 5000.0,
                "policy_number": "POL-ANALYSIS-1",
                "structured_claim": {"patient_name": "Test Patient"},
                "fraud_review_result": {"risk_level": "LOW"},
            })

            assert res.success is True
            out = res.output
            assert out["recommended_amount"] == 4500.0
            assert out["confidence"] == 0.92
            assert "Emergency Room Visit" in out["covered_items"]
            assert "Cosmetic procedure" in out["excluded_items"]
            assert out["evaluation_method"] == "SNOWFLAKE_CORTEX"

    @pytest.mark.asyncio
    async def test_claim_analysis_fallback(self):
        from app.skills.claim_analysis import ClaimAnalysisSkill

        skill = ClaimAnalysisSkill()
        res = await skill.run({
            "claimed_amount": 3000.0,
            "policy_number": "POL-FALLBACK-1",
        })

        assert res.success is True
        out = res.output
        assert out["evaluation_method"] == "FALLBACK_ANALYZER"
        assert out["recommended_amount"] == 2500.0  # 3000 - 500 deductible
        assert out["is_covered"] is True
        assert out["policy_active"] is True

    @pytest.mark.asyncio
    async def test_claim_analysis_expired_policy(self):
        from app.skills.claim_analysis import ClaimAnalysisSkill

        skill = ClaimAnalysisSkill()
        res = await skill.run({
            "claimed_amount": 3000.0,
            "policy_number": "EXPIRED-POL-1",
        })

        assert res.success is True
        out = res.output
        assert out["is_covered"] is False
        assert out["policy_active"] is False


# --- Semantic Bridge Cortex Tests ---

class TestSemanticBridgeCortexIntegration:
    @pytest.mark.asyncio
    async def test_semantic_bridge_cortex_success(self):
        from app.skills.semantic_bridge import SemanticBridgeSkill

        cortex_json = {
            "customer_explanation": "Dear John, your insurance claim has been approved. We will process a payment of $4,500.00 to your account."
        }
        mock_row = {"RESPONSE": json.dumps(cortex_json)}
        skill = SemanticBridgeSkill()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_row):

            res = await skill.run({
                "claimant_name": "John",
                "policy_number": "POL-SEM-1",
                "claimed_amount": 5000.0,
                "approved_amount": 4500.0,
                "status": "APPROVED",
                "adjuster_notes": "Looks good",
            })

            assert res.success is True
            out = res.output
            assert "approved" in out["customer_explanation"].lower()
            assert out["translation_method"] == "SNOWFLAKE_CORTEX"

    @pytest.mark.asyncio
    async def test_semantic_bridge_fallback_approved(self):
        from app.skills.semantic_bridge import SemanticBridgeSkill

        skill = SemanticBridgeSkill()
        res = await skill.run({
            "claimant_name": "Alice",
            "policy_number": "POL-SEM-2",
            "claimed_amount": 3000.0,
            "approved_amount": 2500.0,
            "status": "APPROVED",
            "adjuster_notes": "",
        })

        assert res.success is True
        out = res.output
        assert "Alice" in out["customer_explanation"]
        assert "approved" in out["customer_explanation"].lower()
        assert out["translation_method"] == "FALLBACK_GENERATOR"

    @pytest.mark.asyncio
    async def test_semantic_bridge_fallback_rejected(self):
        from app.skills.semantic_bridge import SemanticBridgeSkill

        skill = SemanticBridgeSkill()
        res = await skill.run({
            "claimant_name": "Bob",
            "policy_number": "POL-SEM-3",
            "claimed_amount": 3000.0,
            "approved_amount": 0.0,
            "status": "REJECTED",
            "adjuster_notes": "Policy expired",
        })

        assert res.success is True
        out = res.output
        assert "Bob" in out["customer_explanation"]
        assert "unable to approve" in out["customer_explanation"].lower()


# --- Customer Communication Cortex Tests ---

class TestCustomerCommunicationCortexIntegration:
    @pytest.mark.asyncio
    async def test_customer_comm_cortex_success(self):
        from app.skills.customer_comm import CustomerCommunicationSkill

        cortex_json = {
            "subject": "Your Claim CLM-COMM-1 Has Been Processed",
            "body": "Dear customer, your claim has been approved.",
            "approval_message": "Your claim for $5,000 has been approved with a payout of $4,500.",
            "rejection_message": "",
            "additional_documents_requested": "",
            "appeal_guidance": ""
        }
        mock_row = {"RESPONSE": json.dumps(cortex_json)}
        skill = CustomerCommunicationSkill()

        with patch("app.config.settings.settings.LLM_PROVIDER_MOCK", False), \
             patch("app.services.cortex_service.fetch_one", new_callable=AsyncMock, return_value=mock_row):

            res = await skill.run({
                "claim_number": "CLM-COMM-1",
                "customer_explanation": "Your claim has been approved.",
                "workflow_outcome": "AUTO_APPROVE",
            })

            assert res.success is True
            out = res.output
            assert out["dispatch_status"] == "SENT"
            assert out["generation_method"] == "SNOWFLAKE_CORTEX"
            assert "approved" in out["approval_message"].lower()

    @pytest.mark.asyncio
    async def test_customer_comm_fallback(self):
        from app.skills.customer_comm import CustomerCommunicationSkill

        skill = CustomerCommunicationSkill()
        res = await skill.run({
            "claim_number": "CLM-COMM-2",
            "customer_explanation": "Your claim has been approved with a payout of $2,500.",
            "workflow_outcome": "AUTO_APPROVE",
        })

        assert res.success is True
        out = res.output
        assert out["dispatch_status"] == "SENT"
        assert out["generation_method"] == "FALLBACK_GENERATOR"
        assert out["body"] == "Your claim has been approved with a payout of $2,500."

    @pytest.mark.asyncio
    async def test_customer_comm_never_exposes_internal_data(self):
        from app.skills.customer_comm import CustomerCommunicationSkill

        skill = CustomerCommunicationSkill()
        res = await skill.run({
            "claim_number": "CLM-COMM-3",
            "customer_explanation": "We are unable to approve your claim.",
            "workflow_outcome": "REJECTED",
        })

        assert res.success is True
        out = res.output
        # Verify internal data fields are not exposed in the body
        assert "fraud_score" not in out.get("body", "").lower()
        assert "internal_reasoning" not in out.get("body", "").lower()
        assert out["appeal_guidance"] != ""  # Should have appeal guidance for rejections


# --- Workflow Engine End-to-End Integration Tests ---

class TestWorkflowEngineEndToEnd:
    @pytest.mark.asyncio
    async def test_analysis_step_passes_structured_claim_and_fraud(self):
        """Verify analysis step receives structured claim and fraud detection results."""
        from app.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()
        claim = ClaimModel(
            claim_number="CLM-E2E-1",
            policy_number="POL-E2E",
            claimant_name="E2E User",
            claim_type="Health",
            claimed_amount=5000.0,
            incident_description="Medical procedure",
            ai_analysis_result={
                "structured_claim_json": {"patient_name": "E2E User", "diagnosis": "Sprain"},
                "fraud_detection": {"risk_level": "LOW", "fraud_confidence_score": 0.1},
            },
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            next_state = await engine._run_analysis_step(claim)
            assert next_state == "ADJUSTER_REVIEW"
            assert claim.approved_amount > 0
            assert "claim_analysis" in claim.ai_analysis_result
            analysis = claim.ai_analysis_result["claim_analysis"]
            assert "recommended_amount" in analysis
            assert "covered_items" in analysis
            assert "policy_clauses" in analysis

    @pytest.mark.asyncio
    async def test_semantic_step_receives_analysis_and_adjuster_notes(self):
        """Verify semantic bridge receives claim analysis and adjuster notes."""
        from app.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()
        claim = ClaimModel(
            claim_number="CLM-E2E-2",
            policy_number="POL-E2E",
            claimant_name="Semantic User",
            claim_type="Auto",
            claimed_amount=3000.0,
            approved_amount=2500.0,
            incident_description="Fender bender",
            adjuster_notes="Approved - standard claim",
            status="SEMANTIC_BRIDGE",
            ai_analysis_result={
                "claim_analysis": {
                    "recommended_amount": 2500.0,
                    "policy_clauses": ["Section 4.1"],
                },
            },
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            next_state = await engine._run_semantic_step(claim)
            assert next_state == "CUSTOMER_COMMUNICATION"
            assert claim.customer_explanation != ""
            assert "semantic_bridge" in claim.ai_analysis_result

    @pytest.mark.asyncio
    async def test_comm_step_generates_dispatch_and_completes(self):
        """Verify customer communication step generates dispatch and returns COMPLETED."""
        from app.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()
        claim = ClaimModel(
            claim_number="CLM-E2E-3",
            policy_number="POL-E2E",
            claimant_name="Comm User",
            claim_type="Health",
            claimed_amount=5000.0,
            approved_amount=4500.0,
            incident_description="Medical claim",
            customer_explanation="Your claim has been approved for $4,500.",
            copilot_recommendation="AUTO_APPROVE",
        )

        with patch("app.workflow.engine.WorkflowEngine._record_audit", new_callable=AsyncMock):
            next_state = await engine._run_comm_step(claim)
            assert next_state == "COMPLETED"
            assert claim.customer_communication != {}
            assert claim.customer_communication.get("dispatch_status") == "SENT"
            assert "customer_communication" in claim.ai_analysis_result
