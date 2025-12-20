"""
FastAPI dependency injection.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from {{PROJECT_NAME}}.db.session import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_session():
        yield session


# Type alias for database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]
