"""Ticket API routes — all 6 ticket endpoints (SRS §5)."""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.schemas.common import ResponseEnvelope
from app.schemas.ticket import TicketCreate, TicketListResponse, TicketResponse, StatusUpdate
from app.services import ticket_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseEnvelope,
    summary="Create a new ticket",
)
async def create_ticket(
    body: TicketCreate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """
    Submit a new support ticket.
    Triggers automatic classification and suggestion generation synchronously.
    If the LLM is unavailable the ticket is still saved with a pending classification (HTTP 201).
    """
    ticket = await ticket_service.create_ticket(
        session=session,
        subject=body.subject,
        description=body.description,
        submitter_email=str(body.submitter_email),
    )
    return ResponseEnvelope.success(ticket)


@router.get(
    "/{ticket_id}",
    response_model=ResponseEnvelope,
    summary="Fetch a single ticket",
)
async def get_ticket(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Return a ticket with its latest classification and suggestion."""
    ticket = await ticket_service.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return ResponseEnvelope.success(ticket)


@router.get(
    "",
    response_model=ResponseEnvelope,
    summary="List tickets with filters",
)
async def list_tickets(
    ticket_status: TicketStatus | None = Query(None, alias="status"),
    category: TicketCategory | None = Query(None),
    priority: TicketPriority | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(None),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Return a paginated, filterable list of tickets."""
    ps = page_size or settings.default_page_size
    ps = min(ps, settings.max_page_size)
    result = await ticket_service.list_tickets(
        session,
        status=ticket_status,
        category=category,
        priority=priority,
        page=page,
        page_size=ps,
    )
    return ResponseEnvelope.success(result)


@router.patch(
    "/{ticket_id}/status",
    response_model=ResponseEnvelope,
    summary="Update ticket status",
)
async def update_status(
    ticket_id: uuid.UUID,
    body: StatusUpdate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """
    Update a ticket's status. Returns 409 on invalid transitions.
    Valid transitions:
    - Open → In Progress, Closed
    - In Progress → Resolved, Open, Closed
    - Resolved → Closed, Open
    - Closed → Open
    """
    try:
        new_status = TicketStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value")

    try:
        ticket = await ticket_service.update_ticket_status(session, ticket_id, new_status)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket {ticket_id} not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ResponseEnvelope.success(ticket)


@router.post(
    "/{ticket_id}/classify",
    response_model=ResponseEnvelope,
    summary="Manually re-trigger classification",
)
async def retrigger_classify(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Re-run classification for a ticket (useful when it was marked pending)."""
    ticket = await ticket_service.retrigger_classification(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket {ticket_id} not found")
    return ResponseEnvelope.success(ticket)


@router.get(
    "/{ticket_id}/suggestion",
    response_model=ResponseEnvelope,
    summary="Get the latest resolution suggestion",
)
async def get_suggestion(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Fetch the latest LLM-generated resolution suggestion for a ticket."""
    from app.repositories import resolution_suggestion_repo
    # First verify ticket exists
    ticket = await ticket_service.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket {ticket_id} not found")
    suggestion = ticket.get("suggestion")
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No suggestion found for this ticket")
    return ResponseEnvelope.success(suggestion)
