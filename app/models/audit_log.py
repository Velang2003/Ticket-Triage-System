"""AuditLog ORM model — SRS §4.5."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class AuditEventType(str):
    """Audit event type constants."""

    TICKET_CREATED = "ticket_created"
    CLASSIFIED = "classified"
    CLASSIFICATION_PENDING = "classification_pending"
    SUGGESTION_GENERATED = "suggestion_generated"
    STATUS_CHANGED = "status_changed"
    ARTICLE_ADDED = "article_added"
    ARTICLE_UPDATED = "article_updated"


class AuditLog(Base):
    """Immutable audit trail of all ticket lifecycle events."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationship
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="audit_logs")  # noqa: F821
