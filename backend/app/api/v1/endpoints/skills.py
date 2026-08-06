from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.skill import SkillMeta, SkillExecutionRequest, SkillExecutionResult
from app.services.ai_service import ai_service

router = APIRouter()

@router.get("", response_model=List[SkillMeta], summary="List loaded AI Copilot skills")
async def list_skills():
    return ai_service.list_skills()

@router.post("/execute", response_model=SkillExecutionResult, summary="Execute a standalone AI Skill")
async def execute_skill(req: SkillExecutionRequest):
    try:
        return await ai_service.execute_skill(req.skill_id, req.input_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
