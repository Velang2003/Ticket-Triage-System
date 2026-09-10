"""Resolution suggestion repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resolution_suggestion import ResolutionSuggestion


async def create_suggestion(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    suggested_text: str,
    source_article_ids: list[str],
) -> ResolutionSuggestion:
    """Persist a resolution suggestion."""
    record = ResolutionSuggestion(
        ticket_id=ticket_id,
        suggested_text=suggested_text,
        source_article_ids=source_article_ids,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


async def get_latest_suggestion(
    session: AsyncSession, ticket_id: uuid.UUID
) -> ResolutionSuggestion | None:
    """Return the most recently created suggestion for a ticket."""
    result = await session.execute(
        select(ResolutionSuggestion)
        .where(ResolutionSuggestion.ticket_id == ticket_id)
        .order_by(ResolutionSuggestion.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
