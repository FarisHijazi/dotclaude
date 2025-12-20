"""
Root conftest.py - Shared fixtures for all tests.

Supports dual-mode testing:
- Direct mode: Tests against ASGI app (default, fast)
- Live mode: Tests against running server (set TEST_SERVER_URL)

Usage:
    # Direct testing (default)
    pytest

    # Live server testing
    TEST_SERVER_URL=http://localhost:8000 pytest tests/e2e/
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Database URL for tests (in-memory SQLite by default)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)

# Live server URL (None means use direct ASGI transport)
TEST_SERVER_URL = os.environ.get("TEST_SERVER_URL")


# ---------------------------------------------------------------------------
# App Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app() -> "FastAPI":
    """
    Get the FastAPI application instance.

    Override this in your project's conftest.py:

        @pytest.fixture(scope="session")
        def app():
            from myapp.main import app
            return app
    """
    # Import your app here
    from {{PROJECT_NAME}}.main import app

    return app


# ---------------------------------------------------------------------------
# Database Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture(scope="session")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async database engine for test session.

    Creates all tables on startup, drops on teardown.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session with automatic rollback.

    Each test gets a clean session. Changes are rolled back after test.
    """
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# HTTP Client Fixtures (Dual-Mode)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
async def client(app: "FastAPI") -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client with dual-mode support.

    - If TEST_SERVER_URL is set: connects to live server
    - Otherwise: uses ASGI transport for direct testing

    Direct mode is faster and doesn't require a running server.
    Live mode tests the actual deployed behavior.
    """
    if TEST_SERVER_URL:
        # Live server mode
        async with AsyncClient(
            base_url=TEST_SERVER_URL,
            timeout=30.0,
        ) as c:
            yield c
    else:
        # Direct ASGI mode (default)
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            timeout=30.0,
        ) as c:
            yield c


@pytest.fixture(scope="function")
async def live_client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client that always connects to a live server.

    Requires TEST_SERVER_URL to be set, skips test otherwise.
    Use for tests that must run against a real server.
    """
    if not TEST_SERVER_URL:
        pytest.skip("TEST_SERVER_URL not set - skipping live server test")

    async with AsyncClient(
        base_url=TEST_SERVER_URL,
        timeout=30.0,
    ) as c:
        yield c


@pytest.fixture(scope="function")
async def direct_client(app: "FastAPI") -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client that always uses direct ASGI transport.

    Use for tests that should never hit a live server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Authentication Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def unique_email() -> str:
    """Generate unique email for test isolation."""
    return f"test_{uuid4().hex[:8]}@example.com"


@pytest.fixture(scope="function")
async def registered_user(
    client: AsyncClient,
    unique_email: str,
) -> dict:
    """
    Create a registered user for tests.

    Returns user dict with email and password.
    Override if your registration flow differs.
    """
    password = "TestPassword123!"

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "name": "Test User",
        },
    )

    # Handle both 201 (created) and 200 (ok) responses
    if response.status_code not in (200, 201):
        pytest.skip(f"Could not create test user: {response.text}")

    user_data = response.json()
    user_data["password"] = password
    return user_data


@pytest.fixture(scope="function")
async def auth_token(
    client: AsyncClient,
    registered_user: dict,
) -> str:
    """
    Get authentication token for registered user.

    Override if your auth flow differs.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    if response.status_code != 200:
        pytest.skip(f"Could not login test user: {response.text}")

    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict[str, str]:
    """Authorization headers with bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Utility Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def random_string() -> str:
    """Generate random string for test data."""
    return uuid4().hex[:12]


@pytest.fixture(scope="session")
def is_live_mode() -> bool:
    """Check if running in live server mode."""
    return TEST_SERVER_URL is not None


@pytest.fixture(autouse=True)
def _skip_live_only_in_direct_mode(request, is_live_mode: bool):
    """Auto-skip tests marked 'live_only' when not in live mode."""
    if request.node.get_closest_marker("live_only") and not is_live_mode:
        pytest.skip("Test requires live server (set TEST_SERVER_URL)")


# ---------------------------------------------------------------------------
# Environment Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def env_override(monkeypatch):
    """
    Helper to override environment variables in tests.

    Usage:
        def test_something(env_override):
            env_override("API_KEY", "test-key")
            # API_KEY is now "test-key" for this test only
    """

    def _override(key: str, value: str):
        monkeypatch.setenv(key, value)

    return _override


@pytest.fixture(scope="function")
def env_delete(monkeypatch):
    """
    Helper to delete environment variables in tests.

    Usage:
        def test_missing_config(env_delete):
            env_delete("DATABASE_URL")
            # DATABASE_URL is unset for this test only
    """

    def _delete(key: str):
        monkeypatch.delenv(key, raising=False)

    return _delete
