"""Ticket ORM model — SRS §4.1."""

import enum
import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TicketCategory(enum.StrEnum):
    BILLING = "Billing"
    TECHNICAL = "Technical"
    ACCOUNT = "Account"
    OTHER = "Other"


class TicketPriority(enum.StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketStatus(enum.StrEnum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


# Valid status transitions (from → set of allowed tos)
VALID_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED, TicketStatus.OPEN, TicketStatus.CLOSED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.OPEN},
    TicketStatus.CLOSED: {TicketStatus.OPEN},
}


class Ticket(TimestampMixin, Base):
    """Support ticket entity."""

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    submitter_email: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[TicketCategory | None] = mapped_column(
        Enum(
            TicketCategory,
            name="ticket_category",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    priority: Mapped[TicketPriority | None] = mapped_column(
        Enum(
            TicketPriority,
            name="ticket_priority",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus, name="ticket_status", values_callable=lambda obj: [e.value for e in obj]
        ),
        default=TicketStatus.OPEN,
        nullable=False,
    )

    # Relationships
    classifications: Mapped[list["Classification"]] = relationship(  # noqa: F821
        "Classification", back_populates="ticket", cascade="all, delete-orphan"
    )
    resolution_suggestions: Mapped[list["ResolutionSuggestion"]] = relationship(  # noqa: F821
        "ResolutionSuggestion", back_populates="ticket", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="ticket", cascade="all, delete-orphan"
    )
