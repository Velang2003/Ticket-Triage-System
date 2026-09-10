"""Classification repository — create and fetch classification records."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification import Classification
from app.models.ticket import TicketCategory, TicketPriority


async def create_classification(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    predicted_category: TicketCategory | None,
    predicted_priority: TicketPriority | None,
    confidence_note: str | None,
    is_pending: bool = False,
) -> Classification:
    """Persist a classification record."""
    record = Classification(
        ticket_id=ticket_id,
        predicted_category=predicted_category,
        predicted_priority=predicted_priority,
        confidence_note=confidence_note,
        is_pending=is_pending,
    )
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


async def get_latest_classification(
    session: AsyncSession, ticket_id: uuid.UUID
) -> Classification | None:
    """Return the most recently created classification for a ticket."""
    result = await session.execute(
        select(Classification)
        .where(Classification.ticket_id == ticket_id)
        .order_by(Classification.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_pending_classifications(
    session: AsyncSession, limit: int = 100
) -> list[Classification]:
    """Return classifications still awaiting LLM processing (for retry jobs)."""
    result = await session.execute(
        select(Classification)
        .where(Classification.is_pending == True)  # noqa: E712
        .order_by(Classification.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())
