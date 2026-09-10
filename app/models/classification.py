"""Classification ORM model — SRS §4.2."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.ticket import TicketCategory, TicketPriority


class Classification(Base):
    """LLM classification result for a ticket."""

    __tablename__ = "classifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predicted_category: Mapped[TicketCategory | None] = mapped_column(
        sa.Enum(
            TicketCategory,
            native_enum=False,
            length=50,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
        comment="Null when classification is pending due to LLM failure",
    )
    predicted_priority: Mapped[TicketPriority | None] = mapped_column(
        sa.Enum(
            TicketPriority,
            native_enum=False,
            length=50,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    confidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_pending: Mapped[bool] = mapped_column(
        default=False,
        comment="True when LLM failed and classification must be retried",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationship
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="classifications")  # noqa: F821
