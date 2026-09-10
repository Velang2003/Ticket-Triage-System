"""Classification service — implements SRS §8.2 logic.

Steps:
1. Build classification prompt from ticket text.
2. Call LLM; parse JSON response.
3. Validate returned category/priority against allowed enums.
4. On parse failure → retry with stricter prompt.
5. On repeated failure → mark classification as pending (NFR-2).
6. Persist Classification record + AuditLog entry.
7. Denormalise category/priority back onto the Ticket row.
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import prompts
from app.llm.client import generate_json
from app.models.audit_log import AuditEventType
from app.models.ticket import TicketCategory, TicketPriority
from app.repositories import audit_log_repo, classification_repo, ticket_repo

logger = logging.getLogger(__name__)

_VALID_CATEGORIES = {c.value for c in TicketCategory}
_VALID_PRIORITIES = {p.value for p in TicketPriority}


async def classify_ticket(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    subject: str,
    description: str,
) -> None:
    """
    Classify ticket and persist the result.
    Never raises — on total failure, marks classification as pending.
    """
    prompt = prompts.CLASSIFICATION_PROMPT_TEMPLATE.format(
        subject=subject, description=description
    )
    retry_prompt = prompts.CLASSIFICATION_RETRY_PROMPT_TEMPLATE.format(
        subject=subject, description=description
    )

    parsed: dict | None = None
    try:
        parsed = await generate_json(prompt, retry_prompt=retry_prompt)
    except Exception as exc:
        logger.error(
            "Classification LLM call failed — marking pending",
            extra={"ticket_id": str(ticket_id), "error": str(exc)},
        )

    if parsed is not None:
        raw_category = parsed.get("category", "")
        raw_priority = parsed.get("priority", "")
        rationale = parsed.get("rationale", "")

        if raw_category not in _VALID_CATEGORIES or raw_priority not in _VALID_PRIORITIES:
            logger.warning(
                "LLM returned invalid enum values — marking pending",
                extra={
                    "ticket_id": str(ticket_id),
                    "raw_category": raw_category,
                    "raw_priority": raw_priority,
                },
            )
            await _save_pending(session, ticket_id, rationale)
            return

        category = TicketCategory(raw_category)
        priority = TicketPriority(raw_priority)

        await classification_repo.create_classification(
            session=session,
            ticket_id=ticket_id,
            predicted_category=category,
            predicted_priority=priority,
            confidence_note=rationale,
            is_pending=False,
        )
        # Denormalise onto ticket for fast filter queries
        await ticket_repo.update_ticket_classification(session, ticket_id, category, priority)
        await audit_log_repo.create_entry(
            session=session,
            ticket_id=ticket_id,
            event_type=AuditEventType.CLASSIFIED,
            details={"category": raw_category, "priority": raw_priority},
        )
        logger.info(
            "Ticket classified",
            extra={"ticket_id": str(ticket_id), "category": raw_category, "priority": raw_priority},
        )
    else:
        await _save_pending(session, ticket_id, "")


async def _save_pending(
    session: AsyncSession, ticket_id: uuid.UUID, note: str
) -> None:
    """Persist a pending classification and audit the failure."""
    await classification_repo.create_classification(
        session=session,
        ticket_id=ticket_id,
        predicted_category=None,
        predicted_priority=None,
        confidence_note=note or "LLM unavailable — classification pending",
        is_pending=True,
    )
    await audit_log_repo.create_entry(
        session=session,
        ticket_id=ticket_id,
        event_type=AuditEventType.CLASSIFICATION_PENDING,
        details={"reason": "LLM call failed or returned invalid response"},
    )

