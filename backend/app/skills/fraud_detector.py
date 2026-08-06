import json
import logging
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.schemas.skill import SkillExecutionResult, SkillMeta
from app.services.cortex_service import cortex_service
from app.skills.base import BaseSkill

logger = logging.getLogger("fraud_detector")


class FraudDetectorSkill(BaseSkill):
    """
    Fraud & Anomaly Risk Evaluator Skill using Snowflake Cortex to detect
    fraud patterns and evaluate risk levels across claims and policies.
    """

    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_fraud_detector",
            name="Fraud & Anomaly Risk Evaluator Skill",
            description="Analyzes structured claim data, policy details, and incident narratives for fraud risk indicators using Snowflake Cortex.",
            version="2.0.0",
            category="Risk Assessment",
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        description = input_data.get("incident_description", "")
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        policy_number = input_data.get("policy_number", "")
        structured_claim = input_data.get("structured_claim") or {}

        cortex_result = None
        method = "SNOWFLAKE_CORTEX"

        # Use shared Cortex service
        prompt = self._build_prompt(
            description=description,
            claimed_amount=claimed_amount,
            policy_number=policy_number,
            structured_claim=structured_claim,
        )
        cortex_result = await cortex_service.complete_json(prompt, caller="fraud_detector")

        if not cortex_result:
            method = "FALLBACK_EVALUATOR"
            cortex_result = self._fallback_evaluation(
                description=description,
                claimed_amount=claimed_amount,
                structured_claim=structured_claim,
            )

        # Normalize and validate output fields
        confidence_score = round(max(0.0, min(1.0, float(cortex_result.get("fraud_confidence_score") or cortex_result.get("fraud_score") or 0.05))), 2)
        risk_level = str(cortex_result.get("risk_level", "LOW")).upper()
        if risk_level not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            risk_level = "HIGH" if confidence_score >= 0.70 else ("MEDIUM" if confidence_score >= 0.40 else "LOW")

        reasoning_list = cortex_result.get("fraud_reasoning") or cortex_result.get("reasoning") or []
        if isinstance(reasoning_list, str):
            reasoning_list = [reasoning_list]

        recommendation = str(cortex_result.get("recommendation", "AUTO_APPROVE")).upper()

        alert_threshold = getattr(settings, "FRAUD_RISK_ALERT_THRESHOLD", 0.50)
        exceeds_threshold = confidence_score >= alert_threshold

        output = {
            "fraud_confidence_score": confidence_score,
            "fraud_score": confidence_score,
            "confidence": confidence_score,
            "fraud_risk_score": confidence_score,  # Backward compatibility
            "risk_level": risk_level,
            "fraud_reasoning": reasoning_list,
            "reasoning": reasoning_list,
            "recommendation": recommendation,
            "exceeds_threshold": exceeds_threshold,
            "flags": reasoning_list,
            "evaluation_method": method,
        }

        reasoning = [
            f"Evaluated fraud risk score: {confidence_score:.2f} (Alert Threshold: {alert_threshold:.2f}).",
            f"Risk level: {risk_level}, Recommendation: '{recommendation}'.",
            f"Evaluation method: {method}.",
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.95 if method == "SNOWFLAKE_CORTEX" else 0.85,
            output=output,
            reasoning=reasoning,
        )

    def _build_prompt(
        self,
        description: str,
        claimed_amount: float,
        policy_number: str,
        structured_claim: Dict[str, Any],
    ) -> str:
        return (
            "You are an AI insurance fraud detection specialist. "
            "Analyze the claim and policy information below for potential fraud or anomaly indicators.\n"
            "Respond ONLY with a valid JSON object. Do NOT include markdown code blocks or conversational text.\n\n"
            "Target JSON schema:\n"
            "{\n"
            '  "fraud_confidence_score": float (between 0.00 and 1.00),\n'
            '  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            '  "fraud_reasoning": ["list of detected anomaly/risk explanations"],\n'
            '  "recommendation": "AUTO_APPROVE" | "MANUAL_REVIEW" | "SIU_INVESTIGATION"\n'
            "}\n\n"
            f"POLICY NUMBER: {policy_number}\n"
            f"CLAIMED AMOUNT: ${claimed_amount:.2f}\n"
            f"INCIDENT DESCRIPTION: {description[:2000]}\n"
            f"STRUCTURED CLAIM DATA: {json.dumps(structured_claim)}"
        )

    def _fallback_evaluation(
        self,
        description: str,
        claimed_amount: float,
        structured_claim: Dict[str, Any],
    ) -> Dict[str, Any]:
        desc_lower = description.lower()
        risk_flags = []
        score = 0.05

        if "unwitnessed" in desc_lower or "cash" in desc_lower:
            score += 0.30
            risk_flags.append("Unwitnessed incident or cash payout request.")

        if claimed_amount > 10000:
            score += 0.25
            risk_flags.append("High financial value claim threshold triggered.")

        if "late report" in desc_lower or "delay" in desc_lower:
            score += 0.15
            risk_flags.append("Significant filing delay between incident and claim date.")

        score = round(min(1.0, score), 2)
        risk_level = "HIGH" if score >= 0.70 else ("MEDIUM" if score >= 0.40 else "LOW")
        recommendation = "SIU_INVESTIGATION" if score >= 0.70 else ("MANUAL_REVIEW" if score >= 0.40 else "AUTO_APPROVE")

        return {
            "fraud_confidence_score": score,
            "risk_level": risk_level,
            "fraud_reasoning": risk_flags if risk_flags else ["Standard claim metrics within normal risk bounds."],
            "recommendation": recommendation,
        }
