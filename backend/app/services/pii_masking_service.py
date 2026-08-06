"""PII Masking Service — privacy-first guardrail for LLM integrations.

Accepts arbitrary dicts (structured claims, skill inputs, etc.), creates a
deep copy, and recursively redacts every key that appears in the configured
PII field list.  The original input is **never** modified.

Usage::

    from app.services.pii_masking_service import pii_masking_service

    sanitized = pii_masking_service.sanitize_input(raw_input_dict)
"""

import copy
import logging
from typing import Any, Dict, List

from app.config.pii_config import PII_FIELDS, PII_REDACTED_VALUE

logger = logging.getLogger("pii_masking_service")


class PIIMaskingService:
    """Redacts configured PII fields from arbitrary nested dicts."""

    def __init__(self, pii_fields: List[str] | None = None, redacted_value: str | None = None):
        # Store lower-cased field names for case-insensitive matching.
        self._pii_fields: set[str] = {
            f.lower() for f in (pii_fields or PII_FIELDS)
        }
        self._redacted_value: str = redacted_value or PII_REDACTED_VALUE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return a deep-copied dict with all PII fields redacted.

        The original *data* dict is **never** mutated.
        """
        sanitized = copy.deepcopy(data)
        redacted_count = self._redact_recursive(sanitized)

        if redacted_count > 0:
            logger.info(
                "Sanitized claim generated for LLM processing — "
                "%d PII field(s) redacted",
                redacted_count,
            )
        else:
            logger.debug("No PII fields found during sanitization")

        return sanitized

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _redact_recursive(self, obj: Any) -> int:
        """Walk *obj* in-place and replace PII values.  Returns count of redactions."""
        redacted = 0

        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if key.lower() in self._pii_fields:
                    obj[key] = self._redacted_value
                    redacted += 1
                else:
                    redacted += self._redact_recursive(obj[key])

        elif isinstance(obj, list):
            for item in obj:
                redacted += self._redact_recursive(item)

        return redacted


# Module-level singleton
pii_masking_service = PIIMaskingService()
