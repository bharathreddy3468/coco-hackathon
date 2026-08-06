from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class ClaimCreate(BaseModel):
    policy_number: str = Field(..., example="POL-2026-8841")
    claimant_name: str = Field(..., example="Sarah Jenkins")
    claim_type: str = Field(..., example="Auto")
    claimed_amount: float = Field(..., gt=0, example=3500.00)
    incident_description: str = Field(..., example="Vehicle rear-ended while stopped at a red light on 5th Ave.")
    documents: List[Dict[str, Any]] = Field(default_factory=list, example=[{"name": "police_report.pdf", "size": "1.2 MB", "type": "application/pdf"}])

class ClaimUpdate(BaseModel):
    status: Optional[str] = None
    approved_amount: Optional[float] = None
    copilot_recommendation: Optional[str] = None
    adjuster_notes: Optional[str] = None

class FraudReviewAction(BaseModel):
    fraud_confirmed: bool
    investigator_notes: str = Field(..., example="SIU confirmed synthetic identity and staged accident patterns.")

class WorkflowStepResult(BaseModel):
    step_name: str
    status: str
    latency_ms: float
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)

class ClaimCopilotEvaluation(BaseModel):
    claim_id: str
    overall_recommendation: str
    confidence_score: float
    fraud_risk_score: float
    policy_coverage_valid: bool
    summary_reasoning: List[str]
    suggested_payout: float
    workflow_steps: List[WorkflowStepResult]

class ClaimResponse(BaseModel):
    id: str
    claim_number: str
    policy_number: str
    claimant_name: str
    claim_type: str
    claimed_amount: float
    approved_amount: float
    status: str
    risk_score: float
    copilot_recommendation: str
    incident_description: str
    redacted_description: Optional[str] = ""
    privacy_flags: List[str] = Field(default_factory=list)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    adjuster_notes: Optional[str] = ""
    customer_explanation: Optional[str] = ""
    customer_communication: Dict[str, Any] = Field(default_factory=dict)
    workflow_history: List[Dict[str, Any]] = Field(default_factory=list)
    ai_analysis_result: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
