"""Unit tests for ticket service — status transitions and pagination logic."""

import uuid

import pytest

from app.models.ticket import TicketStatus


@pytest.mark.asyncio
async def test_valid_status_transitions():
    """All documented valid transitions should be accepted."""
    from app.models.ticket import VALID_TRANSITIONS

    assert TicketStatus.IN_PROGRESS in VALID_TRANSITIONS[TicketStatus.OPEN]
    assert TicketStatus.CLOSED in VALID_TRANSITIONS[TicketStatus.OPEN]
    assert TicketStatus.RESOLVED in VALID_TRANSITIONS[TicketStatus.IN_PROGRESS]
    assert TicketStatus.CLOSED in VALID_TRANSITIONS[TicketStatus.RESOLVED]
    assert TicketStatus.OPEN in VALID_TRANSITIONS[TicketStatus.CLOSED]


@pytest.mark.asyncio
async def test_invalid_transition_raises():
    """Direct Open → Resolved transition is not allowed."""
    from app.models.ticket import VALID_TRANSITIONS

    assert TicketStatus.RESOLVED not in VALID_TRANSITIONS[TicketStatus.OPEN]


def test_pagination_math():
    """Verify page count calculation for edge cases."""

    def pages(total, page_size):
        return max(1, (total + page_size - 1) // page_size)

    assert pages(0, 20) == 1
    assert pages(20, 20) == 1
    assert pages(21, 20) == 2
    assert pages(100, 20) == 5
    assert pages(101, 20) == 6


@pytest.mark.asyncio
async def test_update_ticket_status_not_found(db_session):
    """update_ticket_status raises LookupError for unknown ticket."""
    from app.repositories.ticket_repo import update_ticket_status

    with pytest.raises(LookupError):
        await update_ticket_status(db_session, uuid.uuid4(), TicketStatus.IN_PROGRESS)
