from typing import Dict, Any, List
from app.skills import skills_registry
from app.schemas.skill import SkillMeta, SkillExecutionResult

class AIService:
    """
    Service wrapper for AI Skill registry discovery and standalone skill execution.
    """
    def list_skills(self) -> List[SkillMeta]:
        return [skill.meta for skill in skills_registry.values()]

    async def execute_skill(self, skill_id: str, input_data: Dict[str, Any]) -> SkillExecutionResult:
        if skill_id not in skills_registry:
            raise ValueError(f"Skill '{skill_id}' not found in registry.")
        return await skills_registry[skill_id].run(input_data)

ai_service = AIService()
