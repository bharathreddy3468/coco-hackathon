"""Workflow engine — drives state transitions using StateManager and ClaimRepository."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.database.claim_repository import claim_repository
from app.models.claim import AuditLogModel, ClaimModel
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
                await state_manager.mark_failed(ctx, str(exc))
                raise

            # Record transition
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

        return claim

    async def _run_intake_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.DOCUMENT_INTAKE]
        res = await skill.run({
            "incident_description": claim.incident_description,
            "claimed_amount": claim.claimed_amount,
            "documents": claim.documents or [],
        })
        await self._record_audit(claim.id, "SKILL_DOCUMENT_INTAKE", res.model_dump())
        return ClaimState.PRIVACY_GUARD

    async def _run_privacy_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.PRIVACY_GUARD]
        res = await skill.run({
            "incident_description": claim.incident_description,
        })
        output = res.output or {}
        claim.redacted_description = output.get("redacted_description", claim.incident_description)
        claim.privacy_flags = output.get("privacy_flags", [])
        await self._record_audit(claim.id, "SKILL_PRIVACY_GUARD", res.model_dump())
        return ClaimState.FRAUD_DETECTION

    async def _run_fraud_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.FRAUD_DETECTION]
        res = await skill.run({
            "incident_description": claim.redacted_description or claim.incident_description,
            "claimed_amount": claim.claimed_amount,
        })
        output = res.output or {}
        risk_score = float(output.get("fraud_risk_score", 0.0))
        claim.risk_score = risk_score
        await self._record_audit(claim.id, "SKILL_FRAUD_DETECTION", res.model_dump())

        if risk_score >= 0.50:
            claim.copilot_recommendation = "MANUAL_REVIEW"
            return ClaimState.FRAUD_REVIEW
        return ClaimState.CLAIM_ANALYSIS

    async def _run_analysis_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.CLAIM_ANALYSIS]
        res = await skill.run({
            "claimed_amount": claim.claimed_amount,
            "policy_number": claim.policy_number,
        })
        output = res.output or {}
        claim.approved_amount = float(output.get("suggested_payout", 0.0))
        await self._record_audit(claim.id, "SKILL_CLAIM_ANALYSIS", res.model_dump())
        return ClaimState.ADJUSTER_REVIEW

    async def _run_semantic_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.SEMANTIC_BRIDGE]
        res = await skill.run({
            "claimant_name": claim.claimant_name,
            "policy_number": claim.policy_number,
            "claimed_amount": claim.claimed_amount,
            "approved_amount": claim.approved_amount,
            "status": claim.status,
            "adjuster_notes": claim.adjuster_notes,
        })
        output = res.output or {}
        claim.customer_explanation = output.get("customer_explanation", "")
        await self._record_audit(claim.id, "SKILL_SEMANTIC_BRIDGE", res.model_dump())
        return ClaimState.CUSTOMER_COMMUNICATION

    async def _run_comm_step(self, claim: ClaimModel) -> str:
        from app.skills import STATE_SKILL_MAPPING
        skill = STATE_SKILL_MAPPING[ClaimState.CUSTOMER_COMMUNICATION]
        res = await skill.run({
            "claim_number": claim.claim_number,
            "customer_explanation": claim.customer_explanation,
        })
        claim.customer_communication = res.output or {}
        await self._record_audit(claim.id, "SKILL_CUSTOMER_COMMUNICATION", res.model_dump())
        return ClaimState.COMPLETED

    async def _record_audit(self, claim_id: str, action: str, details: Dict[str, Any]) -> None:
        audit_entry = AuditLogModel(
            claim_id=claim_id,
            action=action,
            performed_by="WORKFLOW_ENGINE",
            details=details,
        )
        await claim_repository.create_audit_log(audit_entry)


workflow_engine = WorkflowEngine()
