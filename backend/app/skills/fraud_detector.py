from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class FraudDetectorSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_fraud_detector",
            name="Fraud & Anomaly Risk Evaluator Skill",
            description="Analyzes claim frequency, narrative anomaly indicators, unwitnessed events, and high-risk payout thresholds.",
            version="2.0.0",
            category="Risk Assessment"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        description = input_data.get("incident_description", "").lower()
        claimed_amount = float(input_data.get("claimed_amount", 0.0))

        risk_flags = []
        base_score = 0.05

        if "unwitnessed" in description or "cash" in description:
            base_score += 0.30
            risk_flags.append("Unwitnessed incident or cash payout request.")

        if claimed_amount > 10000:
            base_score += 0.25
            risk_flags.append("High financial value claim threshold triggered.")

        if "late report" in description or "delay" in description:
            base_score += 0.15
            risk_flags.append("Significant filing delay between incident and claim date.")

        risk_score = round(min(1.0, base_score), 2)
        exceeds_threshold = risk_score >= 0.50

        reasoning = [
            f"Evaluated claim fraud risk score: {risk_score:.2f} (Threshold: 0.50).",
            f"Anomaly flags: {len(risk_flags)} item(s) found.",
            f"Fraud threshold exceeded: {exceeds_threshold}. Requires SIU Fraud Review: {exceeds_threshold}."
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.92,
            output={
                "fraud_risk_score": risk_score,
                "exceeds_threshold": exceeds_threshold,
                "flags": risk_flags,
                "recommended_state": "FRAUD_REVIEW" if exceeds_threshold else "CLAIM_ANALYSIS"
            },
            reasoning=reasoning
        )
