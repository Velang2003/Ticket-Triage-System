"""Unit tests for RAG service (SRS §8.3)."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import rag_service


@pytest.mark.asyncio
async def test_generate_suggestion_success(db_session, mock_embedding, mock_llm_suggest):
    """Happy path: articles found → suggestion generated and saved."""
    ticket_id = uuid.uuid4()

    # Mock an article returned from vector search
    fake_article = MagicMock()
    fake_article.id = uuid.uuid4()
    fake_article.title = "How to reset your password"
    fake_article.content = "Go to login page, click 'Forgot Password'..."

    with (
        patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[fake_article]),
        patch("app.services.rag_service.resolution_suggestion_repo.create_suggestion", new_callable=AsyncMock) as mock_save,
        patch("app.services.rag_service.audit_log_repo.create_entry", new_callable=AsyncMock),
    ):
        await rag_service.generate_suggestion(
            session=db_session,
            ticket_id=ticket_id,
            subject="Cannot log in",
            description="I get invalid credentials error.",
        )
        mock_save.assert_awaited_once()
        assert "Please restart" in mock_save.call_args.kwargs["suggested_text"]


@pytest.mark.asyncio
async def test_generate_suggestion_no_articles(db_session, mock_embedding):
    """If no articles match → suggestion is silently skipped (no save called)."""
    ticket_id = uuid.uuid4()

    with (
        patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]),
        patch("app.services.rag_service.resolution_suggestion_repo.create_suggestion", new_callable=AsyncMock) as mock_save,
    ):
        await rag_service.generate_suggestion(
            session=db_session,
            ticket_id=ticket_id,
            subject="Random issue",
            description="Something weird happened.",
        )
        mock_save.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_suggestion_embedding_failure_does_not_raise(db_session):
    """Embedding failure → logs error but does not propagate exception."""
    ticket_id = uuid.uuid4()

    with patch("app.services.rag_service.get_embedding", side_effect=RuntimeError("API error")):
        # Should not raise
        await rag_service.generate_suggestion(
            session=db_session,
            ticket_id=ticket_id,
            subject="Test",
            description="Test",
        )

