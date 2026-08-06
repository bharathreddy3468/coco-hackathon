import re
from typing import Dict, Any
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class PrivacyGuardSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_privacy_guard",
            name="Privacy Guard PII Redaction Skill",
            description="Detects and redacts sensitive Personally Identifiable Information (SSNs, phone numbers, credit cards) from claim narratives.",
            version="2.0.0",
            category="Security & Compliance"
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        description = input_data.get("incident_description", "")
        
        # Regex patterns for PII
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
        credit_card_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'

        privacy_flags = []
        redacted_text = description

        if re.search(ssn_pattern, redacted_text):
            redacted_text = re.sub(ssn_pattern, '[REDACTED SSN]', redacted_text)
            privacy_flags.append('SSN_DETECTED')

        if re.search(phone_pattern, redacted_text):
            redacted_text = re.sub(phone_pattern, '[REDACTED PHONE]', redacted_text)
            privacy_flags.append('PHONE_DETECTED')

        if re.search(credit_card_pattern, redacted_text):
            redacted_text = re.sub(credit_card_pattern, '[REDACTED CARD]', redacted_text)
            privacy_flags.append('CREDIT_CARD_DETECTED')

        reasoning = [
            f"Scanned narrative for PII compliance.",
            f"Redacted {len(privacy_flags)} sensitive pattern(s): {', '.join(privacy_flags) if privacy_flags else 'None'}.",
            f"Generated PII-compliant sanitized narrative for downstream AI processing."
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.99,
            output={
                "original_length": len(description),
                "redacted_description": redacted_text,
                "privacy_flags": privacy_flags,
                "pii_detected": len(privacy_flags) > 0
            },
            reasoning=reasoning
        )
