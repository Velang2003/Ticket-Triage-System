"""Knowledge article API routes — 3 endpoints (SRS §5)."""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.db.session import get_db_session
from app.models.ticket import TicketCategory
from app.schemas.common import ResponseEnvelope
from app.schemas.knowledge_article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.services import knowledge_article_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-articles", tags=["Knowledge Articles"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseEnvelope,
    summary="Add a knowledge-base article",
)
async def add_article(
    body: ArticleCreate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """
    Add a new knowledge-base article.
    Automatically generates an embedding and indexes it for RAG retrieval.
    """
    category = TicketCategory(body.category) if body.category else None
    article = await knowledge_article_service.add_article(
        session, title=body.title, content=body.content, category=category
    )
    return ResponseEnvelope.success(article)


@router.put(
    "/{article_id}",
    response_model=ResponseEnvelope,
    summary="Update a knowledge-base article",
)
async def update_article(
    article_id: uuid.UUID,
    body: ArticleUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Update an article. Triggers re-embedding and re-indexing."""
    category = TicketCategory(body.category) if body.category else None
    article = await knowledge_article_service.update_article(
        session,
        article_id=article_id,
        title=body.title,
        content=body.content,
        category=category,
    )
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )
    return ResponseEnvelope.success(article)


@router.get(
    "",
    response_model=ResponseEnvelope,
    summary="List knowledge-base articles",
)
async def list_articles(
    category: TicketCategory | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """List knowledge-base articles, optionally filtered by category."""
    articles = await knowledge_article_service.list_articles(
        session, category=category, page=page, page_size=page_size
    )
    return ResponseEnvelope.success({"items": articles, "page": page, "page_size": page_size})

