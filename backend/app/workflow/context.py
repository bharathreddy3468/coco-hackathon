"""WorkflowContext — holds transient state for a claim's workflow execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class WorkflowContext:
    claim_id: str
    current_state: str
    previous_state: Optional[str] = None
    structured_claim: Dict[str, Any] = field(default_factory=dict)
    intermediate_outputs: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
