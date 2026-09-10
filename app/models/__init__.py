"""Models package — exports all ORM models so Alembic can discover them."""

from app.models.audit_log import AuditEventType, AuditLog
from app.models.base import Base, TimestampMixin
from app.models.classification import Classification
from app.models.knowledge_article import EMBEDDING_DIM, KnowledgeArticle
from app.models.resolution_suggestion import ResolutionSuggestion
from app.models.ticket import (
    VALID_TRANSITIONS,
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "Ticket",
    "TicketCategory",
    "TicketPriority",
    "TicketStatus",
    "VALID_TRANSITIONS",
    "Classification",
    "KnowledgeArticle",
    "EMBEDDING_DIM",
    "ResolutionSuggestion",
    "AuditLog",
    "AuditEventType",
]
