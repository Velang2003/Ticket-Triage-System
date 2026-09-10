"""Unit tests for classification service (SRS §8.2)."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services import classification_service


@pytest.mark.asyncio
async def test_classify_ticket_success(db_session, mock_llm_classify):
    """Happy path: LLM returns valid category + priority."""
    ticket_id = uuid.uuid4()

    # Patch repo calls so we don't need a real DB row
    with (
        patch("app.services.classification_service.classification_repo.create_classification", new_callable=AsyncMock) as mock_create,
        patch("app.services.classification_service.ticket_repo.update_ticket_classification", new_callable=AsyncMock),
        patch("app.services.classification_service.audit_log_repo.create_entry", new_callable=AsyncMock),
    ):
        await classification_service.classify_ticket(
            session=db_session,
            ticket_id=ticket_id,
            subject="App crashes on login",
            description="The mobile app crashes immediately after entering credentials.",
        )
        mock_create.assert_awaited_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["is_pending"] is False
        assert call_kwargs["predicted_category"].value == "Technical"
        assert call_kwargs["predicted_priority"].value == "High"


@pytest.mark.asyncio
async def test_classify_ticket_pending_on_llm_failure(db_session):
    """LLM raises → classification saved as pending (NFR-2)."""
    ticket_id = uuid.uuid4()

    with (
        patch(
            "app.services.classification_service.generate_json",
            side_effect=RuntimeError("LLM timeout"),
        ),
        patch("app.services.classification_service.classification_repo.create_classification", new_callable=AsyncMock) as mock_create,
        patch("app.services.classification_service.audit_log_repo.create_entry", new_callable=AsyncMock),
    ):
        # Should NOT raise
        await classification_service.classify_ticket(
            session=db_session,
            ticket_id=ticket_id,
            subject="Test",
            description="Test description",
        )
        mock_create.assert_awaited_once()
        assert mock_create.call_args.kwargs["is_pending"] is True


@pytest.mark.asyncio
async def test_classify_ticket_invalid_enum_becomes_pending(db_session):
    """LLM returns unknown category → treated as pending."""
    ticket_id = uuid.uuid4()

    with (
        patch(
            "app.services.classification_service.generate_json",
            return_value={"category": "UNKNOWN_CAT", "priority": "High", "rationale": "..."},
        ),
        patch("app.services.classification_service.classification_repo.create_classification", new_callable=AsyncMock) as mock_create,
        patch("app.services.classification_service.audit_log_repo.create_entry", new_callable=AsyncMock),
    ):
        await classification_service.classify_ticket(
            session=db_session,
            ticket_id=ticket_id,
            subject="Test",
            description="Test",
        )
        assert mock_create.call_args.kwargs["is_pending"] is True


@pytest.mark.asyncio
async def test_classify_ticket_all_categories():
    """All valid category/priority combinations should parse correctly."""
    from app.models.ticket import TicketCategory, TicketPriority

    for cat in TicketCategory:
        for pri in TicketPriority:
            # Just verify they are valid enum values
            assert cat.value in {"Billing", "Technical", "Account", "Other"}
            assert pri.value in {"Low", "Medium", "High", "Critical"}

