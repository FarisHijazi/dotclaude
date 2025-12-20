"""
Unit tests for {{MODULE_NAME}}.

Unit tests verify individual functions/methods in isolation.
They should be fast, deterministic, and have no external dependencies.

Naming convention:
- File: <module>_test.py (e.g., user_service_test.py)
- Function: test_<function>_<scenario>_<expected_outcome>

Run:
    pytest tests/unit/
    pytest tests/unit/{{MODULE_NAME}}_test.py -v
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the module under test
# from {{PROJECT_NAME}}.services.{{MODULE_NAME}} import (
#     calculate_total,
#     validate_email,
#     format_currency,
# )


# ---------------------------------------------------------------------------
# Simple Function Tests
# ---------------------------------------------------------------------------


def test_validate_email_accepts_valid_format():
    """Valid email with standard format should return True."""
    # Arrange
    email = "user@example.com"

    # Act
    result = validate_email(email)

    # Assert
    assert result is True


def test_validate_email_rejects_missing_at_symbol():
    """Email without @ symbol should return False."""
    assert validate_email("userexample.com") is False


def test_validate_email_rejects_empty_string():
    """Empty string should return False."""
    assert validate_email("") is False


# ---------------------------------------------------------------------------
# Parametrized Tests (multiple inputs, same logic)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email,expected",
    [
        ("user@example.com", True),
        ("user.name@example.com", True),
        ("user+tag@example.com", True),
        ("user@sub.domain.com", True),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
        ("user@.com", False),
        ("", False),
        (None, False),
    ],
    ids=[
        "standard_email",
        "email_with_dot",
        "email_with_plus",
        "subdomain_email",
        "no_at_symbol",
        "missing_local",
        "missing_domain",
        "invalid_domain",
        "empty_string",
        "none_value",
    ],
)
def test_validate_email_handles_various_formats(email, expected):
    """Email validation correctly handles various input formats."""
    assert validate_email(email) is expected


# ---------------------------------------------------------------------------
# Tests with Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_cart_items():
    """Sample cart items for testing."""
    return [
        {"product_id": 1, "price": Decimal("10.00"), "quantity": 2},
        {"product_id": 2, "price": Decimal("25.50"), "quantity": 1},
        {"product_id": 3, "price": Decimal("5.00"), "quantity": 3},
    ]


def test_calculate_total_sums_item_prices(sample_cart_items):
    """Total should equal sum of (price * quantity) for all items."""
    # Expected: (10*2) + (25.50*1) + (5*3) = 20 + 25.50 + 15 = 60.50
    result = calculate_total(sample_cart_items)

    assert result == Decimal("60.50")


def test_calculate_total_returns_zero_for_empty_cart():
    """Empty cart should return zero total."""
    result = calculate_total([])

    assert result == Decimal("0")


def test_calculate_total_handles_single_item():
    """Single item cart should return that item's total."""
    items = [{"product_id": 1, "price": Decimal("99.99"), "quantity": 1}]

    result = calculate_total(items)

    assert result == Decimal("99.99")


# ---------------------------------------------------------------------------
# Tests with Mocking
# ---------------------------------------------------------------------------


def test_format_currency_calls_locale_service():
    """Currency formatting should use the locale service."""
    with patch("{{PROJECT_NAME}}.services.locale.get_currency_symbol") as mock_symbol:
        mock_symbol.return_value = "$"

        result = format_currency(Decimal("100.00"), "USD")

        mock_symbol.assert_called_once_with("USD")
        assert result == "$100.00"


def test_format_currency_handles_unknown_currency():
    """Unknown currency should use default formatting."""
    with patch("{{PROJECT_NAME}}.services.locale.get_currency_symbol") as mock_symbol:
        mock_symbol.side_effect = ValueError("Unknown currency")

        result = format_currency(Decimal("100.00"), "UNKNOWN")

        assert result == "100.00 UNKNOWN"


# ---------------------------------------------------------------------------
# Async Function Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_validate_user_exists_returns_true_when_found():
    """User validation should return True when user exists in database."""
    # Arrange
    mock_db = AsyncMock()
    mock_db.get_user.return_value = {"id": 1, "email": "user@example.com"}

    # Act
    result = await validate_user_exists(mock_db, user_id=1)

    # Assert
    assert result is True
    mock_db.get_user.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_async_validate_user_exists_returns_false_when_not_found():
    """User validation should return False when user doesn't exist."""
    mock_db = AsyncMock()
    mock_db.get_user.return_value = None

    result = await validate_user_exists(mock_db, user_id=999)

    assert result is False


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


def test_calculate_total_raises_on_negative_quantity():
    """Negative quantity should raise ValueError."""
    items = [{"product_id": 1, "price": Decimal("10.00"), "quantity": -1}]

    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        calculate_total(items)


def test_calculate_total_raises_on_negative_price():
    """Negative price should raise ValueError."""
    items = [{"product_id": 1, "price": Decimal("-10.00"), "quantity": 1}]

    with pytest.raises(ValueError) as exc_info:
        calculate_total(items)

    assert "Price cannot be negative" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


def test_calculate_total_handles_very_large_numbers():
    """Large numbers should not cause overflow."""
    items = [
        {"product_id": 1, "price": Decimal("999999999.99"), "quantity": 1000}
    ]

    result = calculate_total(items)

    assert result == Decimal("999999999990.00")


def test_calculate_total_handles_decimal_precision():
    """Decimal precision should be maintained correctly."""
    items = [
        {"product_id": 1, "price": Decimal("0.01"), "quantity": 3},
        {"product_id": 2, "price": Decimal("0.02"), "quantity": 1},
    ]

    result = calculate_total(items)

    # 0.01*3 + 0.02*1 = 0.03 + 0.02 = 0.05
    assert result == Decimal("0.05")


# ---------------------------------------------------------------------------
# Tests Using Fixtures from conftest.py
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_with_db_session(db_session, unique_email):
    """User creation should persist to database."""
    user_data = {"email": unique_email, "name": "Test User"}

    user = await create_user(db_session, user_data)

    assert user.id is not None
    assert user.email == unique_email

    # Verify persistence
    fetched = await db_session.get(User, user.id)
    assert fetched is not None
    assert fetched.email == unique_email
