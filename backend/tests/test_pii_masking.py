"""Tests verifying PII masking guardrail behaviour.

Covers:
- PII config completeness
- Flat and nested dict redaction
- Deep-copy guarantee (original never mutated)
- Non-PII fields preserved
- Edge cases (empty, missing, None values)
- Integration: workflow engine passes sanitized data to skills
"""

import copy
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.pii_config import PII_FIELDS, PII_REDACTED_VALUE
from app.services.pii_masking_service import PIIMaskingService, pii_masking_service


# ---------------------------------------------------------------------------
# PII Config tests
# ---------------------------------------------------------------------------

class TestPIIConfig:
    """Verify the PII configuration module."""

    def test_pii_fields_is_nonempty_list(self):
        assert isinstance(PII_FIELDS, list)
        assert len(PII_FIELDS) > 0

    def test_required_fields_present(self):
        required = {
            "patient_name", "claimant_name", "phone", "email",
            "address", "aadhaar", "passport", "insurance_id",
            "policy_number", "claim_number",
        }
        assert required.issubset(set(PII_FIELDS))

    def test_redacted_value_is_string(self):
        assert isinstance(PII_REDACTED_VALUE, str)
        assert len(PII_REDACTED_VALUE) > 0


# ---------------------------------------------------------------------------
# PII Masking Service — unit tests
# ---------------------------------------------------------------------------

class TestPIIMaskingServiceFlat:
    """Flat (non-nested) dict redaction."""

    def test_redacts_known_pii_fields(self):
        data = {
            "patient_name": "John Doe",
            "policy_number": "POL-2026-1234",
            "claimed_amount": 5000.0,
        }
        result = pii_masking_service.sanitize_input(data)

        assert result["patient_name"] == PII_REDACTED_VALUE
        assert result["policy_number"] == PII_REDACTED_VALUE
        # Non-PII field must survive
        assert result["claimed_amount"] == 5000.0

    def test_preserves_non_pii_fields(self):
        data = {
            "incident_description": "Car accident on I-95",
            "claimed_amount": 12000.0,
            "status": "SUBMITTED",
        }
        result = pii_masking_service.sanitize_input(data)

        assert result == data  # nothing changed

    def test_original_dict_not_mutated(self):
        data = {"patient_name": "Jane Doe", "claimed_amount": 100.0}
        original_copy = copy.deepcopy(data)

        _ = pii_masking_service.sanitize_input(data)

        # The input dict MUST be identical to its snapshot before the call
        assert data == original_copy

    def test_case_insensitive_matching(self):
        """Field matching should be case-insensitive."""
        data = {"Patient_Name": "John", "POLICY_NUMBER": "POL-1"}
        result = pii_masking_service.sanitize_input(data)

        assert result["Patient_Name"] == PII_REDACTED_VALUE
        assert result["POLICY_NUMBER"] == PII_REDACTED_VALUE


class TestPIIMaskingServiceNested:
    """Nested / recursive dict redaction."""

    def test_redacts_nested_pii_in_structured_claim(self):
        data = {
            "claimed_amount": 5000.0,
            "structured_claim": {
                "patient_name": "Alice Smith",
                "policy_number": "POL-9999",
                "diagnosis": "Fracture",
                "hospital": "General Hospital",
            },
        }
        result = pii_masking_service.sanitize_input(data)

        assert result["structured_claim"]["patient_name"] == PII_REDACTED_VALUE
        assert result["structured_claim"]["policy_number"] == PII_REDACTED_VALUE
        # Non-PII nested fields preserved
        assert result["structured_claim"]["diagnosis"] == "Fracture"
        assert result["structured_claim"]["hospital"] == "General Hospital"
        assert result["claimed_amount"] == 5000.0

    def test_redacts_pii_in_list_of_dicts(self):
        data = {
            "records": [
                {"patient_name": "Bob", "amount": 100},
                {"patient_name": "Carol", "amount": 200},
            ]
        }
        result = pii_masking_service.sanitize_input(data)

        for record in result["records"]:
            assert record["patient_name"] == PII_REDACTED_VALUE

    def test_deeply_nested_redaction(self):
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "email": "user@example.com",
                        "safe_field": "keep me",
                    }
                }
            }
        }
        result = pii_masking_service.sanitize_input(data)

        assert result["level1"]["level2"]["level3"]["email"] == PII_REDACTED_VALUE
        assert result["level1"]["level2"]["level3"]["safe_field"] == "keep me"

    def test_original_nested_dict_not_mutated(self):
        data = {
            "structured_claim": {
                "patient_name": "Alice",
                "hospital": "City Hospital",
            }
        }
        snapshot = copy.deepcopy(data)

        _ = pii_masking_service.sanitize_input(data)

        assert data == snapshot


class TestPIIMaskingServiceEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_dict(self):
        assert pii_masking_service.sanitize_input({}) == {}

    def test_none_pii_values(self):
        data = {"patient_name": None, "claimed_amount": 0}
        result = pii_masking_service.sanitize_input(data)
        assert result["patient_name"] == PII_REDACTED_VALUE

    def test_numeric_pii_values(self):
        data = {"phone": 1234567890, "amount": 500}
        result = pii_masking_service.sanitize_input(data)
        assert result["phone"] == PII_REDACTED_VALUE
        assert result["amount"] == 500

    def test_empty_string_pii_values(self):
        data = {"email": "", "status": "OK"}
        result = pii_masking_service.sanitize_input(data)
        assert result["email"] == PII_REDACTED_VALUE
        assert result["status"] == "OK"

    def test_custom_pii_fields(self):
        """A service instantiated with custom fields should only redact those."""
        svc = PIIMaskingService(pii_fields=["secret_field"], redacted_value="***")
        data = {"secret_field": "top secret", "patient_name": "Alice"}
        result = svc.sanitize_input(data)

        assert result["secret_field"] == "***"
        # patient_name is NOT in this custom service's PII list
        assert result["patient_name"] == "Alice"


# ---------------------------------------------------------------------------
# Integration: workflow engine feeds sanitized data to skills
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_snowflake_imports():
    """Mock snowflake.connector so we can import the workflow engine even when
    the Snowflake driver is not installed locally."""
    modules_to_mock = [
        "snowflake",
        "snowflake.connector",
        "snowflake.connector.pandas_tools",
    ]
    originals = {}
    for mod in modules_to_mock:
        originals[mod] = sys.modules.get(mod)
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()

    yield

    for mod in modules_to_mock:
        if originals[mod] is None:
            sys.modules.pop(mod, None)
        else:
            sys.modules[mod] = originals[mod]


class TestWorkflowEnginePIIIntegration:
    """Verify that the workflow engine passes only sanitized data to AI Skills."""

    def _make_claim(self):
        from app.models.claim import ClaimModel
        return ClaimModel(
            id="test-claim-id",
            claim_number="CLM-ABC123",
            policy_number="POL-2026-SECRET",
            claimant_name="Sensitive Person",
            claim_type="Auto",
            claimed_amount=5000.0,
            incident_description="Car accident on highway",
            redacted_description="Car accident on highway",
            ai_analysis_result={
                "structured_claim_json": {
                    "patient_name": "Sensitive Person",
                    "policy_number": "POL-2026-SECRET",
                    "hospital": "General Hospital",
                    "diagnosis": "Whiplash",
                },
                "fraud_detection": {
                    "fraud_confidence_score": 0.1,
                    "risk_level": "LOW",
                },
                "claim_analysis": {
                    "recommended_amount": 4500.0,
                    "policy_clauses": ["Section 4.1"],
                },
            },
            approved_amount=4500.0,
            copilot_recommendation="AUTO_APPROVE",
            customer_explanation="Your claim has been approved.",
        )

    def _make_mock_skill(self, output: dict):
        """Create a mock skill whose .run() captures input and returns given output."""
        captured_input = {}

        async def mock_run(input_data):
            captured_input.update(input_data)
            result = MagicMock()
            result.output = output
            result.model_dump = lambda: {"output": output, "success": True}
            result.success = True
            return result

        skill = MagicMock()
        skill.run = mock_run
        return skill, captured_input

    @pytest.mark.asyncio
    async def test_fraud_step_receives_sanitized_input(self, mock_snowflake_imports):
        from app.workflow.engine import WorkflowEngine
        from app.workflow.state_machine import ClaimState

        engine = WorkflowEngine()
        claim = self._make_claim()

        skill, captured = self._make_mock_skill({
            "fraud_confidence_score": 0.1,
            "risk_level": "LOW",
            "fraud_reasoning": [],
            "recommendation": "AUTO_APPROVE",
        })

        with patch("app.database.claim_repository.claim_repository") as mock_repo, \
             patch("app.skills.STATE_SKILL_MAPPING", {ClaimState.FRAUD_DETECTION: skill}):
            mock_repo.create_audit_log = AsyncMock()
            await engine._run_fraud_step(claim)

        # PII must be redacted
        assert captured["policy_number"] == PII_REDACTED_VALUE
        assert captured["structured_claim"]["patient_name"] == PII_REDACTED_VALUE
        assert captured["structured_claim"]["policy_number"] == PII_REDACTED_VALUE
        # Non-PII preserved
        assert captured["claimed_amount"] == 5000.0
        assert captured["structured_claim"]["hospital"] == "General Hospital"
        # Original claim untouched
        assert claim.policy_number == "POL-2026-SECRET"

    @pytest.mark.asyncio
    async def test_analysis_step_receives_sanitized_input(self, mock_snowflake_imports):
        from app.workflow.engine import WorkflowEngine
        from app.workflow.state_machine import ClaimState

        engine = WorkflowEngine()
        claim = self._make_claim()

        skill, captured = self._make_mock_skill({
            "recommended_amount": 4500.0,
            "confidence": 0.95,
            "covered_items": [], "excluded_items": [],
            "coverage_summary": "", "policy_clauses": [],
            "internal_reasoning": [], "evaluation_method": "SNOWFLAKE_CORTEX",
        })

        with patch("app.database.claim_repository.claim_repository") as mock_repo, \
             patch("app.skills.STATE_SKILL_MAPPING", {ClaimState.CLAIM_ANALYSIS: skill}):
            mock_repo.create_audit_log = AsyncMock()
            await engine._run_analysis_step(claim)

        assert captured["policy_number"] == PII_REDACTED_VALUE
        assert captured["structured_claim"]["patient_name"] == PII_REDACTED_VALUE
        assert claim.policy_number == "POL-2026-SECRET"

    @pytest.mark.asyncio
    async def test_semantic_step_receives_sanitized_input(self, mock_snowflake_imports):
        from app.workflow.engine import WorkflowEngine
        from app.workflow.state_machine import ClaimState

        engine = WorkflowEngine()
        claim = self._make_claim()

        skill, captured = self._make_mock_skill({
            "customer_explanation": "Approved.",
            "tone": "Professional", "audience": "Policyholder",
            "translation_method": "FALLBACK_GENERATOR",
        })

        with patch("app.database.claim_repository.claim_repository") as mock_repo, \
             patch("app.skills.STATE_SKILL_MAPPING", {ClaimState.SEMANTIC_BRIDGE: skill}):
            mock_repo.create_audit_log = AsyncMock()
            await engine._run_semantic_step(claim)

        assert captured["claimant_name"] == PII_REDACTED_VALUE
        assert captured["policy_number"] == PII_REDACTED_VALUE
        assert claim.claimant_name == "Sensitive Person"

    @pytest.mark.asyncio
    async def test_comm_step_receives_sanitized_input(self, mock_snowflake_imports):
        from app.workflow.engine import WorkflowEngine
        from app.workflow.state_machine import ClaimState

        engine = WorkflowEngine()
        claim = self._make_claim()

        skill, captured = self._make_mock_skill({
            "channel": "EMAIL_AND_PORTAL",
            "subject": "Update", "body": "Approved.",
            "dispatch_status": "SENT",
        })

        with patch("app.database.claim_repository.claim_repository") as mock_repo, \
             patch("app.skills.STATE_SKILL_MAPPING", {ClaimState.CUSTOMER_COMMUNICATION: skill}):
            mock_repo.create_audit_log = AsyncMock()
            await engine._run_comm_step(claim)

        assert captured["claim_number"] == PII_REDACTED_VALUE
        assert claim.claim_number == "CLM-ABC123"
