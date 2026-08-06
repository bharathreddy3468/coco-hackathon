"""Shared Snowflake Cortex LLM Service.

Centralizes all Snowflake Cortex model invocations with:
- Configurable model name via environment
- Retry logic (up to 2 attempts)
- Timeout / failure handling
- Markdown code-block cleaning
- JSON response parsing and validation
- Structured logging
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.database.session import fetch_one

logger = logging.getLogger("cortex_service")

# Default model — can be overridden via CORTEX_MODEL_NAME env var
DEFAULT_MODEL = "mistral-7b"


class CortexService:
    """Shared Snowflake Cortex LLM invocation service."""

    def __init__(self):
        self._model_name = getattr(settings, "CORTEX_MODEL_NAME", DEFAULT_MODEL)
        self._max_retries = 2

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete_json(
        self,
        prompt: str,
        *,
        caller: str = "unknown",
    ) -> Optional[Dict[str, Any]]:
        """Execute a Snowflake Cortex COMPLETE query and parse the JSON response.

        Args:
            prompt: The full prompt string to send to the model.
            caller: Identifier of the calling skill (for logging).

        Returns:
            Parsed JSON dict on success, or None on failure.
        """
        if settings.LLM_PROVIDER_MOCK:
            logger.info(f"[{caller}] LLM_PROVIDER_MOCK=True — skipping Cortex invocation")
            return None

        sql = "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s) AS RESPONSE"
        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    f"[{caller}] Cortex invocation attempt {attempt}/{self._max_retries} "
                    f"(model={self._model_name})"
                )
                row = await fetch_one(sql, (self._model_name, prompt))
                if row:
                    raw_response = row.get("RESPONSE") or row.get("response") or ""
                    parsed = self._parse_json_response(raw_response, caller=caller)
                    if parsed is not None:
                        logger.info(f"[{caller}] Cortex invocation succeeded on attempt {attempt}")
                        return parsed
                    else:
                        logger.warning(
                            f"[{caller}] Cortex returned unparseable response on attempt {attempt}"
                        )
                else:
                    logger.warning(f"[{caller}] Cortex returned empty row on attempt {attempt}")
            except Exception as e:
                last_error = e
                logger.error(
                    f"[{caller}] Cortex invocation failed on attempt {attempt}: {e}",
                    exc_info=True,
                )

        logger.error(
            f"[{caller}] All {self._max_retries} Cortex attempts exhausted. "
            f"Last error: {last_error}"
        )
        return None

    def _parse_json_response(
        self, text: str, *, caller: str = "unknown"
    ) -> Optional[Dict[str, Any]]:
        """Clean markdown code blocks and parse JSON from Cortex response."""
        if not text:
            return None

        # Strip markdown fences (```json ... ```)
        clean_text = re.sub(r"```(?:json)?", "", text).strip("` \n\r\t")

        # Extract first JSON object
        match = re.search(r"\{.*\}", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(0)

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as e:
            logger.error(
                f"[{caller}] Failed to parse Cortex JSON response: {e} "
                f"(first 200 chars: '{text[:200]}')"
            )
        return None


# Module-level singleton
cortex_service = CortexService()
