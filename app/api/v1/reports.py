"""Reporting endpoint — SRS FR-10."""
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.db.session import get_db_session
from app.schemas.common import ResponseEnvelope
from app.schemas.report import ReportSummaryResponse
from app.services.ticket_service import get_reporting_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/summary",
    response_model=ResponseEnvelope,
    summary="Ticket volume summary report",
)
async def summary_report(
    from_date: str | None = Query(None, description="ISO 8601 date e.g. 2026-01-01"),
    to_date: str | None = Query(None, description="ISO 8601 date e.g. 2026-12-31"),
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """
    Return ticket volume grouped by category, priority, and status.
    Optionally filter by date range (from_date, to_date — ISO 8601).
    """
    summary = await get_reporting_summary(session, from_date=from_date, to_date=to_date)
    return ResponseEnvelope.success(summary)

