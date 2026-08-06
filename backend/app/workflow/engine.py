"""Workflow engine — drives state transitions using StateManager and ClaimRepository."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.database.claim_repository import claim_repository
from app.models.claim import AuditLogModel, ClaimModel
from app.services.pii_masking_service import pii_masking_service
from app.services.state_manager import state_manager
from app.workflow.state_machine import ClaimState, HUMAN_REVIEW_STATES, TERMINAL_STATES

logger = logging.getLogger("workflow_engine")


class WorkflowEngine:
    """State-driven workflow engine for claim processing."""

    async def advance_claim_workflow(self, claim_id: str) -> ClaimModel:
        """Advance claim through automated states until a pause or terminal state."""
        claim = await claim_repository.get_claim(claim_id)
        if not claim:
            raise ValueError(f"Claim with ID '{claim_id}' not found.")

        ctx = await state_manager.load_workflow_state(claim_id)

        max_loop = 10
        loop_count = 0

        while claim.status not in HUMAN_REVIEW_STATES and claim.status not in TERMINAL_STATES and loop_count < max_loop:
            loop_count += 1
            current_state = claim.status

            logger.info(f"[claim={claim_id}] Processing state: {current_state} (loop {loop_count})")

            try:
                if current_state == ClaimState.SUBMITTED:
                    next_state = ClaimState.DOCUMENT_INTAKE
                elif current_state == ClaimState.DOCUMENT_INTAKE:
                    next_state = await self._run_intake_step(claim)
                elif current_state == ClaimState.PRIVACY_GUARD:
                    next_state = await self._run_privacy_step(claim)
                elif current_state == ClaimState.FRAUD_DETECTION:
                    next_state = await self._run_fraud_step(claim)
                elif current_state == ClaimState.CLAIM_ANALYSIS:
                    next_state = await self._run_analysis_step(claim)
                elif current_state == ClaimState.SEMANTIC_BRIDGE:
                    next_state = await self._run_semantic_step(claim)
                elif current_state == ClaimState.CUSTOMER_COMMUNICATION:
                    next_state = await self._run_comm_step(claim)
                else:
                    logger.warning(f"Unhandled state '{current_state}' for claim {claim.id}")
                    break
            except Exception as exc:
                logger.error(
                    f"[claim={claim_id}] Skill execution failed in state {current_state}: {exc}",
                    exc_info=True,
                )
                await state_manager.mark_failed(ctx, str(exc))
                raise

            # Record transition
            logger.info(f"[claim={claim_id}] State transition: {current_state} -> {next_state}")
            history = list(claim.workflow_history or [])
            history.append({
                "from_state": current_state,
                "to_state": next_state,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Update claim in repository
            await claim_repository.update_claim(claim.id, {
                "status": next_state,
                "workflow_history": history,
                "documents": claim.documents,
                "ai_analysis_result": claim.ai_analysis_result,
                "redacted_description": claim.redacted_description,
                "privacy_flags": claim.privacy_flags,
                "risk_score": claim.risk_score,
                "copilot_recommendation": claim.copilot_recommendation,
                "approved_amount": claim.approved_amount,
                "customer_explanation": claim.customer_explanation,
                "customer_communication": claim.customer_communication,
            })

            # Transition state manager
            await state_manager.transition(ctx, next_state, actor="WORKFLOW_ENGINE")

            # Refresh claim from DB
            claim = await claim_repository.get_claim(claim_id)

        logger.info(f"[claim={claim_id}] Workflow paused/completed at state: {claim.status}")
        return claim

    async def _run_intake_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing DOCUMENT_INTAKE skill")
        from app.skills import STATE_SKILL_MAPPING, skills_registry
        skill = STATE_SKILL_MAPPING[ClaimState.DOCUMENT_INTAKE]
        res = await skill.run({
            "incident_description": claim.incident_description,
            "claimed_amount": claim.claimed_amount,
            "documents": claim.documents or [],
        })
        output = res.output or {}
        if "updated_documents" in output:
            claim.documents = output["updated_documents"]
        await self._record_audit(claim.id, "SKILL_DOCUMENT_INTAKE", res.model_dump())
        logger.info(f"[claim={claim.id}] DOCUMENT_INTAKE completed (success={res.success})")

        # Execute Claim Parser Skill (Snowflake Cortex)
        logger.info(f"[claim={claim.id}] Executing CLAIM_PARSER skill")
        parser_skill = skills_registry.get("skill_claim_parser")
        if parser_skill:
            parser_res = await parser_skill.run({
                "incident_description": claim.incident_description,
                "claimant_name": claim.claimant_name,
                "policy_number": claim.policy_number,
                "claimed_amount": claim.claimed_amount,
                "documents": claim.documents or [],
            })
            parser_output = parser_res.output or {}
            claim_ai_res = dict(claim.ai_analysis_result or {})
            claim_ai_res["structured_claim_json"] = parser_output.get("structured_claim_json", {})
            claim_ai_res["extraction_timestamp"] = parser_output.get("extraction_timestamp")
            claim_ai_res["extraction_method"] = parser_output.get("extraction_method")
            claim.ai_analysis_result = claim_ai_res

            await self._record_audit(claim.id, "SKILL_CLAIM_PARSER", parser_res.model_dump())
            logger.info(f"[claim={claim.id}] CLAIM_PARSER completed (method={parser_output.get('extraction_method')})")

        return ClaimState.PRIVACY_GUARD

    async def _run_privacy_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing PRIVACY_GUARD skill")
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.PRIVACY_GUARD]
        res = await skill.run({
            "incident_description": claim.incident_description,
        })
        output = res.output or {}
        claim.redacted_description = output.get("redacted_description", claim.incident_description)
        claim.privacy_flags = output.get("privacy_flags", [])
        await self._record_audit(claim.id, "SKILL_PRIVACY_GUARD", res.model_dump())
        logger.info(f"[claim={claim.id}] PRIVACY_GUARD completed (pii_detected={output.get('pii_detected', False)})")
        return ClaimState.FRAUD_DETECTION

    async def _run_fraud_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing FRAUD_DETECTION skill")
        from app.config.settings import settings
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.FRAUD_DETECTION]

        structured_claim = (claim.ai_analysis_result or {}).get("structured_claim_json", {})
        raw_input = {
            "incident_description": claim.redacted_description or claim.incident_description,
            "claimed_amount": claim.claimed_amount,
            "policy_number": claim.policy_number,
            "structured_claim": structured_claim,
        }
        sanitized_input = pii_masking_service.sanitize_input(raw_input)
        logger.info(f"[claim={claim.id}] LLM invoked using sanitized claim (PII redacted) for FRAUD_DETECTION")
        res = await skill.run(sanitized_input)
        output = res.output or {}
        confidence_score = float(output.get("fraud_confidence_score") or output.get("fraud_risk_score") or 0.0)
        claim.risk_score = confidence_score

        # Persist fraud analysis into ai_analysis_result
        ai_res = dict(claim.ai_analysis_result or {})
        ai_res["fraud_detection"] = {
            "fraud_confidence_score": confidence_score,
            "fraud_score": confidence_score,
            "confidence": confidence_score,
            "risk_level": output.get("risk_level", "LOW"),
            "fraud_reasoning": output.get("fraud_reasoning", []),
            "reasoning": output.get("reasoning", []),
            "recommendation": output.get("recommendation", "AUTO_APPROVE"),
            "evaluation_method": output.get("evaluation_method", "SNOWFLAKE_CORTEX"),
        }
        claim.ai_analysis_result = ai_res

        await self._record_audit(claim.id, "SKILL_FRAUD_DETECTION", res.model_dump())

        alert_threshold = getattr(settings, "FRAUD_RISK_ALERT_THRESHOLD", 0.50)
        if confidence_score >= alert_threshold:
            claim.copilot_recommendation = "MANUAL_REVIEW"
            logger.info(
                f"[claim={claim.id}] FRAUD_DETECTION: HIGH RISK (score={confidence_score:.2f} >= {alert_threshold:.2f}) -> FRAUD_REVIEW"
            )
            return ClaimState.FRAUD_REVIEW

        claim.copilot_recommendation = "AUTO_APPROVE"
        logger.info(
            f"[claim={claim.id}] FRAUD_DETECTION: LOW RISK (score={confidence_score:.2f} < {alert_threshold:.2f}) -> CLAIM_ANALYSIS"
        )
        return ClaimState.CLAIM_ANALYSIS

    async def _run_analysis_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing CLAIM_ANALYSIS skill")
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.CLAIM_ANALYSIS]

        structured_claim = (claim.ai_analysis_result or {}).get("structured_claim_json", {})
        fraud_review_result = (claim.ai_analysis_result or {}).get("fraud_detection", {})

        raw_input = {
            "claimed_amount": claim.claimed_amount,
            "policy_number": claim.policy_number,
            "structured_claim": structured_claim,
            "fraud_review_result": fraud_review_result,
        }
        sanitized_input = pii_masking_service.sanitize_input(raw_input)
        logger.info(f"[claim={claim.id}] LLM invoked using sanitized claim (PII redacted) for CLAIM_ANALYSIS")
        res = await skill.run(sanitized_input)
        output = res.output or {}
        claim.approved_amount = float(output.get("recommended_amount") or output.get("suggested_payout") or 0.0)

        # Persist claim analysis into ai_analysis_result
        ai_res = dict(claim.ai_analysis_result or {})
        ai_res["claim_analysis"] = {
            "recommended_amount": output.get("recommended_amount", 0.0),
            "confidence": output.get("confidence", 0.0),
            "covered_items": output.get("covered_items", []),
            "excluded_items": output.get("excluded_items", []),
            "coverage_summary": output.get("coverage_summary", ""),
            "policy_clauses": output.get("policy_clauses", []),
            "internal_reasoning": output.get("internal_reasoning", []),
            "evaluation_method": output.get("evaluation_method", "SNOWFLAKE_CORTEX"),
        }
        claim.ai_analysis_result = ai_res

        await self._record_audit(claim.id, "SKILL_CLAIM_ANALYSIS", res.model_dump())
        logger.info(
            f"[claim={claim.id}] CLAIM_ANALYSIS completed (recommended=${output.get('recommended_amount', 0.0):,.2f}) -> ADJUSTER_REVIEW"
        )
        return ClaimState.ADJUSTER_REVIEW

    async def _run_semantic_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing SEMANTIC_BRIDGE skill")
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.SEMANTIC_BRIDGE]

        claim_analysis = (claim.ai_analysis_result or {}).get("claim_analysis", {})
        policy_clauses = claim_analysis.get("policy_clauses", [])

        raw_input = {
            "claimant_name": claim.claimant_name,
            "policy_number": claim.policy_number,
            "claimed_amount": claim.claimed_amount,
            "approved_amount": claim.approved_amount,
            "status": claim.status,
            "adjuster_notes": claim.adjuster_notes,
            "claim_analysis": claim_analysis,
            "policy_clauses": policy_clauses,
        }
        sanitized_input = pii_masking_service.sanitize_input(raw_input)
        logger.info(f"[claim={claim.id}] LLM invoked using sanitized claim (PII redacted) for SEMANTIC_BRIDGE")
        res = await skill.run(sanitized_input)
        output = res.output or {}
        claim.customer_explanation = output.get("customer_explanation", "")

        # Persist semantic bridge result
        ai_res = dict(claim.ai_analysis_result or {})
        ai_res["semantic_bridge"] = {
            "customer_explanation": claim.customer_explanation,
            "tone": output.get("tone", ""),
            "audience": output.get("audience", ""),
            "translation_method": output.get("translation_method", "FALLBACK_GENERATOR"),
        }
        claim.ai_analysis_result = ai_res

        await self._record_audit(claim.id, "SKILL_SEMANTIC_BRIDGE", res.model_dump())
        logger.info(f"[claim={claim.id}] SEMANTIC_BRIDGE completed -> CUSTOMER_COMMUNICATION")
        return ClaimState.CUSTOMER_COMMUNICATION

    async def _run_comm_step(self, claim: ClaimModel) -> str:
        logger.info(f"[claim={claim.id}] Executing CUSTOMER_COMMUNICATION skill")
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.CUSTOMER_COMMUNICATION]

        adjuster_decision = {
            "approved_amount": claim.approved_amount,
            "adjuster_notes": claim.adjuster_notes,
            "copilot_recommendation": claim.copilot_recommendation,
        }

        raw_input = {
            "claim_number": claim.claim_number,
            "customer_explanation": claim.customer_explanation,
            "workflow_outcome": claim.copilot_recommendation,
            "adjuster_decision": adjuster_decision,
            "semantic_explanation": claim.customer_explanation,
        }
        sanitized_input = pii_masking_service.sanitize_input(raw_input)
        logger.info(f"[claim={claim.id}] LLM invoked using sanitized claim (PII redacted) for CUSTOMER_COMMUNICATION")
        res = await skill.run(sanitized_input)
        claim.customer_communication = res.output or {}

        # Persist communication result
        ai_res = dict(claim.ai_analysis_result or {})
        ai_res["customer_communication"] = claim.customer_communication
        claim.ai_analysis_result = ai_res

        await self._record_audit(claim.id, "SKILL_CUSTOMER_COMMUNICATION", res.model_dump())
        final_state = ClaimState.REJECTED if claim.copilot_recommendation == "REJECT" else ClaimState.COMPLETED
        logger.info(f"[claim={claim.id}] CUSTOMER_COMMUNICATION dispatched -> {final_state}")
        return final_state

    async def _record_audit(self, claim_id: str, action: str, details: Dict[str, Any]) -> None:
        audit_entry = AuditLogModel(
            claim_id=claim_id,
            action=action,
            performed_by="WORKFLOW_ENGINE",
            details=details,
        )
        await claim_repository.create_audit_log(audit_entry)


workflow_engine = WorkflowEngine()
