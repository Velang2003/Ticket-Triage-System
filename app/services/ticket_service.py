"""Ticket service — orchestrates the full ticket lifecycle."""
import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditEventType
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.models.classification import Classification
from app.models.resolution_suggestion import ResolutionSuggestion
from app.repositories import audit_log_repo, classification_repo, resolution_suggestion_repo, ticket_repo
from app.services import classification_service, rag_service

logger = logging.getLogger(__name__)


async def create_ticket(
    session: AsyncSession,
    subject: str,
    description: str,
    submitter_email: str,
) -> dict[str, Any]:
    """
    Persist a new ticket, then run classification + suggestion in-process.
    Returns the created ticket enriched with classification and suggestion.
    NFR-2: If LLM fails, ticket is saved with pending classification.
    """
    ticket = await ticket_repo.create_ticket(
        session,
        {"subject": subject, "description": description, "submitter_email": submitter_email},
    )
    await audit_log_repo.create_entry(
        session, ticket.id, AuditEventType.TICKET_CREATED,
        {"subject": subject},
    )
    logger.info("Ticket created", extra={"ticket_id": str(ticket.id)})

    # Run classification (never raises)
    await classification_service.classify_ticket(
        session=session,
        ticket_id=ticket.id,
        subject=subject,
        description=description,
    )

    # Reload to get updated category/priority after classification
    await session.refresh(ticket)

    # Run RAG suggestion using predicted category (never raises)
    await rag_service.generate_suggestion(
        session=session,
        ticket_id=ticket.id,
        subject=subject,
        description=description,
        category=ticket.category,
    )

    return await _enrich_ticket(session, ticket)


async def get_ticket(session: AsyncSession, ticket_id: uuid.UUID) -> dict[str, Any] | None:
    """Fetch a ticket with its latest classification and suggestion."""
    ticket = await ticket_repo.get_ticket_by_id(session, ticket_id)
    if ticket is None:
        return None
    return await _enrich_ticket(session, ticket)


async def list_tickets(
    session: AsyncSession,
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    priority: TicketPriority | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Return paginated ticket list with metadata."""
    tickets, total = await ticket_repo.list_tickets(
        session, status=status, category=category, priority=priority,
        page=page, page_size=page_size,
    )
    return {
        "items": [_ticket_to_dict(t) for t in tickets],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    new_status: TicketStatus,
    old_status: TicketStatus | None = None,
) -> dict[str, Any]:
    """Update status, write audit entry. Raises LookupError or ValueError on bad input."""
    ticket = await ticket_repo.update_ticket_status(session, ticket_id, new_status)
    await audit_log_repo.create_entry(
        session, ticket_id, AuditEventType.STATUS_CHANGED,
        {"from": old_status.value if old_status else None, "to": new_status.value},
    )
    return _ticket_to_dict(ticket)


async def retrigger_classification(
    session: AsyncSession,
    ticket_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Manually re-run classification for a ticket."""
    ticket = await ticket_repo.get_ticket_by_id(session, ticket_id)
    if ticket is None:
        return None
    await classification_service.classify_ticket(
        session, ticket.id, ticket.subject, ticket.description
    )
    await session.refresh(ticket)
    return await _enrich_ticket(session, ticket)


async def get_reporting_summary(
    session: AsyncSession,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """
    Return ticket volume grouped by category, priority, and status.
    Uses raw SQL aggregation for efficiency.
    """
    from sqlalchemy import func, select, and_
    from app.models.ticket import Ticket
    from datetime import datetime

    base = select(
        Ticket.category, Ticket.priority, Ticket.status, func.count().label("count")
    )
    conditions = []
    if from_date:
        conditions.append(Ticket.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        conditions.append(Ticket.created_at <= datetime.fromisoformat(to_date))
    if conditions:
        base = base.where(and_(*conditions))
    base = base.group_by(Ticket.category, Ticket.priority, Ticket.status)

    result = await session.execute(base)
    rows = result.all()

    # Aggregate into nested dict
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total = 0

    for row in rows:
        cat = row.category.value if row.category else "Unclassified"
        pri = row.priority.value if row.priority else "Unclassified"
        sta = row.status.value
        count = row.count
        by_category[cat] = by_category.get(cat, 0) + count
        by_priority[pri] = by_priority.get(pri, 0) + count
        by_status[sta] = by_status.get(sta, 0) + count
        total += count

    return {
        "total": total,
        "by_category": by_category,
        "by_priority": by_priority,
        "by_status": by_status,
        "from_date": from_date,
        "to_date": to_date,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _enrich_ticket(session: AsyncSession, ticket: Any) -> dict[str, Any]:
    """Add latest classification and suggestion to ticket dict."""
    classification = await classification_repo.get_latest_classification(session, ticket.id)
    suggestion = await resolution_suggestion_repo.get_latest_suggestion(session, ticket.id)
    d = _ticket_to_dict(ticket)
    d["classification"] = _classification_to_dict(classification)
    d["suggestion"] = _suggestion_to_dict(suggestion)
    return d


def _ticket_to_dict(ticket: Any) -> dict[str, Any]:
    return {
        "id": str(ticket.id),
        "subject": ticket.subject,
        "description": ticket.description,
        "submitter_email": ticket.submitter_email,
        "category": ticket.category.value if ticket.category else None,
        "priority": ticket.priority.value if ticket.priority else None,
        "status": ticket.status.value,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }


def _classification_to_dict(c: Classification | None) -> dict[str, Any] | None:
    if c is None:
        return None
    return {
        "id": str(c.id),
        "predicted_category": c.predicted_category.value if c.predicted_category else None,
        "predicted_priority": c.predicted_priority.value if c.predicted_priority else None,
        "confidence_note": c.confidence_note,
        "is_pending": c.is_pending,
        "created_at": c.created_at.isoformat(),
    }


def _suggestion_to_dict(s: ResolutionSuggestion | None) -> dict[str, Any] | None:
    if s is None:
        return None
    return {
        "id": str(s.id),
        "suggested_text": s.suggested_text,
        "source_article_ids": s.source_article_ids,
        "created_at": s.created_at.isoformat(),
    }
