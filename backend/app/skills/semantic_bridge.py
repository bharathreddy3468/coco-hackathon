from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class SemanticBridgeSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_semantic_bridge",
            name="Semantic Bridge & Customer Translation Skill",
            description="Translates complex insurance policy clauses, technical risk codes, and adjuster payout math into clear, empathetic plain-language explanations.",
            version="2.0.0",
            category="NLG & Translation"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        claimant_name = input_data.get("claimant_name", "Policyholder")
        policy_number = input_data.get("policy_number", "")
        approved_amount = float(input_data.get("approved_amount", 0.0))
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        status = input_data.get("status", "IN_REVIEW")
        adjuster_notes = input_data.get("adjuster_notes", "")

        if status == "APPROVED":
            explanation = (
                f"Hello {claimant_name}, your claim under Policy {policy_number} has been approved! "
                f"An authorized payout of ${approved_amount:,.2f} (reflecting your $500 deductible from your requested ${claimed_amount:,.2f}) "
                f"has been finalized. "
                + (f"Adjuster Note: {adjuster_notes}" if adjuster_notes else "Disbursement will be initiated within 1-2 business days.")
            )
        elif status == "REJECTED":
            explanation = (
                f"Hello {claimant_name}, regarding your claim under Policy {policy_number}: "
                f"Following policy verification and risk review, we are unable to approve payment for this claim. "
                + (f"Reason: {adjuster_notes}" if adjuster_notes else "Please contact your representative for details.")
            )
        else:
            explanation = (
                f"Hello {claimant_name}, your claim under Policy {policy_number} is currently in review. "
                f"Our AI Copilot has compiled your documents for specialist evaluation."
            )

        reasoning = [
            f"Generated empathetic customer explanation for status '{status}'.",
            f"Included payout breakdown: ${approved_amount:,.2f} authorized."
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.98,
            output={
                "customer_explanation": explanation,
                "tone": "Empathetic & Professional",
                "audience": "Policyholder"
            },
            reasoning=reasoning
        )
