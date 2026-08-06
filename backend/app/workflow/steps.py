from typing import Dict, Any
from app.schemas.claim import WorkflowStepResult
from app.skills import skills_registry

async def execute_extraction_step(claim_data: Dict[str, Any]) -> WorkflowStepResult:
    skill = skills_registry["skill_claim_extractor"]
    res = await skill.run(claim_data)
    return WorkflowStepResult(
        step_name="Narrative & Entity Extraction",
        status="COMPLETED" if res.success else "FAILED",
        latency_ms=res.execution_time_ms,
        summary=f"Extracted entities with confidence {res.confidence_score*100:.0f}%.",
        details=res.output
    )

async def execute_coverage_step(claim_data: Dict[str, Any]) -> WorkflowStepResult:
    skill = skills_registry["skill_coverage_checker"]
    res = await skill.run(claim_data)
    is_covered = res.output.get("is_covered", False)
    return WorkflowStepResult(
        step_name="Policy Coverage Check",
        status="COMPLETED" if res.success else "FAILED",
        latency_ms=res.execution_time_ms,
        summary=f"Coverage Verified: {is_covered}. Payable max ${res.output.get('payable_amount', 0):,.2f}.",
        details=res.output
    )

async def execute_fraud_step(claim_data: Dict[str, Any]) -> WorkflowStepResult:
    skill = skills_registry["skill_fraud_detector"]
    res = await skill.run(claim_data)
    score = res.output.get("fraud_risk_score", 0.0)
    return WorkflowStepResult(
        step_name="Fraud Risk Assessment",
        status="COMPLETED" if res.success else "FAILED",
        latency_ms=res.execution_time_ms,
        summary=f"Risk Score: {score:.2f}. Action: {res.output.get('recommended_action')}.",
        details=res.output
    )

async def execute_synthesis_step(synthesis_input: Dict[str, Any]) -> WorkflowStepResult:
    skill = skills_registry["skill_decision_synthesis"]
    res = await skill.run(synthesis_input)
    rec = res.output.get("recommendation", "MANUAL_REVIEW")
    return WorkflowStepResult(
        step_name="Decision Synthesis",
        status="COMPLETED" if res.success else "FAILED",
        latency_ms=res.execution_time_ms,
        summary=f"Final Copilot Recommendation: {rec}.",
        details=res.output
    )
