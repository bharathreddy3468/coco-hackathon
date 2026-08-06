from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class ClaimExtractorSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_claim_extractor",
            name="Document & Narrative Data Extractor",
            description="Parses raw unstructured claim descriptions into structured entities (location, damage type, severe severity, third-party involvement).",
            version="1.0.0",
            category="Information Extraction"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        description = input_data.get("incident_description", "").lower()
        claimed_amount = float(input_data.get("claimed_amount", 0.0))
        claim_type = input_data.get("claim_type", "Auto")

        # Entity extraction logic (Simulated LLM extraction pipeline)
        has_third_party = any(w in description for w in ["other driver", "rear-ended", "another vehicle", "pedestrian", "truck"])
        has_police_report = "police" in description or "officer" in description
        severity = "HIGH" if claimed_amount > 10000 or "totaled" in description else ("MEDIUM" if claimed_amount > 2000 else "LOW")
        
        extracted_entities = {
            "claim_type": claim_type,
            "severity": severity,
            "has_third_party_involvement": has_third_party,
            "has_police_report_filed": has_police_report,
            "estimated_loss": claimed_amount,
            "extracted_keywords": [w for w in ["collision", "fire", "water", "theft", "rear-ended", "stopped", "red light"] if w in description]
        }

        reasoning = [
            f"Extracted claim severity as '{severity}' based on claimed amount ${claimed_amount:.2f}.",
            f"Third-party involvement detected: {has_third_party}.",
            f"Police report filed: {has_police_report}."
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.94,
            output=extracted_entities,
            reasoning=reasoning
        )
