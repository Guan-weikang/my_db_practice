import asyncio
from pathlib import Path
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:123456@localhost:5432/family_tree_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_REFRESH_SECRET_KEY", "test-refresh-secret")
os.environ.setdefault("APP_ENV", "test")

from app.api.deps.auth import get_refresh_token_store
from app.api.deps.db import get_db_session
from app.core.token_store import InMemoryRefreshTokenStore
from app.db.session import AsyncSessionLocal
from app.main import app


@pytest_asyncio.fixture(loop_scope="session")
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncClient:
    token_store = InMemoryRefreshTokenStore()

    async def override_get_db_session():
        async with AsyncSessionLocal() as session:
            yield session

    def override_refresh_token_store() -> InMemoryRefreshTokenStore:
        return token_store

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_refresh_token_store] = override_refresh_token_store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
