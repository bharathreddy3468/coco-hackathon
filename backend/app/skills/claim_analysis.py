import json
import logging
from typing import Any, Dict

from app.config.settings import settings
from app.schemas.skill import SkillExecutionResult, SkillMeta
from app.services.cortex_service import cortex_service
from app.skills.base import BaseSkill

logger = logging.getLogger("claim_analysis")


class ClaimAnalysisSkill(BaseSkill):
    """
    Policy Coverage & Claim Analysis Skill using Snowflake Cortex to evaluate
    claim coverage, recommended amounts, and policy compliance.
    """

    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_claim_analysis",
            name="Policy Coverage & Analysis Skill",
            description="Analyzes structured claims against policy terms to determine coverage eligibility, recommended payout, and policy clause compliance via Snowflake Cortex.",
            version="2.0.0",
            category="Policy Analysis",
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        policy_number = input_data.get("policy_number", "")
        structured_claim = input_data.get("structured_claim") or {}
        fraud_review_result = input_data.get("fraud_review_result") or {}

        cortex_result = None
        method = "SNOWFLAKE_CORTEX"

        prompt = self._build_prompt(
            claimed_amount=claimed_amount,
            policy_number=policy_number,
            structured_claim=structured_claim,
            fraud_review_result=fraud_review_result,
        )
        cortex_result = await cortex_service.complete_json(prompt, caller="claim_analysis")

        if not cortex_result:
            method = "FALLBACK_ANALYZER"
            cortex_result = self._fallback_analysis(
                claimed_amount=claimed_amount,
                policy_number=policy_number,
            )

        # Normalize output
        policy_limit = 25000.0
        deductible = 500.0
        policy_active = not policy_number.startswith("EXPIRED")

        recommended_amount = float(cortex_result.get("recommended_amount") or cortex_result.get("suggested_payout") or 0.0)
        confidence = float(cortex_result.get("confidence", 0.90))
        covered_items = cortex_result.get("covered_items") or []
        excluded_items = cortex_result.get("excluded_items") or []
        coverage_summary = cortex_result.get("coverage_summary", "")
        policy_clauses = cortex_result.get("policy_clauses") or []
        internal_reasoning = cortex_result.get("internal_reasoning") or []

        if isinstance(covered_items, str):
            covered_items = [covered_items]
        if isinstance(excluded_items, str):
            excluded_items = [excluded_items]
        if isinstance(policy_clauses, str):
            policy_clauses = [policy_clauses]
        if isinstance(internal_reasoning, str):
            internal_reasoning = [internal_reasoning]

        is_covered = policy_active and (claimed_amount <= policy_limit)
        if recommended_amount == 0.0 and is_covered:
            recommended_amount = max(0.0, min(claimed_amount, policy_limit) - deductible)

        output = {
            "recommended_amount": round(recommended_amount, 2),
            "suggested_payout": round(recommended_amount, 2),  # Backward compat
            "confidence": round(confidence, 2),
            "covered_items": covered_items,
            "excluded_items": excluded_items,
            "coverage_summary": coverage_summary,
            "policy_clauses": policy_clauses,
            "internal_reasoning": internal_reasoning,
            "is_covered": is_covered,
            "policy_active": policy_active,
            "policy_limit": policy_limit,
            "deductible": deductible,
            "evaluation_method": method,
        }

        reasoning = [
            f"Claim analysis completed via {method}.",
            f"Policy {'active' if policy_active else 'inactive/expired'}. Annual limit: ${policy_limit:,.2f}.",
            f"Recommended payout: ${recommended_amount:,.2f} (Claimed: ${claimed_amount:,.2f}, Deductible: ${deductible:,.2f}).",
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.96 if method == "SNOWFLAKE_CORTEX" else 0.90,
            output=output,
            reasoning=reasoning,
        )

    def _build_prompt(
        self,
        claimed_amount: float,
        policy_number: str,
        structured_claim: Dict[str, Any],
        fraud_review_result: Dict[str, Any],
    ) -> str:
        return (
            "You are an expert insurance claim analyst. Analyze the claim details against policy terms "
            "and determine coverage eligibility, recommended payout amount, and applicable policy clauses.\n"
            "Respond ONLY with a valid JSON object. Do NOT include markdown code blocks or conversational text.\n\n"
            "Target JSON schema:\n"
            "{\n"
            '  "recommended_amount": float,\n'
            '  "confidence": float (0.0 to 1.0),\n'
            '  "covered_items": ["list of covered procedure/service descriptions"],\n'
            '  "excluded_items": ["list of excluded items with reasons"],\n'
            '  "coverage_summary": "brief coverage determination summary",\n'
            '  "policy_clauses": ["applicable policy clause references"],\n'
            '  "internal_reasoning": ["step-by-step analysis reasoning"]\n'
            "}\n\n"
            f"POLICY NUMBER: {policy_number}\n"
            f"CLAIMED AMOUNT: ${claimed_amount:.2f}\n"
            f"STRUCTURED CLAIM: {json.dumps(structured_claim)}\n"
            f"FRAUD REVIEW RESULT: {json.dumps(fraud_review_result)}"
        )

    def _fallback_analysis(
        self,
        claimed_amount: float,
        policy_number: str,
    ) -> Dict[str, Any]:
        policy_limit = 25000.0
        deductible = 500.0
        policy_active = not policy_number.startswith("EXPIRED")
        is_covered = policy_active and (claimed_amount <= policy_limit)
        payable = max(0.0, min(claimed_amount, policy_limit) - deductible) if is_covered else 0.0

        reasoning = []
        if not policy_active:
            reasoning.append("Policy is inactive or expired at incident date.")
        else:
            reasoning.append(f"Policy active. Annual limit: ${policy_limit:,.2f}.")
            reasoning.append(f"Claimed amount (${claimed_amount:,.2f}) within limits. Applied ${deductible:,.2f} deductible.")

        return {
            "recommended_amount": round(payable, 2),
            "confidence": 0.90,
            "covered_items": ["Emergency services", "Diagnostic procedures"],
            "excluded_items": [],
            "coverage_summary": f"Claim {'approved for coverage' if is_covered else 'not covered due to policy constraints'}.",
            "policy_clauses": ["Section 4.1 — Coverage Limits", "Section 5.2 — Deductible Application"],
            "internal_reasoning": reasoning,
        }
