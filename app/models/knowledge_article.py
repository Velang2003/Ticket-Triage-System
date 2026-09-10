"""KnowledgeArticle ORM model — SRS §4.3."""

import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow
from app.models.ticket import TicketCategory

# Gemini text-embedding-004 outputs 768-dimensional vectors
EMBEDDING_DIM = 768


class FlexibleVector(TypeDecorator):
    """
    Dialect-flexible vector column:
    - PostgreSQL: delegates to pgvector's Vector(dim) for native HNSW/cosine ops.
    - SQLite (test DB): stores as a JSON text string; cosine queries are always
      mocked in tests so this code path is never executed.
    """

    impl = Text
    cache_ok = True

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if dialect.name == "postgresql":
            return value
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    @property
    def python_type(self):
        return list


class KnowledgeArticle(Base):
    """Knowledge-base article used for RAG retrieval."""

    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        FlexibleVector(EMBEDDING_DIM), nullable=True
    )
    category: Mapped[TicketCategory | None] = mapped_column(
        Enum(
            TicketCategory,
            name="ticket_category",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
