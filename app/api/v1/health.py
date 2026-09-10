"""Health check endpoint — for uptime monitoring (SRS §5)."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.llm.client import get_client
from app.schemas.common import ResponseEnvelope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=ResponseEnvelope, summary="Health check")
async def health_check(
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope:
    """
    Returns 200 with connectivity status for DB and LLM provider.
    Does NOT require API key — used by load balancers and uptime monitors.
    """
    # DB check
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning("Health check: DB unreachable", extra={"error": str(exc)})

    # LLM check (lightweight — just verify client initializes)
    llm_ok = False
    try:
        get_client()
        llm_ok = True
    except Exception as exc:
        logger.warning("Health check: LLM client not initialised", extra={"error": str(exc)})

    return ResponseEnvelope.success({
        "status": "healthy" if (db_ok and llm_ok) else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "llm_provider": "ok" if llm_ok else "unavailable",
    })

