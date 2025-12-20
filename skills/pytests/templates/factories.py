"""
Test data factories using factory_boy.

Factories provide consistent, customizable test data generation.
Place in tests/fixtures/factories.py.

Usage:
    from tests.fixtures.factories import UserFactory, ProductFactory

    # Create instance (not persisted)
    user = UserFactory.build()

    # Create and persist to database
    user = await UserFactory.create_async(session)

    # Create with overrides
    admin = UserFactory.build(is_admin=True, email="admin@test.com")

    # Create batch
    users = UserFactory.build_batch(5)
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

import factory
from faker import Faker

# Initialize Faker with seed for reproducible tests
fake = Faker()
Faker.seed(12345)  # Remove for random data each run


# ---------------------------------------------------------------------------
# Base Factory
# ---------------------------------------------------------------------------


class BaseFactory(factory.Factory):
    """
    Base factory with common patterns.

    For SQLModel/SQLAlchemy models, inherit from this.
    """

    class Meta:
        abstract = True

    @classmethod
    async def create_async(cls, session, **kwargs) -> Any:
        """Create and persist instance to async database session."""
        instance = cls.build(**kwargs)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        return instance

    @classmethod
    async def create_batch_async(cls, session, size: int, **kwargs) -> list[Any]:
        """Create and persist multiple instances."""
        instances = cls.build_batch(size, **kwargs)
        for instance in instances:
            session.add(instance)
        await session.commit()
        for instance in instances:
            await session.refresh(instance)
        return instances


# ---------------------------------------------------------------------------
# User Factories
# ---------------------------------------------------------------------------


class UserFactory(BaseFactory):
    """
    Factory for User model.

    Examples:
        user = UserFactory.build()
        admin = UserFactory.build(is_admin=True)
        verified = UserFactory.build(email_verified=True)
    """

    class Meta:
        # model = User  # Uncomment and set your User model
        pass

    id = factory.LazyFunction(lambda: uuid4())
    email = factory.LazyFunction(lambda: fake.unique.email())
    name = factory.LazyFunction(lambda: fake.name())
    password_hash = factory.LazyAttribute(lambda _: "hashed_password_placeholder")
    is_active = True
    is_admin = False
    email_verified = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    # Related objects
    # profile = factory.SubFactory(UserProfileFactory)

    class Params:
        """Traits for common user states."""

        admin = factory.Trait(is_admin=True, email_verified=True)
        verified = factory.Trait(email_verified=True)
        inactive = factory.Trait(is_active=False)


class UserProfileFactory(BaseFactory):
    """Factory for user profile data."""

    class Meta:
        # model = UserProfile
        pass

    user_id = factory.LazyFunction(lambda: uuid4())
    phone = factory.LazyFunction(lambda: fake.phone_number())
    bio = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    avatar_url = factory.LazyFunction(lambda: fake.image_url())
    date_of_birth = factory.LazyFunction(lambda: fake.date_of_birth(minimum_age=18))


# ---------------------------------------------------------------------------
# Product Factories
# ---------------------------------------------------------------------------


class ProductFactory(BaseFactory):
    """
    Factory for Product model.

    Examples:
        product = ProductFactory.build()
        expensive = ProductFactory.build(price=Decimal("999.99"))
        out_of_stock = ProductFactory.build(stock=0)
    """

    class Meta:
        # model = Product
        pass

    id = factory.LazyFunction(lambda: uuid4())
    name = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    price = factory.LazyFunction(
        lambda: Decimal(str(fake.pydecimal(min_value=1, max_value=500, right_digits=2)))
    )
    stock = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    category = factory.LazyFunction(lambda: fake.word())
    sku = factory.LazyFunction(lambda: fake.bothify(text="???-####").upper())
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        out_of_stock = factory.Trait(stock=0)
        expensive = factory.Trait(
            price=factory.LazyFunction(
                lambda: Decimal(
                    str(fake.pydecimal(min_value=500, max_value=5000, right_digits=2))
                )
            )
        )
        cheap = factory.Trait(
            price=factory.LazyFunction(
                lambda: Decimal(
                    str(fake.pydecimal(min_value=1, max_value=20, right_digits=2))
                )
            )
        )


class CategoryFactory(BaseFactory):
    """Factory for product categories."""

    class Meta:
        # model = Category
        pass

    id = factory.LazyFunction(lambda: uuid4())
    name = factory.LazyFunction(lambda: fake.word().capitalize())
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    description = factory.LazyFunction(lambda: fake.sentence())
    parent_id = None


# ---------------------------------------------------------------------------
# Order Factories
# ---------------------------------------------------------------------------


class OrderFactory(BaseFactory):
    """
    Factory for Order model.

    Examples:
        order = OrderFactory.build(user_id=user.id)
        pending = OrderFactory.build(status="pending")
    """

    class Meta:
        # model = Order
        pass

    id = factory.LazyFunction(lambda: uuid4())
    user_id = factory.LazyFunction(lambda: uuid4())
    status = "pending"
    total = factory.LazyFunction(
        lambda: Decimal(str(fake.pydecimal(min_value=10, max_value=1000, right_digits=2)))
    )
    currency = "USD"
    shipping_address = factory.LazyFunction(
        lambda: {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "postal_code": fake.postcode(),
            "country": "US",
        }
    )
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        confirmed = factory.Trait(status="confirmed")
        shipped = factory.Trait(status="shipped")
        delivered = factory.Trait(status="delivered")
        cancelled = factory.Trait(status="cancelled")


class OrderItemFactory(BaseFactory):
    """Factory for order line items."""

    class Meta:
        # model = OrderItem
        pass

    id = factory.LazyFunction(lambda: uuid4())
    order_id = factory.LazyFunction(lambda: uuid4())
    product_id = factory.LazyFunction(lambda: uuid4())
    quantity = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    unit_price = factory.LazyFunction(
        lambda: Decimal(str(fake.pydecimal(min_value=5, max_value=200, right_digits=2)))
    )

    @factory.lazy_attribute
    def total_price(self):
        return self.unit_price * self.quantity


# ---------------------------------------------------------------------------
# Cart Factories
# ---------------------------------------------------------------------------


class CartFactory(BaseFactory):
    """Factory for shopping cart."""

    class Meta:
        # model = Cart
        pass

    id = factory.LazyFunction(lambda: uuid4())
    user_id = factory.LazyFunction(lambda: uuid4())
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class CartItemFactory(BaseFactory):
    """Factory for cart items."""

    class Meta:
        # model = CartItem
        pass

    id = factory.LazyFunction(lambda: uuid4())
    cart_id = factory.LazyFunction(lambda: uuid4())
    product_id = factory.LazyFunction(lambda: uuid4())
    quantity = factory.LazyFunction(lambda: fake.random_int(min=1, max=10))


# ---------------------------------------------------------------------------
# Authentication Factories
# ---------------------------------------------------------------------------


class TokenFactory(BaseFactory):
    """Factory for auth tokens."""

    class Meta:
        # model = Token
        pass

    token = factory.LazyFunction(lambda: fake.sha256())
    user_id = factory.LazyFunction(lambda: uuid4())
    token_type = "access"
    expires_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc).replace(year=datetime.now().year + 1)
    )
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        expired = factory.Trait(
            expires_at=factory.LazyFunction(
                lambda: datetime.now(timezone.utc).replace(year=datetime.now().year - 1)
            )
        )
        refresh = factory.Trait(token_type="refresh")


# ---------------------------------------------------------------------------
# Address Factory
# ---------------------------------------------------------------------------


class AddressFactory(BaseFactory):
    """Factory for addresses."""

    class Meta:
        # model = Address
        pass

    id = factory.LazyFunction(lambda: uuid4())
    user_id = factory.LazyFunction(lambda: uuid4())
    street = factory.LazyFunction(lambda: fake.street_address())
    city = factory.LazyFunction(lambda: fake.city())
    state = factory.LazyFunction(lambda: fake.state_abbr())
    postal_code = factory.LazyFunction(lambda: fake.postcode())
    country = "US"
    is_default = False

    class Params:
        default = factory.Trait(is_default=True)
        international = factory.Trait(
            country=factory.LazyFunction(lambda: fake.country_code()),
            state=factory.LazyFunction(lambda: fake.state()),
        )


# ---------------------------------------------------------------------------
# Review Factory
# ---------------------------------------------------------------------------


class ReviewFactory(BaseFactory):
    """Factory for product reviews."""

    class Meta:
        # model = Review
        pass

    id = factory.LazyFunction(lambda: uuid4())
    user_id = factory.LazyFunction(lambda: uuid4())
    product_id = factory.LazyFunction(lambda: uuid4())
    rating = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4))
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=300))
    is_verified_purchase = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        positive = factory.Trait(rating=factory.LazyFunction(lambda: fake.random_int(min=4, max=5)))
        negative = factory.Trait(rating=factory.LazyFunction(lambda: fake.random_int(min=1, max=2)))


# ---------------------------------------------------------------------------
# Support Ticket Factory
# ---------------------------------------------------------------------------


class TicketFactory(BaseFactory):
    """Factory for support tickets."""

    class Meta:
        # model = Ticket
        pass

    id = factory.LazyFunction(lambda: uuid4())
    user_id = factory.LazyFunction(lambda: uuid4())
    subject = factory.LazyFunction(lambda: fake.sentence(nb_words=5))
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    category = factory.LazyFunction(
        lambda: fake.random_element(["billing", "technical", "orders", "general"])
    )
    priority = "normal"
    status = "open"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    class Params:
        urgent = factory.Trait(priority="high")
        resolved = factory.Trait(status="resolved")
        in_progress = factory.Trait(status="in_progress")


# ---------------------------------------------------------------------------
# Fixture Helpers
# ---------------------------------------------------------------------------


def create_user_with_profile(**user_kwargs) -> tuple:
    """Create user with associated profile."""
    user = UserFactory.build(**user_kwargs)
    profile = UserProfileFactory.build(user_id=user.id)
    return user, profile


def create_order_with_items(
    user_id,
    num_items: int = 3,
    **order_kwargs,
) -> tuple:
    """Create order with line items."""
    order = OrderFactory.build(user_id=user_id, **order_kwargs)
    items = OrderItemFactory.build_batch(num_items, order_id=order.id)

    # Calculate total from items
    order.total = sum(item.total_price for item in items)

    return order, items


def create_product_catalog(num_products: int = 10) -> list:
    """Create a catalog of diverse products."""
    products = []

    # Mix of product types
    products.extend(ProductFactory.build_batch(num_products // 2))
    products.extend(ProductFactory.build_batch(num_products // 4, cheap=True))
    products.extend(ProductFactory.build_batch(num_products // 4, expensive=True))

    return products


# ---------------------------------------------------------------------------
# Pytest Fixtures for Factories
# ---------------------------------------------------------------------------


def pytest_fixtures():
    """
    Copy these fixtures to your conftest.py.

    Example:
        @pytest.fixture
        def user_factory():
            return UserFactory

        @pytest.fixture
        def product_factory():
            return ProductFactory
    """
    pass


# Example conftest.py additions:
"""
@pytest.fixture
def user_factory():
    return UserFactory

@pytest.fixture
def product_factory():
    return ProductFactory

@pytest.fixture
def order_factory():
    return OrderFactory

@pytest.fixture
async def sample_user(db_session):
    return await UserFactory.create_async(db_session)

@pytest.fixture
async def sample_products(db_session):
    return await ProductFactory.create_batch_async(db_session, 5)
"""
