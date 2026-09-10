"""Knowledge article service — add/update articles with automatic embedding."""
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.embedding import get_embedding
from app.models.ticket import TicketCategory
from app.repositories import knowledge_article_repo

logger = logging.getLogger(__name__)


async def add_article(
    session: AsyncSession,
    title: str,
    content: str,
    category: TicketCategory | None = None,
) -> dict[str, Any]:
    """Add a new knowledge article and embed it for RAG retrieval."""
    embedding = await _embed_article(title, content)
    article = await knowledge_article_repo.create_article(
        session,
        {"title": title, "content": content, "category": category, "embedding": embedding},
    )
    logger.info("Knowledge article added", extra={"article_id": str(article.id), "title": title})
    return _article_to_dict(article)


async def update_article(
    session: AsyncSession,
    article_id: uuid.UUID,
    title: str | None = None,
    content: str | None = None,
    category: TicketCategory | None = None,
) -> dict[str, Any] | None:
    """Update article and re-embed if title or content changed."""
    existing = await knowledge_article_repo.get_article_by_id(session, article_id)
    if existing is None:
        return None

    new_title = title if title is not None else existing.title
    new_content = content if content is not None else existing.content
    new_category = category if category is not None else existing.category

    embedding = await _embed_article(new_title, new_content)
    article = await knowledge_article_repo.update_article(
        session,
        article_id,
        {"title": new_title, "content": new_content, "category": new_category, "embedding": embedding},
    )
    logger.info("Knowledge article updated", extra={"article_id": str(article_id)})
    return _article_to_dict(article) if article else None


async def list_articles(
    session: AsyncSession,
    category: TicketCategory | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    articles = await knowledge_article_repo.list_articles(session, category=category, page=page, page_size=page_size)
    return [_article_to_dict(a) for a in articles]


async def _embed_article(title: str, content: str) -> list[float]:
    """Embed the combined title + content."""
    text = f"{title}\n\n{content}"
    return await get_embedding(text)


def _article_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "title": a.title,
        "content": a.content,
        "category": a.category.value if a.category else None,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }
