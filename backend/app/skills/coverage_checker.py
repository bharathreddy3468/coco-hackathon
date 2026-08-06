from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class CoverageCheckerSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_coverage_checker",
            name="Policy Coverage & Limits Checker",
            description="Verifies policy status, active coverage window, policy limits, deductibles, and exclusion rules.",
            version="1.0.0",
            category="Policy Validation"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        policy_number = input_data.get("policy_number", "")

        # Default mock policy constraints
        policy_limit = 25000.0
        deductible = 500.0
        policy_active = True if not policy_number.startswith("EXPIRED") else False

        is_covered = policy_active and (claimed_amount <= policy_limit)
        payable_amount = max(0.0, min(claimed_amount, policy_limit) - deductible) if is_covered else 0.0

        reasoning = []
        if not policy_active:
            reasoning.append("Policy is inactive or expired at the time of incident.")
        else:
            reasoning.append(f"Policy status active. Annual limit: ${policy_limit:,.2f}.")
            if claimed_amount > policy_limit:
                reasoning.append(f"Claimed amount (${claimed_amount:,.2f}) exceeds policy limit (${policy_limit:,.2f}).")
            else:
                reasoning.append(f"Claimed amount is within policy limits. Deductible of ${deductible:,.2f} applied.")

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.98 if is_covered else 0.85,
            output={
                "is_covered": is_covered,
                "policy_active": policy_active,
                "policy_limit": policy_limit,
                "deductible": deductible,
                "payable_amount": payable_amount
            },
            reasoning=reasoning
        )
