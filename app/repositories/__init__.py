"""Repositories package."""

from app.repositories import (
    audit_log_repo,
    classification_repo,
    knowledge_article_repo,
    resolution_suggestion_repo,
    ticket_repo,
)

__all__ = [
    "ticket_repo",
    "classification_repo",
    "knowledge_article_repo",
    "resolution_suggestion_repo",
    "audit_log_repo",
]
