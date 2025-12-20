"""
FastAPI application entrypoint with uvloop for better async performance.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from {{PROJECT_NAME}}.api.routes import health
from {{PROJECT_NAME}}.config import settings
from {{PROJECT_NAME}}.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Application factory for creating the FastAPI app."""
    application = FastAPI(
        title=settings.app_name,
        description="{{PROJECT_DESCRIPTION}}",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(health.router, prefix="/api/v1", tags=["health"])

    return application


app = create_app()


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs" if settings.debug else None,
    }


if __name__ == "__main__":
    uvicorn.run(
        "{{PROJECT_NAME}}.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        loop="uvloop",
    )
