"""ResolutionSuggestion ORM model — SRS §4.4."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class ResolutionSuggestion(Base):
    """LLM-generated resolution suggestion for a ticket."""

    __tablename__ = "resolution_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggested_text: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON works in both PostgreSQL and SQLite (test DB).
    # Stored as a list of UUID strings, e.g. ["uuid1", "uuid2"]
    source_article_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="UUIDs of knowledge articles used to generate this suggestion",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Relationship
    ticket: Mapped["Ticket"] = relationship(  # noqa: F821
        "Ticket", back_populates="resolution_suggestions"
    )
