"""RAG / Suggestion service — implements SRS §8.3 logic.

Steps:
1. Generate embedding for ticket subject + description.
2. Query pgvector for top-k similar articles, filtered by predicted category.
3. Build suggestion prompt with ticket text + article excerpts.
4. Call LLM to generate suggested resolution.
5. Persist ResolutionSuggestion + AuditLog entry.
"""
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm import prompts
from app.llm.client import generate_text
from app.llm.embedding import get_embedding
from app.models.audit_log import AuditEventType
from app.models.ticket import TicketCategory
from app.repositories import audit_log_repo, knowledge_article_repo, resolution_suggestion_repo

logger = logging.getLogger(__name__)
settings = get_settings()


async def generate_suggestion(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    subject: str,
    description: str,
    category: TicketCategory | None = None,
) -> None:
    """
    Generate and persist a resolution suggestion for a ticket.
    Never raises — logs errors and returns silently on failure.
    """
    try:
        ticket_text = f"{subject}\n\n{description}"
        embedding = await get_embedding(ticket_text)

        articles = await knowledge_article_repo.find_similar_articles(
            session=session,
            embedding=embedding,
            top_k=settings.rag_top_k,
            category=category,
        )

        if not articles:
            logger.info(
                "No relevant articles found for ticket — skipping suggestion",
                extra={"ticket_id": str(ticket_id)},
            )
            return

        articles_text = _format_articles(articles)
        prompt = prompts.SUGGESTION_PROMPT_TEMPLATE.format(
            subject=subject,
            description=description,
            articles=articles_text,
        )

        suggested_text = await generate_text(prompt, temperature=0.3)

        source_ids = [str(a.id) for a in articles]
        await resolution_suggestion_repo.create_suggestion(
            session=session,
            ticket_id=ticket_id,
            suggested_text=suggested_text,
            source_article_ids=source_ids,
        )
        await audit_log_repo.create_entry(
            session=session,
            ticket_id=ticket_id,
            event_type=AuditEventType.SUGGESTION_GENERATED,
            details={"source_article_ids": source_ids, "article_count": len(articles)},
        )
        logger.info(
            "Suggestion generated",
            extra={"ticket_id": str(ticket_id), "article_count": len(articles)},
        )

    except Exception as exc:
        logger.error(
            "Suggestion generation failed",
            extra={"ticket_id": str(ticket_id), "error": str(exc)},
        )


def _format_articles(articles: list) -> str:
    """Format knowledge articles into a numbered list for the prompt."""
    parts = []
    for i, article in enumerate(articles, start=1):
        parts.append(f"[Article {i}] {article.title}\n{article.content[:1000]}")
    return "\n\n".join(parts)

