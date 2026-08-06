from pydantic import BaseModel, Field
from datetime import datetime

class HealthCheckResponse(BaseModel):
    status: str = Field(..., example="healthy")
    app_name: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str = Field(..., example="ready")
    database_connected: bool
    skills_loaded: int
    timestamp: datetime
