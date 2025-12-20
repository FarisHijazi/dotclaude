"""
End-to-end tests for {{FEATURE_NAME}}.

E2E tests verify complete request/response cycles through the full stack.
They simulate real client behavior and test the system as a whole.

Key characteristics:
- Test complete workflows from API request to database
- Minimal mocking (only external services)
- Test realistic scenarios
- Slower than unit/integration tests

Best for:
- Critical business workflows
- Complex multi-step operations
- Verifying system behavior end-to-end

Run:
    pytest tests/e2e/ -v
    pytest tests/e2e/ -m e2e
    TEST_SERVER_URL=http://localhost:8000 pytest tests/e2e/
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Complete Workflow Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_order_workflow(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Complete order flow: browse -> add to cart -> checkout -> confirm.

    This tests the entire purchase workflow as a real user would experience it.
    """
    # Step 1: Browse available products
    products_response = await client.get("/api/v1/products?in_stock=true")
    assert products_response.status_code == 200
    products = products_response.json()["items"]
    assert len(products) > 0, "No products available for testing"

    product = products[0]
    product_id = product["id"]

    # Step 2: Add product to cart
    cart_response = await client.post(
        "/api/v1/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers=auth_headers,
    )
    assert cart_response.status_code == 201
    cart = cart_response.json()
    assert len(cart["items"]) >= 1

    # Step 3: Review cart
    review_response = await client.get(
        "/api/v1/cart",
        headers=auth_headers,
    )
    assert review_response.status_code == 200
    cart_data = review_response.json()
    assert cart_data["total"] > 0

    # Step 4: Proceed to checkout
    checkout_response = await client.post(
        "/api/v1/checkout",
        json={
            "payment_method": "card",
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "US",
            },
        },
        headers=auth_headers,
    )
    assert checkout_response.status_code == 200
    order = checkout_response.json()
    order_id = order["order_id"]
    assert order["status"] == "pending"

    # Step 5: Confirm/pay order
    confirm_response = await client.post(
        f"/api/v1/orders/{order_id}/confirm",
        json={"payment_token": "test_token_123"},
        headers=auth_headers,
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"

    # Step 6: Verify order in history
    history_response = await client.get(
        "/api/v1/orders",
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    orders = history_response.json()["items"]
    order_ids = [o["id"] for o in orders]
    assert order_id in order_ids


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_user_registration_and_profile_setup(
    client: AsyncClient,
    unique_email: str,
):
    """
    Complete registration flow: register -> login -> setup profile -> verify.
    """
    password = "SecurePassword123!"

    # Step 1: Register new user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "name": "E2E Test User",
        },
    )
    assert register_response.status_code == 201
    user = register_response.json()
    user_id = user["id"]

    # Step 2: Login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Update profile
    profile_response = await client.patch(
        "/api/v1/users/me/profile",
        json={
            "phone": "+1234567890",
            "bio": "E2E test user biography",
            "preferences": {"notifications": True, "newsletter": False},
        },
        headers=headers,
    )
    assert profile_response.status_code == 200

    # Step 4: Verify profile is complete
    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == unique_email
    assert me_data["phone"] == "+1234567890"
    assert me_data["profile_completed"] is True


# ---------------------------------------------------------------------------
# Search and Filter Workflows
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_search_filter_and_sort_workflow(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Search workflow: search -> filter -> sort -> paginate.
    """
    # Step 1: Basic search
    search_response = await client.get(
        "/api/v1/products?q=test",
        headers=auth_headers,
    )
    assert search_response.status_code == 200
    results = search_response.json()
    assert "items" in results
    assert "total" in results

    # Step 2: Apply category filter
    filter_response = await client.get(
        "/api/v1/products?q=test&category=electronics",
        headers=auth_headers,
    )
    assert filter_response.status_code == 200

    # Step 3: Apply price filter
    price_response = await client.get(
        "/api/v1/products?min_price=10&max_price=100",
        headers=auth_headers,
    )
    assert price_response.status_code == 200
    for item in price_response.json()["items"]:
        assert 10 <= item["price"] <= 100

    # Step 4: Sort by price descending
    sort_response = await client.get(
        "/api/v1/products?sort_by=price&order=desc",
        headers=auth_headers,
    )
    assert sort_response.status_code == 200
    items = sort_response.json()["items"]
    if len(items) > 1:
        prices = [item["price"] for item in items]
        assert prices == sorted(prices, reverse=True)

    # Step 5: Paginate through results
    page1 = await client.get(
        "/api/v1/products?limit=2&offset=0",
        headers=auth_headers,
    )
    page2 = await client.get(
        "/api/v1/products?limit=2&offset=2",
        headers=auth_headers,
    )
    assert page1.status_code == 200
    assert page2.status_code == 200

    # Pages should have different items
    page1_ids = {item["id"] for item in page1.json()["items"]}
    page2_ids = {item["id"] for item in page2.json()["items"]}
    assert page1_ids.isdisjoint(page2_ids)


# ---------------------------------------------------------------------------
# Error Recovery Workflows
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_checkout_error_recovery(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Error recovery: failed checkout -> retry -> success.
    """
    # Setup: Add item to cart
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 1},
        headers=auth_headers,
    )

    # Step 1: Attempt checkout with invalid payment
    fail_response = await client.post(
        "/api/v1/checkout",
        json={"payment_method": "invalid_method"},
        headers=auth_headers,
    )
    assert fail_response.status_code in (400, 422)

    # Step 2: Verify cart is still intact
    cart_response = await client.get("/api/v1/cart", headers=auth_headers)
    assert cart_response.status_code == 200
    assert len(cart_response.json()["items"]) > 0

    # Step 3: Retry with valid payment
    success_response = await client.post(
        "/api/v1/checkout",
        json={
            "payment_method": "card",
            "shipping_address": {
                "street": "123 Retry St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "US",
            },
        },
        headers=auth_headers,
    )
    assert success_response.status_code == 200
    assert "order_id" in success_response.json()


# ---------------------------------------------------------------------------
# Concurrent Operations
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_concurrent_cart_modifications(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Concurrent operations: multiple cart updates should be consistent.
    """
    import asyncio

    # Add initial item
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 1},
        headers=auth_headers,
    )

    # Concurrent updates
    async def add_item(product_id: int):
        return await client.post(
            "/api/v1/cart/items",
            json={"product_id": product_id, "quantity": 1},
            headers=auth_headers,
        )

    responses = await asyncio.gather(
        add_item(2),
        add_item(3),
        add_item(4),
    )

    # All should succeed
    for resp in responses:
        assert resp.status_code in (200, 201)

    # Verify final cart state
    cart = await client.get("/api/v1/cart", headers=auth_headers)
    assert cart.status_code == 200
    assert len(cart.json()["items"]) >= 4


# ---------------------------------------------------------------------------
# Data Integrity Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_order_inventory_consistency(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Verify inventory is correctly decremented after order.
    """
    # Get initial stock
    product_resp = await client.get("/api/v1/products/1")
    initial_stock = product_resp.json()["stock"]

    # Create order
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": 1, "quantity": 2},
        headers=auth_headers,
    )

    checkout_resp = await client.post(
        "/api/v1/checkout",
        json={
            "payment_method": "card",
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "US",
            },
        },
        headers=auth_headers,
    )
    order_id = checkout_resp.json()["order_id"]

    await client.post(
        f"/api/v1/orders/{order_id}/confirm",
        json={"payment_token": "test_token"},
        headers=auth_headers,
    )

    # Verify stock decreased
    product_resp = await client.get("/api/v1/products/1")
    final_stock = product_resp.json()["stock"]
    assert final_stock == initial_stock - 2


# ---------------------------------------------------------------------------
# Live Server E2E Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.live_only
@pytest.mark.asyncio
async def test_live_complete_workflow(live_client: AsyncClient):
    """
    Full workflow against live server.

    Only runs when TEST_SERVER_URL is set.
    Tests the actual deployed system.
    """
    # Health check
    health = await live_client.get("/api/v1/health")
    assert health.status_code == 200

    # Public endpoints work
    products = await live_client.get("/api/v1/products?limit=5")
    assert products.status_code == 200
    assert len(products.json()["items"]) > 0


@pytest.mark.e2e
@pytest.mark.live_only
@pytest.mark.slow
@pytest.mark.asyncio
async def test_live_performance_under_load(live_client: AsyncClient):
    """
    Simple load test against live server.

    Only runs when TEST_SERVER_URL is set.
    Verifies system handles concurrent requests.
    """
    import asyncio
    import time

    async def make_request():
        start = time.time()
        resp = await live_client.get("/api/v1/health")
        elapsed = time.time() - start
        return resp.status_code, elapsed

    # Make 10 concurrent requests
    results = await asyncio.gather(*[make_request() for _ in range(10)])

    # All should succeed
    statuses = [r[0] for r in results]
    assert all(s == 200 for s in statuses)

    # Average response time should be reasonable
    times = [r[1] for r in results]
    avg_time = sum(times) / len(times)
    assert avg_time < 2.0  # Average under 2 seconds
