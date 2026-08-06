"""Claim service — business logic layer using Snowflake-backed repositories."""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.database.claim_repository import claim_repository
from app.models.claim import AuditLogModel, ClaimModel
from app.schemas.claim import ClaimCreate, ClaimUpdate, FraudReviewAction
from app.services.state_manager import state_manager
from app.workflow.engine import workflow_engine
from app.workflow.state_machine import ClaimState

logger = logging.getLogger("claim_service")


async def run_workflow_background(claim_id: str):
    """Background worker for executing automated workflow steps."""
    try:
        logger.info(f"Background worker starting workflow execution for claim {claim_id}")
        await workflow_engine.advance_claim_workflow(claim_id)
    except Exception as e:
        logger.error(f"Error in background workflow for claim {claim_id}: {e}", exc_info=True)


class ClaimService:
    """Business logic layer for claims."""

    async def create_claim(self, data: ClaimCreate) -> ClaimModel:
        claim_number = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        claim = ClaimModel(
            claim_number=claim_number,
            policy_number=data.policy_number,
            claimant_name=data.claimant_name,
            claim_type=data.claim_type,
            claimed_amount=data.claimed_amount,
            incident_description=data.incident_description,
            documents=data.documents,
            status=ClaimState.SUBMITTED,
            copilot_recommendation="PENDING",
            workflow_history=[{
                "from_state": None,
                "to_state": ClaimState.SUBMITTED,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        )
        claim = await claim_repository.create_claim(claim)
        # Initialize workflow state
        ctx = await state_manager.load_workflow_state(claim.id)
        logger.info(f"Submitted new claim ID={claim.id}, claim_number={claim_number}")
        return claim

    async def list_claims(self, limit: int = 50) -> List[ClaimModel]:
        return await claim_repository.list_claims(limit)

    async def get_claim(self, claim_id: str) -> Optional[ClaimModel]:
        return await claim_repository.get_claim(claim_id)

    async def advance_workflow(self, claim_id: str) -> ClaimModel:
        return await workflow_engine.advance_claim_workflow(claim_id)

    async def process_fraud_review(self, claim_id: str, action: FraudReviewAction) -> ClaimModel:
        claim = await self.get_claim(claim_id)
        if not claim:
            raise ValueError(f"Claim with ID '{claim_id}' not found.")

        if action.fraud_confirmed:
            await claim_repository.update_claim(claim.id, {
                "status": ClaimState.REJECTED,
                "copilot_recommendation": "REJECT",
                "adjuster_notes": f"[SIU FRAUD CONFIRMED]: {action.investigator_notes}",
            })
            audit = AuditLogModel(
                claim_id=claim.id,
                action="FRAUD_INVESTIGATION_CONFIRMED",
                performed_by="SIU_INVESTIGATOR",
                details={"notes": action.investigator_notes, "final_status": "REJECTED"},
            )
            await claim_repository.create_audit_log(audit)
        else:
            await claim_repository.update_claim(claim.id, {
                "status": ClaimState.CLAIM_ANALYSIS,
                "adjuster_notes": f"[SIU FRAUD CLEARED]: {action.investigator_notes}",
            })
            audit = AuditLogModel(
                claim_id=claim.id,
                action="FRAUD_INVESTIGATION_CLEARED",
                performed_by="SIU_INVESTIGATOR",
                details={"notes": action.investigator_notes, "next_status": "CLAIM_ANALYSIS"},
            )
            await claim_repository.create_audit_log(audit)
            await workflow_engine.advance_claim_workflow(claim.id)

        return await claim_repository.get_claim(claim_id)

    async def update_claim_adjuster(self, claim_id: str, update_data: ClaimUpdate) -> ClaimModel:
        claim = await self.get_claim(claim_id)
        if not claim:
            raise ValueError(f"Claim with ID '{claim_id}' not found.")

        fields = {}
        if update_data.approved_amount is not None:
            fields["approved_amount"] = update_data.approved_amount
        if update_data.adjuster_notes is not None:
            fields["adjuster_notes"] = update_data.adjuster_notes

        if update_data.status == "REJECTED":
            fields["status"] = ClaimState.REJECTED
            fields["copilot_recommendation"] = "REJECT"
        else:
            fields["status"] = ClaimState.SEMANTIC_BRIDGE
            fields["copilot_recommendation"] = "AUTO_APPROVE" if update_data.status == "APPROVED" else "MANUAL_REVIEW"

        await claim_repository.update_claim(claim.id, fields)

        audit = AuditLogModel(
            claim_id=claim.id,
            action=f"ADJUSTER_ACTION_{fields.get('status', claim.status)}",
            performed_by="HUMAN_ADJUSTER",
            details={
                "status": fields.get("status", claim.status),
                "approved_amount": fields.get("approved_amount", claim.approved_amount),
                "notes": fields.get("adjuster_notes", claim.adjuster_notes),
            },
        )
        await claim_repository.create_audit_log(audit)

        if fields.get("status") == ClaimState.SEMANTIC_BRIDGE:
            await workflow_engine.advance_claim_workflow(claim.id)

        return await claim_repository.get_claim(claim_id)


claim_service = ClaimService()
