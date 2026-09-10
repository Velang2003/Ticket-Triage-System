"""Knowledge article repository — CRUD + pgvector similarity search."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_article import KnowledgeArticle
from app.models.ticket import TicketCategory


async def create_article(session: AsyncSession, data: dict[str, Any]) -> KnowledgeArticle:
    """Persist a new knowledge article (embedding must already be set in data)."""
    article = KnowledgeArticle(**data)
    session.add(article)
    await session.flush()
    await session.refresh(article)
    return article


async def get_article_by_id(
    session: AsyncSession, article_id: uuid.UUID
) -> KnowledgeArticle | None:
    result = await session.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    return result.scalar_one_or_none()


async def update_article(
    session: AsyncSession,
    article_id: uuid.UUID,
    data: dict[str, Any],
) -> KnowledgeArticle | None:
    """Update article fields and re-embed (caller sets embedding in data)."""
    article = await get_article_by_id(session, article_id)
    if article is None:
        return None
    for key, value in data.items():
        setattr(article, key, value)
    await session.flush()
    await session.refresh(article)
    return article


async def list_articles(
    session: AsyncSession,
    category: TicketCategory | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[KnowledgeArticle]:
    query = select(KnowledgeArticle)
    if category:
        query = query.where(KnowledgeArticle.category == category)
    offset = (page - 1) * page_size
    result = await session.execute(
        query.order_by(KnowledgeArticle.updated_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all())


async def find_similar_articles(
    session: AsyncSession,
    embedding: list[float],
    top_k: int = 5,
    category: TicketCategory | None = None,
) -> list[KnowledgeArticle]:
    """
    Return the top-k most similar articles using cosine distance (pgvector).
    Optionally filtered by category to narrow RAG context.
    """
    # pgvector cosine distance operator: <=>
    query = (
        select(KnowledgeArticle)
        .where(KnowledgeArticle.embedding.is_not(None))
        .order_by(KnowledgeArticle.embedding.op("<=>")(embedding))
        .limit(top_k)
    )
    if category:
        query = query.where(KnowledgeArticle.category == category)

    result = await session.execute(query)
    return list(result.scalars().all())
