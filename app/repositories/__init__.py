"""Repositories package."""
from app.repositories import (
    ticket_repo,
    classification_repo,
    knowledge_article_repo,
    resolution_suggestion_repo,
    audit_log_repo,
)

__all__ = [
    "ticket_repo",
    "classification_repo",
    "knowledge_article_repo",
    "resolution_suggestion_repo",
    "audit_log_repo",
]

