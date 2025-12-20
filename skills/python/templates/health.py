"""
Health check endpoints.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from {{PROJECT_NAME}}.config import settings


router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/health/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies the application is ready to serve traffic.
    Add database and external service checks here.
    """
    checks: dict[str, bool] = {
        "app": True,
    }

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check endpoint.

    Simple check that the application is running.
    Used by Kubernetes liveness probes.
    """
    return {"status": "alive"}
