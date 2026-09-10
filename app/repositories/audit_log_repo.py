"""Audit log repository — append-only event trail."""
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def create_entry(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """Append an audit log entry — never updates, only inserts."""
    entry = AuditLog(
        ticket_id=ticket_id,
        event_type=event_type,
        details=details or {},
    )
    session.add(entry)
    await session.flush()
    return entry


async def get_audit_trail(
    session: AsyncSession, ticket_id: uuid.UUID
) -> list[AuditLog]:
    """Return the full ordered audit trail for a ticket."""
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.ticket_id == ticket_id)
        .order_by(AuditLog.created_at.asc())
    )
    return list(result.scalars().all())
