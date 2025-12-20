"""
Reusable test fixtures for common testing scenarios.

Place in tests/fixtures/__init__.py or import directly.

These fixtures provide:
- Time manipulation (freezegun)
- HTTP mocking (respx)
- File system helpers
- Async utilities
- Database helpers
"""

from __future__ import annotations

import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Time Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def frozen_time():
    """
    Freeze time for deterministic datetime testing.

    Usage:
        def test_with_frozen_time(frozen_time):
            frozen_time("2024-01-15 10:30:00")
            assert datetime.now() == datetime(2024, 1, 15, 10, 30, 0)
    """
    from freezegun import freeze_time as _freeze_time

    freezer = None

    def _freeze(time_str: str):
        nonlocal freezer
        if freezer:
            freezer.stop()
        freezer = _freeze_time(time_str)
        freezer.start()
        return freezer

    yield _freeze

    if freezer:
        freezer.stop()


@pytest.fixture
def fixed_now() -> datetime:
    """Fixed datetime for consistent test comparisons."""
    return datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# HTTP Mocking Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_http():
    """
    Mock external HTTP requests using respx.

    Usage:
        @pytest.mark.asyncio
        async def test_external_api(mock_http):
            mock_http.get("https://api.example.com/data").respond(
                json={"result": "mocked"}
            )

            result = await fetch_external_data()
            assert result == {"result": "mocked"}
    """
    import respx

    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def mock_http_strict():
    """
    Strict HTTP mock - fails if unexpected requests are made.

    Usage:
        @pytest.mark.asyncio
        async def test_known_calls(mock_http_strict):
            mock_http_strict.get("https://api.example.com/users").respond(
                json={"users": []}
            )
            # Any other HTTP call will fail the test
    """
    import respx

    with respx.mock(assert_all_mocked=True, assert_all_called=True) as mock:
        yield mock


# ---------------------------------------------------------------------------
# File System Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create temporary directory, cleaned up after test.

    Usage:
        def test_file_writing(temp_dir):
            file_path = temp_dir / "test.txt"
            file_path.write_text("Hello")
            assert file_path.read_text() == "Hello"
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path):
    """
    Factory for creating temporary files.

    Usage:
        def test_file_processing(temp_file):
            path = temp_file("data.json", '{"key": "value"}')
            result = process_json_file(path)
    """

    def _create(name: str, content: str = "") -> Path:
        path = temp_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    return _create


@pytest.fixture
def mock_file_system():
    """
    Mock file operations without touching real filesystem.

    Usage:
        def test_config_loading(mock_file_system):
            mock_file_system.set_file("config.yaml", "debug: true")
            config = load_config("config.yaml")
    """

    class MockFS:
        def __init__(self):
            self.files: dict[str, str] = {}

        def set_file(self, path: str, content: str):
            self.files[path] = content

        def read(self, path: str) -> str:
            if path not in self.files:
                raise FileNotFoundError(path)
            return self.files[path]

        def exists(self, path: str) -> bool:
            return path in self.files

    return MockFS()


# ---------------------------------------------------------------------------
# Async Utilities
# ---------------------------------------------------------------------------


@pytest.fixture
def async_mock():
    """
    Create AsyncMock instances with common patterns.

    Usage:
        async def test_service(async_mock):
            db = async_mock.db_session()
            db.get.return_value = {"id": 1}
            result = await fetch_user(db, 1)
    """

    class AsyncMockFactory:
        @staticmethod
        def db_session() -> AsyncMock:
            """Mock database session."""
            mock = AsyncMock()
            mock.commit = AsyncMock()
            mock.rollback = AsyncMock()
            mock.refresh = AsyncMock()
            mock.execute = AsyncMock()
            mock.get = AsyncMock()
            mock.add = MagicMock()
            mock.delete = AsyncMock()
            return mock

        @staticmethod
        def http_client() -> AsyncMock:
            """Mock HTTP client."""
            mock = AsyncMock()
            mock.get = AsyncMock()
            mock.post = AsyncMock()
            mock.put = AsyncMock()
            mock.patch = AsyncMock()
            mock.delete = AsyncMock()
            return mock

        @staticmethod
        def cache() -> AsyncMock:
            """Mock cache (Redis-like)."""
            mock = AsyncMock()
            mock.get = AsyncMock(return_value=None)
            mock.set = AsyncMock()
            mock.delete = AsyncMock()
            mock.exists = AsyncMock(return_value=False)
            return mock

        @staticmethod
        def queue() -> AsyncMock:
            """Mock message queue."""
            mock = AsyncMock()
            mock.publish = AsyncMock()
            mock.subscribe = AsyncMock()
            mock.ack = AsyncMock()
            return mock

    return AsyncMockFactory()


@pytest.fixture
def capture_logs():
    """
    Capture log messages for assertions.

    Usage:
        def test_logging(capture_logs):
            with capture_logs("myapp.service") as logs:
                do_something()
            assert "Processing complete" in logs.messages
    """
    import logging

    class LogCapture:
        def __init__(self):
            self.records: list[logging.LogRecord] = []

        @property
        def messages(self) -> list[str]:
            return [r.getMessage() for r in self.records]

        @property
        def levels(self) -> list[str]:
            return [r.levelname for r in self.records]

    class LogHandler(logging.Handler):
        def __init__(self, capture: LogCapture):
            super().__init__()
            self.capture = capture

        def emit(self, record: logging.LogRecord):
            self.capture.records.append(record)

    from contextlib import contextmanager

    @contextmanager
    def _capture(logger_name: str):
        capture = LogCapture()
        handler = LogHandler(capture)
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        old_level = logger.level
        logger.setLevel(logging.DEBUG)

        try:
            yield capture
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)

    return _capture


# ---------------------------------------------------------------------------
# Data Generation Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def random_data():
    """
    Generate random test data with Faker.

    Usage:
        def test_user_creation(random_data):
            user_data = {
                "email": random_data.email(),
                "name": random_data.name(),
            }
    """
    from faker import Faker

    return Faker()


@pytest.fixture
def sample_user_data(random_data) -> dict[str, Any]:
    """Pre-built user data for tests."""
    return {
        "email": random_data.email(),
        "name": random_data.name(),
        "password": "TestPassword123!",
        "phone": random_data.phone_number(),
    }


@pytest.fixture
def sample_product_data(random_data) -> dict[str, Any]:
    """Pre-built product data for tests."""
    return {
        "name": random_data.catch_phrase(),
        "description": random_data.text(max_nb_chars=200),
        "price": float(random_data.pydecimal(min_value=1, max_value=1000)),
        "stock": random_data.random_int(min=0, max=100),
        "category": random_data.word(),
    }


# ---------------------------------------------------------------------------
# Database Test Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def db_reset(db_session):
    """
    Reset database state after test.

    Usage:
        @pytest.mark.asyncio
        async def test_data_operations(db_session, db_reset):
            # Test with dirty data
            await create_many_records(db_session)
            # db_reset ensures cleanup
    """
    yield
    # The db_session fixture handles rollback automatically


@pytest.fixture
async def seeded_db(db_session):
    """
    Database with pre-seeded test data.

    Override in project conftest.py to add specific seed data.
    """
    # Add common seed data here
    # Example:
    # await db_session.execute(
    #     insert(User).values(email="test@example.com", name="Test")
    # )
    # await db_session.commit()
    yield db_session


# ---------------------------------------------------------------------------
# Configuration Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """
    Mock application settings.

    Usage:
        def test_with_custom_settings(mock_settings):
            mock_settings(debug=True, api_key="test_key")
            result = get_config()
    """

    def _mock(**overrides):
        # Create a mock settings object with overrides
        settings = MagicMock()
        for key, value in overrides.items():
            setattr(settings, key, value)
        return settings

    return _mock


@pytest.fixture
def clean_env(monkeypatch):
    """
    Clean environment for isolated config tests.

    Usage:
        def test_config_defaults(clean_env):
            # DATABASE_URL not set
            config = load_config()
            assert config.database_url == "sqlite:///default.db"
    """
    # Remove common config env vars
    env_vars_to_remove = [
        "DATABASE_URL",
        "REDIS_URL",
        "API_KEY",
        "SECRET_KEY",
        "DEBUG",
    ]
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)

    yield monkeypatch


# ---------------------------------------------------------------------------
# API Client Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client_factory(client):
    """
    Create API clients with different auth states.

    Usage:
        @pytest.mark.asyncio
        async def test_permissions(api_client_factory):
            admin = await api_client_factory.as_admin()
            user = await api_client_factory.as_user()

            admin_resp = await admin.get("/admin/users")
            user_resp = await user.get("/admin/users")

            assert admin_resp.status_code == 200
            assert user_resp.status_code == 403
    """
    from dataclasses import dataclass

    @dataclass
    class AuthenticatedClient:
        client: Any
        headers: dict

        async def get(self, url: str, **kwargs):
            return await self.client.get(url, headers=self.headers, **kwargs)

        async def post(self, url: str, **kwargs):
            return await self.client.post(url, headers=self.headers, **kwargs)

        async def patch(self, url: str, **kwargs):
            return await self.client.patch(url, headers=self.headers, **kwargs)

        async def delete(self, url: str, **kwargs):
            return await self.client.delete(url, headers=self.headers, **kwargs)

    class ClientFactory:
        def __init__(self, base_client):
            self._client = base_client

        async def as_admin(self) -> AuthenticatedClient:
            # Create or login as admin user
            headers = {"Authorization": "Bearer admin_token"}
            return AuthenticatedClient(self._client, headers)

        async def as_user(self) -> AuthenticatedClient:
            # Create or login as regular user
            headers = {"Authorization": "Bearer user_token"}
            return AuthenticatedClient(self._client, headers)

        def anonymous(self) -> AuthenticatedClient:
            return AuthenticatedClient(self._client, {})

    return ClientFactory(client)


# ---------------------------------------------------------------------------
# Performance Testing Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def timer():
    """
    Simple timer for performance assertions.

    Usage:
        def test_performance(timer):
            with timer() as t:
                result = expensive_operation()
            assert t.elapsed < 1.0  # Should complete in under 1 second
    """
    import time
    from contextlib import contextmanager
    from dataclasses import dataclass

    @dataclass
    class TimerResult:
        elapsed: float = 0.0

    @contextmanager
    def _timer():
        result = TimerResult()
        start = time.perf_counter()
        try:
            yield result
        finally:
            result.elapsed = time.perf_counter() - start

    return _timer
