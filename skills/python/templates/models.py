"""
SQLModel database models.

SQLModel combines SQLAlchemy and Pydantic, providing:
- Database ORM capabilities
- Pydantic validation
- Type hints and IDE support
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class UUIDMixin(SQLModel):
    """Mixin for UUID primary key."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class BaseModel(UUIDMixin, TimestampMixin, SQLModel):
    """Base model with UUID primary key and timestamps."""

    pass


# Example model - replace with your own models
class Item(BaseModel, table=True):
    """Example item model."""

    __tablename__ = "items"

    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)
    is_active: bool = Field(default=True)


# Pydantic schemas for API (without table=True)
class ItemCreate(SQLModel):
    """Schema for creating an item."""

    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)


class ItemUpdate(SQLModel):
    """Schema for updating an item."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ItemRead(BaseModel):
    """Schema for reading an item."""

    name: str
    description: str | None
    price: float
    is_active: bool
