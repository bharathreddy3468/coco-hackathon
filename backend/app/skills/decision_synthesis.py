from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class DecisionSynthesisSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_decision_synthesis",
            name="Copilot Recommendation Synthesizer",
            description="Synthesizes outputs from data extraction, policy coverage, and fraud evaluation into a final claim recommendation.",
            version="1.0.0",
            category="Decision Engine"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        coverage_output = input_data.get("coverage", {})
        fraud_output = input_data.get("fraud", {})
        extraction_output = input_data.get("extraction", {})
        claimed_amount = float(input_data.get("claimed_amount", 0.0))

        is_covered = coverage_output.get("is_covered", False)
        payable_amount = coverage_output.get("payable_amount", 0.0)
        fraud_score = fraud_output.get("fraud_risk_score", 0.0)

        reasoning = []
        if not is_covered:
            recommendation = "REJECT"
            confidence = 0.95
            reasoning.append("Claim is REJECTED due to lack of valid policy coverage.")
        elif fraud_score >= 0.50:
            recommendation = "MANUAL_REVIEW"
            confidence = 0.88
            reasoning.append(f"Claim requires MANUAL_REVIEW due to elevated fraud risk score ({fraud_score:.2f}).")
        elif claimed_amount > 10000:
            recommendation = "MANUAL_REVIEW"
            confidence = 0.90
            reasoning.append(f"Claim requires MANUAL_REVIEW as claimed amount (${claimed_amount:,.2f}) exceeds auto-approval ceiling.")
        else:
            recommendation = "AUTO_APPROVE"
            confidence = 0.96
            reasoning.append(f"Claim is AUTO_APPROVED for ${payable_amount:,.2f}. Low risk and full coverage confirmed.")

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=confidence,
            output={
                "recommendation": recommendation,
                "suggested_payout": payable_amount if recommendation != "REJECT" else 0.0,
                "confidence_score": confidence,
                "primary_reason": reasoning[0]
            },
            reasoning=reasoning
        )
