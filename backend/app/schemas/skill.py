from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SkillMeta(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: str

class SkillExecutionRequest(BaseModel):
    skill_id: str
    input_data: Dict[str, Any]

class SkillExecutionResult(BaseModel):
    skill_id: str
    success: bool
    execution_time_ms: float
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    output: Dict[str, Any]
    reasoning: List[str] = Field(default_factory=list)
    error: Optional[str] = None
