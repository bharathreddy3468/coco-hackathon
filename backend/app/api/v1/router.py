from fastapi import APIRouter
from app.api.v1.endpoints import health, claims, skills

api_router = APIRouter()

api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(claims.router, prefix="/claims", tags=["Claims"])
api_router.include_router(skills.router, prefix="/skills", tags=["AI Skills"])
