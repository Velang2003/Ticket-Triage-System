"""
Pytest configuration and shared fixtures.

Strategy:
- Use an in-memory SQLite database for fast unit tests (no PostgreSQL required).
- Provide mock LLM client and embedding functions as fixtures.
- Provide a real async HTTP test client via httpx.
- Auth header uses the real API key from Settings so tests always match the app.
"""
import logging
import uuid
from typing import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Silence noisy loggers before importing the app ───────────────────────────
# app/main.py calls configure_logging(level="DEBUG") at import time when
# DEBUG=true in .env.  We reset the loggers that flood the output here so
# pytest's own log_level setting takes effect.
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

# ── App imports (after logger suppression) ────────────────────────────────────
from app.core.config import get_settings
from app.db.session import get_db_session
from app.main import app
from app.models.base import Base

settings = get_settings()

# ── Test database ─────────────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a fresh in-memory SQLite engine per test function."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session backed by the test SQLite engine."""
    factory = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Return an httpx AsyncClient wired to the FastAPI app.
    Overrides the DB dependency with the test SQLite session.
    """
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── Auth header ───────────────────────────────────────────────────────────────
@pytest.fixture
def auth_headers() -> dict[str, str]:
    """
    Return the X-API-Key header using the same key that the app reads from
    Settings.  This ensures tests always authenticate correctly regardless of
    what API_KEY is set to in .env.
    """
    return {"X-API-Key": settings.api_key}


# ── Mock LLM fixtures ─────────────────────────────────────────────────────────
@pytest.fixture
def mock_llm_classify():
    """Mock generate_json to return a valid classification response."""
    with patch("app.services.classification_service.generate_json") as mock:
        mock.return_value = {
            "category": "Technical",
            "priority": "High",
            "rationale": "The issue describes a software bug.",
        }
        yield mock


@pytest.fixture
def mock_llm_suggest():
    """Mock generate_text to return a canned suggestion."""
    with patch("app.services.rag_service.generate_text") as mock:
        mock.return_value = "Please restart the service and check the logs for error codes."
        yield mock


@pytest.fixture
def mock_embedding():
    """Mock get_embedding in rag_service to return a zero vector (no real API call)."""
    with patch("app.services.rag_service.get_embedding") as mock:
        mock.return_value = [0.0] * 768
        yield mock


@pytest.fixture
def mock_embedding_article():
    """Mock get_embedding in knowledge_article_service."""
    with patch("app.services.knowledge_article_service.get_embedding") as mock:
        mock.return_value = [0.0] * 768
        yield mock


# ── Seed helpers ──────────────────────────────────────────────────────────────
@pytest.fixture
def sample_ticket_payload() -> dict:
    return {
        "subject": "Cannot log into my account",
        "description": "I keep getting an 'Invalid credentials' error even after resetting my password.",
        "submitter_email": "user@example.com",
    }
