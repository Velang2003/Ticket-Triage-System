"""Models package — exports all ORM models so Alembic can discover them."""
from app.models.base import Base, TimestampMixin
from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus, VALID_TRANSITIONS
from app.models.classification import Classification
from app.models.knowledge_article import KnowledgeArticle, EMBEDDING_DIM
from app.models.resolution_suggestion import ResolutionSuggestion
from app.models.audit_log import AuditLog, AuditEventType

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
