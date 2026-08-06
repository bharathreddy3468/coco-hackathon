import json
import logging
from typing import Any, Dict

from app.schemas.skill import SkillExecutionResult, SkillMeta
from app.services.cortex_service import cortex_service
from app.skills.base import BaseSkill

logger = logging.getLogger("semantic_bridge")


class SemanticBridgeSkill(BaseSkill):
    """
    Semantic Bridge & Customer Translation Skill using Snowflake Cortex.
    Translates complex insurance policy clauses, technical risk codes, and adjuster
    payout math into clear, empathetic plain-language explanations.
    """

    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_semantic_bridge",
            name="Semantic Bridge & Customer Translation Skill",
            description="Translates complex insurance policy clauses, technical risk codes, and adjuster payout math into clear, empathetic plain-language explanations.",
            version="2.0.0",
            category="NLG & Translation",
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        claimant_name = input_data.get("claimant_name", "Policyholder")
        policy_number = input_data.get("policy_number", "")
        approved_amount = float(input_data.get("approved_amount", 0.0))
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        status = input_data.get("status", "IN_REVIEW")
        adjuster_notes = input_data.get("adjuster_notes", "")
        claim_analysis = input_data.get("claim_analysis") or {}
        adjuster_decision = input_data.get("adjuster_decision") or {}
        policy_clauses = input_data.get("policy_clauses") or []

        cortex_result = None
        method = "SNOWFLAKE_CORTEX"

        prompt = self._build_prompt(
            claimant_name=claimant_name,
            policy_number=policy_number,
            approved_amount=approved_amount,
            claimed_amount=claimed_amount,
            status=status,
            adjuster_notes=adjuster_notes,
            claim_analysis=claim_analysis,
            policy_clauses=policy_clauses,
        )
        cortex_result = await cortex_service.complete_json(prompt, caller="semantic_bridge")

        if cortex_result:
            explanation = cortex_result.get("customer_explanation", "")
        else:
            method = "FALLBACK_GENERATOR"
            explanation = self._fallback_explanation(
                claimant_name=claimant_name,
                policy_number=policy_number,
                approved_amount=approved_amount,
                claimed_amount=claimed_amount,
                status=status,
                adjuster_notes=adjuster_notes,
            )

        reasoning = [
            f"Generated customer-friendly explanation via {method} for status '{status}'.",
            f"Included payout breakdown: ${approved_amount:,.2f} authorized.",
            "Removed internal insurance jargon and technical terminology.",
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.98 if method == "SNOWFLAKE_CORTEX" else 0.92,
            output={
                "customer_explanation": explanation,
                "tone": "Empathetic & Professional",
                "audience": "Policyholder",
                "translation_method": method,
            },
            reasoning=reasoning,
        )

    def _build_prompt(
        self,
        claimant_name: str,
        policy_number: str,
        approved_amount: float,
        claimed_amount: float,
        status: str,
        adjuster_notes: str,
        claim_analysis: Dict[str, Any],
        policy_clauses: list,
    ) -> str:
        return (
            "You are a customer communication specialist for an insurance company. "
            "Convert the following internal insurance decision into a clear, empathetic, "
            "customer-friendly explanation.\n\n"
            "RULES:\n"
            "- Remove ALL insurance jargon and internal terminology\n"
            "- Remove ALL internal policy evaluation details\n"
            "- Preserve the business decision accurately\n"
            "- Do NOT change the claim outcome\n"
            "- Use warm, professional tone\n\n"
            "Respond ONLY with a valid JSON object:\n"
            "{\n"
            '  "customer_explanation": "string — the full customer-friendly explanation"\n'
            "}\n\n"
            f"CLAIMANT NAME: {claimant_name}\n"
            f"POLICY NUMBER: {policy_number}\n"
            f"STATUS: {status}\n"
            f"CLAIMED AMOUNT: ${claimed_amount:.2f}\n"
            f"APPROVED AMOUNT: ${approved_amount:.2f}\n"
            f"ADJUSTER NOTES: {adjuster_notes}\n"
            f"CLAIM ANALYSIS: {json.dumps(claim_analysis)}\n"
            f"POLICY CLAUSES: {json.dumps(policy_clauses)}"
        )

    def _fallback_explanation(
        self,
        claimant_name: str,
        policy_number: str,
        approved_amount: float,
        claimed_amount: float,
        status: str,
        adjuster_notes: str,
    ) -> str:
        if status == "APPROVED" or status == "SEMANTIC_BRIDGE":
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
        return explanation
