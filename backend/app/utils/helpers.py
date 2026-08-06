import uuid
from datetime import datetime, timezone

def generate_uuid() -> str:
    """Generate a unique string ID."""
    return str(uuid.uuid4())

def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)
