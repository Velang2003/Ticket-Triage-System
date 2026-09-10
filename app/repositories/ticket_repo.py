"""Ticket repository — CRUD + filtered/paginated list."""

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ticket import (
    VALID_TRANSITIONS,
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


async def create_ticket(session: AsyncSession, data: dict[str, Any]) -> Ticket:
    """Persist a new ticket and return it."""
    ticket = Ticket(**data)
    session.add(ticket)
    await session.flush()
    await session.refresh(ticket)
    return ticket


async def get_ticket_by_id(session: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
    """Fetch a ticket with its latest classification and suggestion eagerly loaded."""
    result = await session.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.classifications),
            selectinload(Ticket.resolution_suggestions),
        )
        .where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def list_tickets(
    session: AsyncSession,
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Ticket], int]:
    """Return a filtered, paginated list of tickets and the total count."""
    base_query = select(Ticket)
    count_query = select(func.count()).select_from(Ticket)

    if status:
        base_query = base_query.where(Ticket.status == status)
        count_query = count_query.where(Ticket.status == status)
    if category:
        base_query = base_query.where(Ticket.category == category)
        count_query = count_query.where(Ticket.category == category)
    if priority:
        base_query = base_query.where(Ticket.priority == priority)
        count_query = count_query.where(Ticket.priority == priority)

    total = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    tickets = (
        (
            await session.execute(
                base_query.order_by(Ticket.created_at.desc()).offset(offset).limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    return list(tickets), total


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    new_status: TicketStatus,
) -> Ticket:
    """
    Update ticket status, enforcing valid transitions.
    Raises ValueError on invalid transitions (mapped to 409 by the route).
    """
    ticket = await get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise LookupError(f"Ticket {ticket_id} not found")

    allowed = VALID_TRANSITIONS.get(ticket.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{ticket.status}' to '{new_status}'. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    ticket.status = new_status
    await session.flush()
    await session.refresh(ticket)
    return ticket


async def update_ticket_classification(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    category: TicketCategory,
    priority: TicketPriority,
) -> None:
    """Denormalise category/priority back onto the ticket row for fast filtering."""
    await session.execute(
        update(Ticket).where(Ticket.id == ticket_id).values(category=category, priority=priority)
    )
