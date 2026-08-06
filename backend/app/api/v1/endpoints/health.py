from datetime import datetime, timezone
from fastapi import APIRouter
from app.config.settings import settings
from app.database.session import fetch_one
from app.schemas.health import HealthCheckResponse, ReadinessResponse
from app.skills import skills_registry

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse, summary="Liveness Probe")
async def health_check():
    """
    Returns 200 OK if API server is up and responding.
    """
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENV,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def readiness_check():
    """
    Returns system readiness status including database connection and AI Skill loading.
    """
    db_connected = False
    try:
        await fetch_one("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False

    return ReadinessResponse(
        status="ready" if db_connected else "degraded",
        database_connected=db_connected,
        skills_loaded=len(skills_registry),
        timestamp=datetime.now(timezone.utc)
    )
