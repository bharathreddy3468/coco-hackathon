from abc import ABC, abstractmethod
import time
from typing import Dict, Any
from app.schemas.skill import SkillMeta, SkillExecutionResult
from app.utils.logger import get_logger

logger = get_logger("skills")

class BaseSkill(ABC):
    """
    Abstract Base Class for all AI Copilot Skills.
    Provides a standardized contract for input processing, error handling, metadata declaration, and execution timing.
    """
    @property
    @abstractmethod
    def meta(self) -> SkillMeta:
        """Skill metadata declaration."""
        pass

    @abstractmethod
    async def _execute(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        """Internal execution logic implemented by child skill classes."""
        pass

    async def run(self, input_data: Dict[str, Any]) -> SkillExecutionResult:
        """
        Public wrapper to execute the skill with timing and log tracing.
        """
        logger.info(f"Executing skill [{self.meta.id}] - {self.meta.name}")
        start_time = time.perf_counter()
        
        try:
            result = await self._execute(input_data)
            elapsed = (time.perf_counter() - start_time) * 1000.0
            result.execution_time_ms = round(elapsed, 2)
            logger.info(f"Skill [{self.meta.id}] completed in {result.execution_time_ms}ms (Success: {result.success})")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Skill [{self.meta.id}] failed: {str(e)}", exc_info=True)
            return SkillExecutionResult(
                skill_id=self.meta.id,
                success=False,
                execution_time_ms=round(elapsed, 2),
                confidence_score=0.0,
                output={},
                reasoning=[f"Skill execution failed with error: {str(e)}"],
                error=str(e)
            )
