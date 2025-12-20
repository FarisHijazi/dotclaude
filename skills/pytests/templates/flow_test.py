"""
User flow tests for {{JOURNEY_NAME}}.

User flow tests simulate complete user journeys through the application.
They test real-world scenarios from a user's perspective.

Key characteristics:
- Test complete user stories/scenarios
- Multiple steps in a logical sequence
- Verify user experience, not just API responses
- Test the "happy path" and common edge cases

When to use:
- Testing user onboarding
- Verifying critical business workflows
- Testing multi-step processes
- Validating user stories from tickets

Run:
    pytest tests/flows/ -v
    pytest tests/flows/ -m flow
    TEST_SERVER_URL=http://localhost:8000 pytest tests/flows/
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# New User Onboarding Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_new_user_complete_onboarding(
    client: AsyncClient,
    unique_email: str,
):
    """
    New user journey: register -> verify -> setup profile -> first purchase.

    User story: As a new user, I want to sign up and make my first purchase.
    """
    password = "SecurePassword123!"

    # === REGISTER ===
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "name": "New User",
        },
    )
    assert register_resp.status_code == 201, "Registration should succeed"
    user_data = register_resp.json()
    assert user_data["email"] == unique_email

    # === LOGIN ===
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_resp.status_code == 200, "Login should succeed"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # === COMPLETE PROFILE ===
    profile_resp = await client.patch(
        "/api/v1/users/me/profile",
        json={
            "phone": "+1234567890",
            "date_of_birth": "1990-01-15",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "90210",
                "country": "US",
            },
        },
        headers=headers,
    )
    assert profile_resp.status_code == 200, "Profile update should succeed"

    # === BROWSE PRODUCTS ===
    products_resp = await client.get(
        "/api/v1/products?category=recommended&limit=10",
    )
    assert products_resp.status_code == 200, "Should see products"
    products = products_resp.json()["items"]
    assert len(products) > 0, "Should have products available"

    # === ADD TO CART ===
    add_cart_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": products[0]["id"], "quantity": 1},
        headers=headers,
    )
    assert add_cart_resp.status_code == 201, "Should add to cart"

    # === CHECKOUT ===
    checkout_resp = await client.post(
        "/api/v1/checkout",
        json={
            "payment_method": "card",
            "use_profile_address": True,
        },
        headers=headers,
    )
    assert checkout_resp.status_code == 200, "Checkout should succeed"
    order = checkout_resp.json()

    # === CONFIRM ORDER ===
    confirm_resp = await client.post(
        f"/api/v1/orders/{order['order_id']}/confirm",
        json={"payment_token": "test_payment_token"},
        headers=headers,
    )
    assert confirm_resp.status_code == 200, "Order confirmation should succeed"
    assert confirm_resp.json()["status"] == "confirmed"

    # === VERIFY USER STATE ===
    me_resp = await client.get("/api/v1/users/me", headers=headers)
    me_data = me_resp.json()
    assert me_data["profile_completed"] is True
    assert me_data["first_purchase_completed"] is True


# ---------------------------------------------------------------------------
# Returning User Shopping Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_returning_user_quick_purchase(
    client: AsyncClient,
    registered_user: dict,
    auth_headers: dict,
):
    """
    Returning user journey: login -> quick add -> express checkout.

    User story: As a returning customer, I want to quickly reorder.
    """
    # === VIEW ORDER HISTORY ===
    history_resp = await client.get(
        "/api/v1/orders?limit=5",
        headers=auth_headers,
    )
    assert history_resp.status_code == 200

    # === QUICK ADD FROM FAVORITES/HISTORY ===
    # (Assuming user has saved favorites or past orders)
    products_resp = await client.get("/api/v1/products?limit=1")
    product_id = products_resp.json()["items"][0]["id"]

    await client.post(
        "/api/v1/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers=auth_headers,
    )

    # === EXPRESS CHECKOUT (uses saved payment/address) ===
    express_resp = await client.post(
        "/api/v1/checkout/express",
        json={"use_saved_payment": True, "use_saved_address": True},
        headers=auth_headers,
    )

    # Express checkout might not be implemented - handle gracefully
    if express_resp.status_code == 404:
        # Fallback to regular checkout
        checkout_resp = await client.post(
            "/api/v1/checkout",
            json={
                "payment_method": "card",
                "shipping_address": {
                    "street": "123 Quick St",
                    "city": "Fast City",
                    "postal_code": "12345",
                    "country": "US",
                },
            },
            headers=auth_headers,
        )
        assert checkout_resp.status_code == 200
    else:
        assert express_resp.status_code == 200


# ---------------------------------------------------------------------------
# Account Management Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_user_account_management(
    client: AsyncClient,
    registered_user: dict,
    auth_headers: dict,
):
    """
    Account management: update email -> change password -> update preferences.

    User story: As a user, I want to manage my account settings.
    """
    # === VIEW CURRENT SETTINGS ===
    me_resp = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me_resp.status_code == 200
    original_email = me_resp.json()["email"]

    # === UPDATE NOTIFICATION PREFERENCES ===
    prefs_resp = await client.patch(
        "/api/v1/users/me/preferences",
        json={
            "email_notifications": True,
            "push_notifications": False,
            "marketing_emails": False,
            "order_updates": True,
        },
        headers=auth_headers,
    )
    assert prefs_resp.status_code == 200

    # === CHANGE PASSWORD ===
    password_resp = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": registered_user["password"],
            "new_password": "NewSecurePassword456!",
        },
        headers=auth_headers,
    )
    assert password_resp.status_code == 200

    # === VERIFY NEW PASSWORD WORKS ===
    new_login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": original_email,
            "password": "NewSecurePassword456!",
        },
    )
    assert new_login_resp.status_code == 200

    # === ADD PAYMENT METHOD ===
    payment_resp = await client.post(
        "/api/v1/users/me/payment-methods",
        json={
            "type": "card",
            "token": "test_card_token",
            "is_default": True,
        },
        headers=auth_headers,
    )
    # May not be implemented
    if payment_resp.status_code != 404:
        assert payment_resp.status_code in (200, 201)


# ---------------------------------------------------------------------------
# Customer Support Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_customer_support_ticket_flow(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Support flow: create ticket -> add message -> resolve.

    User story: As a user, I want to get help with an issue.
    """
    # === CREATE SUPPORT TICKET ===
    ticket_resp = await client.post(
        "/api/v1/support/tickets",
        json={
            "subject": "Order Issue",
            "category": "orders",
            "description": "I have a question about my order",
            "priority": "normal",
        },
        headers=auth_headers,
    )

    # Support might not be implemented
    if ticket_resp.status_code == 404:
        pytest.skip("Support tickets not implemented")

    assert ticket_resp.status_code == 201
    ticket = ticket_resp.json()
    ticket_id = ticket["id"]
    assert ticket["status"] == "open"

    # === ADD MESSAGE TO TICKET ===
    message_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        json={"content": "Here are more details about my issue..."},
        headers=auth_headers,
    )
    assert message_resp.status_code == 201

    # === VIEW TICKET HISTORY ===
    history_resp = await client.get(
        f"/api/v1/support/tickets/{ticket_id}",
        headers=auth_headers,
    )
    assert history_resp.status_code == 200
    ticket_data = history_resp.json()
    assert len(ticket_data["messages"]) >= 1

    # === VIEW ALL USER TICKETS ===
    list_resp = await client.get(
        "/api/v1/support/tickets",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    assert any(t["id"] == ticket_id for t in list_resp.json()["items"])


# ---------------------------------------------------------------------------
# Product Review Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_product_review_flow(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Review flow: view product -> purchase -> leave review -> view reviews.

    User story: As a user, I want to review products I've purchased.
    """
    # === FIND A PRODUCT ===
    products_resp = await client.get("/api/v1/products?limit=1")
    product = products_resp.json()["items"][0]
    product_id = product["id"]

    # === VIEW EXISTING REVIEWS ===
    reviews_resp = await client.get(f"/api/v1/products/{product_id}/reviews")
    assert reviews_resp.status_code == 200
    initial_count = reviews_resp.json().get("total", 0)

    # === PURCHASE PRODUCT (simplified) ===
    await client.post(
        "/api/v1/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers=auth_headers,
    )

    checkout_resp = await client.post(
        "/api/v1/checkout",
        json={
            "payment_method": "card",
            "shipping_address": {
                "street": "123 Review St",
                "city": "Test City",
                "postal_code": "12345",
                "country": "US",
            },
        },
        headers=auth_headers,
    )

    if checkout_resp.status_code == 200:
        order_id = checkout_resp.json()["order_id"]
        await client.post(
            f"/api/v1/orders/{order_id}/confirm",
            json={"payment_token": "test_token"},
            headers=auth_headers,
        )

    # === LEAVE REVIEW ===
    review_resp = await client.post(
        f"/api/v1/products/{product_id}/reviews",
        json={
            "rating": 5,
            "title": "Great product!",
            "content": "This product exceeded my expectations.",
        },
        headers=auth_headers,
    )

    # Review might require verified purchase or not be implemented
    if review_resp.status_code in (201, 200):
        review_id = review_resp.json()["id"]

        # === VERIFY REVIEW APPEARS ===
        updated_reviews = await client.get(
            f"/api/v1/products/{product_id}/reviews"
        )
        assert updated_reviews.json()["total"] > initial_count

        # === UPDATE REVIEW ===
        update_resp = await client.patch(
            f"/api/v1/products/{product_id}/reviews/{review_id}",
            json={"content": "Updated: Still a great product!"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200


# ---------------------------------------------------------------------------
# Wishlist/Favorites Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_wishlist_management_flow(
    client: AsyncClient,
    auth_headers: dict,
):
    """
    Wishlist flow: browse -> add to wishlist -> move to cart -> purchase.

    User story: As a user, I want to save items for later.
    """
    # === GET PRODUCTS ===
    products_resp = await client.get("/api/v1/products?limit=3")
    products = products_resp.json()["items"]

    if len(products) < 2:
        pytest.skip("Need at least 2 products for wishlist test")

    # === ADD TO WISHLIST ===
    for product in products[:2]:
        add_resp = await client.post(
            "/api/v1/wishlist",
            json={"product_id": product["id"]},
            headers=auth_headers,
        )
        # Wishlist might not be implemented
        if add_resp.status_code == 404:
            pytest.skip("Wishlist not implemented")
        assert add_resp.status_code in (200, 201)

    # === VIEW WISHLIST ===
    wishlist_resp = await client.get("/api/v1/wishlist", headers=auth_headers)
    assert wishlist_resp.status_code == 200
    wishlist = wishlist_resp.json()
    assert len(wishlist["items"]) >= 2

    # === MOVE ITEM TO CART ===
    first_item_id = wishlist["items"][0]["product_id"]
    move_resp = await client.post(
        f"/api/v1/wishlist/{first_item_id}/move-to-cart",
        headers=auth_headers,
    )
    assert move_resp.status_code == 200

    # === VERIFY CART ===
    cart_resp = await client.get("/api/v1/cart", headers=auth_headers)
    assert cart_resp.status_code == 200
    cart_product_ids = [item["product_id"] for item in cart_resp.json()["items"]]
    assert first_item_id in cart_product_ids

    # === VERIFY REMOVED FROM WISHLIST ===
    updated_wishlist = await client.get("/api/v1/wishlist", headers=auth_headers)
    wishlist_ids = [item["product_id"] for item in updated_wishlist.json()["items"]]
    assert first_item_id not in wishlist_ids


# ---------------------------------------------------------------------------
# Error Recovery Flows
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_password_reset_flow(
    client: AsyncClient,
    unique_email: str,
):
    """
    Password reset: request reset -> (verify email) -> set new password.

    User story: As a user who forgot my password, I want to reset it.
    """
    # First register a user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "OldPassword123!",
            "name": "Reset User",
        },
    )

    # === REQUEST PASSWORD RESET ===
    reset_request_resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": unique_email},
    )

    # Might not be implemented
    if reset_request_resp.status_code == 404:
        pytest.skip("Password reset not implemented")

    assert reset_request_resp.status_code == 200

    # === SIMULATE EMAIL VERIFICATION ===
    # In real tests, you'd need to mock the email service
    # and extract the reset token. For this template, we skip.

    # === SET NEW PASSWORD ===
    # reset_resp = await client.post(
    #     "/api/v1/auth/reset-password",
    #     json={
    #         "token": "reset_token_from_email",
    #         "new_password": "NewPassword456!",
    #     },
    # )
    # assert reset_resp.status_code == 200

    # === VERIFY NEW PASSWORD WORKS ===
    # login_resp = await client.post(
    #     "/api/v1/auth/login",
    #     json={"email": unique_email, "password": "NewPassword456!"},
    # )
    # assert login_resp.status_code == 200


# ---------------------------------------------------------------------------
# Multi-User Interaction Flow
# ---------------------------------------------------------------------------


@pytest.mark.flow
@pytest.mark.asyncio
async def test_multi_user_interaction(client: AsyncClient):
    """
    Multi-user scenario: user A shares product with user B.

    User story: As a user, I want to share products with friends.
    """
    # === CREATE TWO USERS ===
    user_a_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_a_{__import__('uuid').uuid4().hex[:8]}@test.com",
            "password": "Password123!",
            "name": "User A",
        },
    )
    user_b_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_b_{__import__('uuid').uuid4().hex[:8]}@test.com",
            "password": "Password123!",
            "name": "User B",
        },
    )

    if user_a_resp.status_code != 201 or user_b_resp.status_code != 201:
        pytest.skip("Could not create test users")

    # Login both users
    login_a = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user_a_resp.json()["email"],
            "password": "Password123!",
        },
    )
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    user_b_id = user_b_resp.json()["id"]

    # === USER A FINDS PRODUCT ===
    products = await client.get("/api/v1/products?limit=1")
    product_id = products.json()["items"][0]["id"]

    # === USER A SHARES WITH USER B ===
    share_resp = await client.post(
        "/api/v1/products/share",
        json={
            "product_id": product_id,
            "recipient_user_id": user_b_id,
            "message": "Check out this product!",
        },
        headers=headers_a,
    )

    # Sharing might not be implemented
    if share_resp.status_code == 404:
        pytest.skip("Product sharing not implemented")

    assert share_resp.status_code in (200, 201)
