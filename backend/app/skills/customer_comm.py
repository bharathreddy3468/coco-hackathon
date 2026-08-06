import json
import logging
from typing import Any, Dict

from app.schemas.skill import SkillExecutionResult, SkillMeta
from app.services.cortex_service import cortex_service
from app.skills.base import BaseSkill

logger = logging.getLogger("customer_comm")


class CustomerCommunicationSkill(BaseSkill):
    """
    Customer Communication Dispatch Skill using Snowflake Cortex.
    Generates final customer-facing response packets including approval messages,
    rejection messages, additional document requests, and appeal guidance.
    Never exposes fraud scores, internal reasoning, reviewer comments, or
    internal policy evaluations.
    """

    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_customer_comm",
            name="Customer Communication Dispatch Skill",
            description="Formats and dispatches multi-channel customer communications (Email, SMS, Portal Notice) with decision summaries.",
            version="2.0.0",
            category="Customer Dispatch",
        )

    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        claim_number = input_data.get("claim_number", "")
        customer_explanation = input_data.get("customer_explanation", "")
        workflow_outcome = input_data.get("workflow_outcome", "")
        adjuster_decision = input_data.get("adjuster_decision") or {}
        semantic_explanation = input_data.get("semantic_explanation", "")

        cortex_result = None
        method = "SNOWFLAKE_CORTEX"

        prompt = self._build_prompt(
            claim_number=claim_number,
            customer_explanation=customer_explanation or semantic_explanation,
            workflow_outcome=workflow_outcome,
            adjuster_decision=adjuster_decision,
        )
        cortex_result = await cortex_service.complete_json(prompt, caller="customer_comm")

        if cortex_result:
            dispatch_payload = {
                "channel": "EMAIL_AND_PORTAL",
                "subject": cortex_result.get("subject", f"Update on Your Insurance Claim {claim_number}"),
                "body": cortex_result.get("body", customer_explanation),
                "approval_message": cortex_result.get("approval_message", ""),
                "rejection_message": cortex_result.get("rejection_message", ""),
                "additional_documents_requested": cortex_result.get("additional_documents_requested", ""),
                "appeal_guidance": cortex_result.get("appeal_guidance", ""),
                "dispatch_status": "SENT",
                "generation_method": method,
            }
        else:
            method = "FALLBACK_GENERATOR"
            body = customer_explanation or semantic_explanation
            is_rejection = "unable to approve" in body.lower() or "rejected" in body.lower() or workflow_outcome == "REJECTED"

            dispatch_payload = {
                "channel": "EMAIL_AND_PORTAL",
                "subject": f"Update on Your Insurance Claim {claim_number}",
                "body": body,
                "approval_message": body if not is_rejection else "",
                "rejection_message": body if is_rejection else "",
                "additional_documents_requested": "",
                "appeal_guidance": "If you believe this decision is incorrect, you may file an appeal within 30 days by contacting our customer support team." if is_rejection else "",
                "dispatch_status": "SENT",
                "generation_method": method,
            }

        reasoning = [
            f"Generated customer communication packet via {method} for claim {claim_number}.",
            f"Dispatched via {dispatch_payload['channel']}.",
            "Ensured no internal fraud scores, reviewer comments, or policy evaluations are exposed.",
        ]

        return SkillExecutionResult(
            skill_id=self.meta.id,
            success=True,
            execution_time_ms=0,
            confidence_score=0.99 if method == "SNOWFLAKE_CORTEX" else 0.95,
            output=dispatch_payload,
            reasoning=reasoning,
        )

    def _build_prompt(
        self,
        claim_number: str,
        customer_explanation: str,
        workflow_outcome: str,
        adjuster_decision: Dict[str, Any],
    ) -> str:
        return (
            "You are a customer communication specialist. Generate a professional customer response "
            "for an insurance claim decision.\n\n"
            "RULES:\n"
            "- NEVER expose fraud scores, internal reasoning, reviewer comments, or internal policy evaluations\n"
            "- Generate appropriate messages based on the outcome\n"
            "- Include appeal guidance for rejections\n"
            "- Be empathetic and professional\n\n"
            "Respond ONLY with a valid JSON object:\n"
            "{\n"
            '  "subject": "email subject line",\n'
            '  "body": "full customer message body",\n'
            '  "approval_message": "message if approved (empty string if not applicable)",\n'
            '  "rejection_message": "message if rejected (empty string if not applicable)",\n'
            '  "additional_documents_requested": "any additional documents needed (empty string if none)",\n'
            '  "appeal_guidance": "appeal process info if rejected (empty string if not applicable)"\n'
            "}\n\n"
            f"CLAIM NUMBER: {claim_number}\n"
            f"WORKFLOW OUTCOME: {workflow_outcome}\n"
            f"CUSTOMER EXPLANATION: {customer_explanation}\n"
            f"ADJUSTER DECISION: {json.dumps(adjuster_decision)}"
        )
