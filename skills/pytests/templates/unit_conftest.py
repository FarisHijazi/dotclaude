"""
Unit test specific conftest.py

Place in tests/unit/conftest.py.
Provides fixtures optimized for fast, isolated unit tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock Dependencies (avoid real I/O in unit tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """
    Mock database session for unit tests.

    Use instead of real db_session for pure unit tests.
    """
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.delete = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.scalar = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_cache():
    """Mock cache/Redis for unit tests."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external API calls."""
    mock = AsyncMock()

    # Configure default responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""
    mock_response.raise_for_status = MagicMock()

    mock.get = AsyncMock(return_value=mock_response)
    mock.post = AsyncMock(return_value=mock_response)
    mock.put = AsyncMock(return_value=mock_response)
    mock.patch = AsyncMock(return_value=mock_response)
    mock.delete = AsyncMock(return_value=mock_response)

    return mock


@pytest.fixture
def mock_email_service():
    """Mock email sending service."""
    mock = AsyncMock()
    mock.send = AsyncMock(return_value=True)
    mock.send_template = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_queue():
    """Mock message queue for async jobs."""
    mock = AsyncMock()
    mock.publish = AsyncMock(return_value=True)
    mock.enqueue = AsyncMock(return_value="job_id_123")
    return mock


# ---------------------------------------------------------------------------
# Service Mocks
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user_service(mock_db):
    """Mock user service with common operations."""
    from unittest.mock import patch

    with patch("{{PROJECT_NAME}}.services.user.get_user_by_id") as get_user:
        with patch("{{PROJECT_NAME}}.services.user.create_user") as create_user:
            with patch("{{PROJECT_NAME}}.services.user.update_user") as update_user:
                get_user.return_value = None
                create_user.return_value = {"id": 1, "email": "test@example.com"}
                update_user.return_value = {"id": 1, "email": "test@example.com"}

                yield {
                    "get_user": get_user,
                    "create_user": create_user,
                    "update_user": update_user,
                }


@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    with patch("{{PROJECT_NAME}}.services.auth.verify_token") as verify:
        with patch("{{PROJECT_NAME}}.services.auth.create_token") as create:
            verify.return_value = {"user_id": 1, "email": "test@example.com"}
            create.return_value = "mock_token_123"

            yield {
                "verify_token": verify,
                "create_token": create,
            }


# ---------------------------------------------------------------------------
# Fast Fixtures (no I/O)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_dict():
    """Simple user dict for testing without database."""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
def sample_product_dict():
    """Simple product dict for testing without database."""
    return {
        "id": 1,
        "name": "Test Product",
        "price": 29.99,
        "stock": 100,
        "category": "test",
    }


@pytest.fixture
def sample_order_dict():
    """Simple order dict for testing without database."""
    return {
        "id": 1,
        "user_id": 1,
        "status": "pending",
        "total": 99.99,
        "items": [
            {"product_id": 1, "quantity": 2, "unit_price": 29.99},
            {"product_id": 2, "quantity": 1, "unit_price": 40.01},
        ],
    }


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_email():
    """Valid email for testing."""
    return "valid@example.com"


@pytest.fixture
def invalid_emails():
    """List of invalid emails for parametrized tests."""
    return [
        "",
        "invalid",
        "@example.com",
        "user@",
        "user@.com",
        "user@@example.com",
        "user @example.com",
        None,
    ]


@pytest.fixture
def valid_password():
    """Valid password meeting requirements."""
    return "SecurePassword123!"


@pytest.fixture
def invalid_passwords():
    """List of invalid passwords for parametrized tests."""
    return [
        "",
        "short",
        "nouppercase123!",
        "NOLOWERCASE123!",
        "NoNumbers!",
        "NoSpecialChar123",
        None,
    ]
