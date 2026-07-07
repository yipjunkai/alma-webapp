"""Health check endpoint."""

from fastapi import APIRouter

from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> HealthOut:
    return HealthOut()
