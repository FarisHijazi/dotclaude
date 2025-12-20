"""
Integration tests for {{MODULE_NAME}}.

Integration tests verify that multiple components work together correctly.
They test API endpoints, database operations, and service interactions.

Key characteristics:
- Test real database operations (with test database)
- Test actual HTTP endpoints
- May use mocks for external services (APIs, email, etc.)

Dual-mode support:
- Default: Direct ASGI testing (fast, no server needed)
- Live: Set TEST_SERVER_URL=http://localhost:8000

Run:
    pytest tests/integration/
    pytest tests/integration/{{MODULE_NAME}}_test.py -v
    TEST_SERVER_URL=http://localhost:8000 pytest tests/integration/
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Basic Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """Health check endpoint should return 200 OK."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_root_endpoint_returns_api_info(client: AsyncClient):
    """Root endpoint should return API information."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


# ---------------------------------------------------------------------------
# CRUD Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_resource_returns_201(
    client: AsyncClient,
    auth_headers: dict,
):
    """POST request should create resource and return 201."""
    payload = {
        "name": "Test Resource",
        "description": "A test resource",
    }

    response = await client.post(
        "/api/v1/resources",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_resource_returns_created_resource(
    client: AsyncClient,
    auth_headers: dict,
):
    """GET request should return previously created resource."""
    # Create resource
    create_resp = await client.post(
        "/api/v1/resources",
        json={"name": "Fetch Me", "description": "Test"},
        headers=auth_headers,
    )
    resource_id = create_resp.json()["id"]

    # Fetch resource
    response = await client.get(
        f"/api/v1/resources/{resource_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Fetch Me"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_resource_modifies_data(
    client: AsyncClient,
    auth_headers: dict,
):
    """PATCH request should update resource fields."""
    # Create
    create_resp = await client.post(
        "/api/v1/resources",
        json={"name": "Original", "description": "Original desc"},
        headers=auth_headers,
    )
    resource_id = create_resp.json()["id"]

    # Update
    update_resp = await client.patch(
        f"/api/v1/resources/{resource_id}",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Original desc"  # Unchanged


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_resource_removes_from_database(
    client: AsyncClient,
    auth_headers: dict,
):
    """DELETE request should remove resource."""
    # Create
    create_resp = await client.post(
        "/api/v1/resources",
        json={"name": "Delete Me", "description": "Test"},
        headers=auth_headers,
    )
    resource_id = create_resp.json()["id"]

    # Delete
    delete_resp = await client.delete(
        f"/api/v1/resources/{resource_id}",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 204

    # Verify gone
    get_resp = await client.get(
        f"/api/v1/resources/{resource_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client: AsyncClient):
    """Protected endpoint without auth should return 401."""
    response = await client.get("/api/v1/resources")

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_accepts_valid_token(
    client: AsyncClient,
    auth_headers: dict,
):
    """Protected endpoint with valid token should return 200."""
    response = await client.get(
        "/api/v1/resources",
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient):
    """Expired token should return 401 Unauthorized."""
    expired_headers = {"Authorization": "Bearer expired.token.here"}

    response = await client.get(
        "/api/v1/resources",
        headers=expired_headers,
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_with_invalid_data_returns_422(
    client: AsyncClient,
    auth_headers: dict,
):
    """Invalid request body should return 422 Unprocessable Entity."""
    invalid_payload = {
        "name": "",  # Empty name (invalid)
        "description": "Test",
    }

    response = await client.post(
        "/api/v1/resources",
        json=invalid_payload,
        headers=auth_headers,
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("name" in str(e).lower() for e in errors)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_with_missing_required_field_returns_422(
    client: AsyncClient,
    auth_headers: dict,
):
    """Missing required field should return 422."""
    incomplete_payload = {"description": "Missing name field"}

    response = await client.post(
        "/api/v1/resources",
        json=incomplete_payload,
        headers=auth_headers,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Pagination Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_endpoint_returns_paginated_results(
    client: AsyncClient,
    auth_headers: dict,
):
    """List endpoint should return paginated results."""
    # Create multiple resources
    for i in range(5):
        await client.post(
            "/api/v1/resources",
            json={"name": f"Resource {i}", "description": "Test"},
            headers=auth_headers,
        )

    # Fetch with pagination
    response = await client.get(
        "/api/v1/resources?limit=2&offset=0",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert "limit" in data
    assert "offset" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_endpoint_respects_limit(
    client: AsyncClient,
    auth_headers: dict,
):
    """List endpoint should respect limit parameter."""
    response = await client.get(
        "/api/v1/resources?limit=1",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) <= 1


# ---------------------------------------------------------------------------
# Database Interaction Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_rollback_on_error(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
):
    """Failed operations should rollback database changes."""
    # Get initial count
    initial_response = await client.get(
        "/api/v1/resources",
        headers=auth_headers,
    )
    initial_count = initial_response.json()["total"]

    # Attempt operation that will fail (e.g., duplicate unique field)
    await client.post(
        "/api/v1/resources",
        json={"name": "Unique Name", "description": "First"},
        headers=auth_headers,
    )

    # Try to create duplicate (should fail)
    duplicate_response = await client.post(
        "/api/v1/resources",
        json={"name": "Unique Name", "description": "Duplicate"},
        headers=auth_headers,
    )

    # Verify count increased by exactly 1 (duplicate was rejected)
    final_response = await client.get(
        "/api/v1/resources",
        headers=auth_headers,
    )
    final_count = final_response.json()["total"]

    assert final_count == initial_count + 1


# ---------------------------------------------------------------------------
# Error Response Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_not_found_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    """Non-existent resource should return 404."""
    response = await client.get(
        "/api/v1/resources/99999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_method_not_allowed_returns_405(client: AsyncClient):
    """Invalid HTTP method should return 405."""
    response = await client.put("/api/v1/health")  # PUT not allowed

    assert response.status_code == 405


# ---------------------------------------------------------------------------
# Live Server Tests (only run with TEST_SERVER_URL)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.live_only
@pytest.mark.asyncio
async def test_live_server_health(live_client: AsyncClient):
    """Live server health check."""
    response = await live_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.live_only
@pytest.mark.asyncio
async def test_live_server_response_time(live_client: AsyncClient):
    """Live server should respond within acceptable time."""
    import time

    start = time.time()
    response = await live_client.get("/api/v1/health")
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 1.0  # Should respond within 1 second
