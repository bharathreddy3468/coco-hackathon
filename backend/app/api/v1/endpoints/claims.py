from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse, FraudReviewAction
from app.services.claim_service import claim_service, run_workflow_background
from app.services.state_manager import state_manager
from app.workflow.engine import workflow_engine

router = APIRouter()


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED, summary="Submit a new insurance claim (Asynchronous)")
async def create_claim(data: ClaimCreate, background_tasks: BackgroundTasks):
    claim = await claim_service.create_claim(data)
    background_tasks.add_task(run_workflow_background, claim.id)
    return claim


@router.get("", response_model=List[ClaimResponse], summary="List all insurance claims")
async def list_claims(limit: int = 50):
    return await claim_service.list_claims(limit=limit)


@router.get("/{claim_id}", response_model=ClaimResponse, summary="Get claim by ID")
async def get_claim(claim_id: str):
    claim = await claim_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/{claim_id}/advance", response_model=ClaimResponse, summary="Advance workflow engine state for claim")
async def advance_claim(claim_id: str):
    try:
        return await claim_service.advance_workflow(claim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/fraud-review", response_model=ClaimResponse, summary="Human Fraud Investigator Action")
async def process_fraud_review(claim_id: str, action: FraudReviewAction, background_tasks: BackgroundTasks):
    try:
        claim = await claim_service.process_fraud_review(claim_id, action)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # Remaining automated steps (e.g. CUSTOMER_COMMUNICATION, Cortex calls) run in the
    # background so this request returns immediately instead of blocking on the LLM.
    background_tasks.add_task(run_workflow_background, claim_id)
    return claim


@router.patch("/{claim_id}", response_model=ClaimResponse, summary="Human Adjuster Review Action")
async def update_claim_adjuster(claim_id: str, update_data: ClaimUpdate, background_tasks: BackgroundTasks):
    try:
        claim = await claim_service.update_claim_adjuster(claim_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    background_tasks.add_task(run_workflow_background, claim_id)
    return claim


@router.post("/{claim_id}/resume", response_model=ClaimResponse, summary="Resume a failed workflow")
async def resume_workflow(claim_id: str):
    """Resume a failed workflow if retry_count < 3."""
    ctx = await state_manager.load_workflow_state(claim_id)
    # Check if workflow is in FAILED status (from the DB row)
    from app.database.session import fetch_one
    row = await fetch_one("SELECT workflow_status, retry_count FROM CLAIM_WORKFLOW WHERE claim_id = %s", (claim_id,))
    if not row:
        raise HTTPException(status_code=404, detail="No workflow state found for this claim.")

    wf_status = row.get("WORKFLOW_STATUS") or row.get("workflow_status", "")
    retry_count = row.get("RETRY_COUNT") or row.get("retry_count", 0)

    if wf_status != "FAILED":
        raise HTTPException(status_code=400, detail=f"Workflow is not in FAILED state (current: {wf_status}).")
    if retry_count >= 3:
        raise HTTPException(status_code=400, detail="Maximum retry count (3) reached. Manual intervention required.")

    # Reset workflow status to ACTIVE and re-dispatch
    from app.database.session import execute_query
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    await execute_query(
        "UPDATE CLAIM_WORKFLOW SET workflow_status = 'ACTIVE', error_message = NULL, updated_at = %s WHERE claim_id = %s",
        (now, claim_id),
    )

    try:
        return await workflow_engine.advance_claim_workflow(claim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
