import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class ClaimModel(BaseModel):
    id: str = Field(default_factory=_new_id)
    claim_number: str
    policy_number: str
    claimant_name: str
    claim_type: str
    claimed_amount: float
    approved_amount: float = 0.0

    # Workflow State Machine Status
    status: str = "SUBMITTED"
    risk_score: float = 0.0
    copilot_recommendation: str = "PENDING"

    incident_description: str
    redacted_description: str = ""
    privacy_flags: List[Any] = Field(default_factory=list)
    documents: List[Any] = Field(default_factory=list)
    adjuster_notes: str = ""
    customer_explanation: str = ""
    customer_communication: Dict[str, Any] = Field(default_factory=dict)
    workflow_history: List[Any] = Field(default_factory=list)
    ai_analysis_result: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class AuditLogModel(BaseModel):
    id: str = Field(default_factory=_new_id)
    claim_id: str
    action: str
    performed_by: str = "SYSTEM_COPILOT"
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)
