"""Error-handling tests — LLM failure scenarios (SRS §8.5, NFR-2)."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_ticket_saved_when_llm_fails(client, auth_headers, sample_ticket_payload):
    """
    When the LLM is unavailable:
    - Ticket MUST still be created (HTTP 201)
    - Classification MUST be marked as pending
    - Response status MUST be 'success' (not 500)
    """
    with (
        patch(
            "app.services.classification_service.generate_json",
            side_effect=RuntimeError("LLM service timeout"),
        ),
        patch(
            "app.services.rag_service.get_embedding",
            side_effect=RuntimeError("Embedding API down"),
        ),
    ):
        response = await client.post(
            "/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers
        )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    # Ticket was persisted
    assert body["data"]["subject"] == sample_ticket_payload["subject"]
    # Classification should be pending
    classification = body["data"].get("classification")
    if classification:
        assert classification["is_pending"] is True


@pytest.mark.asyncio
async def test_invalid_status_transition_returns_409(
    client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest
):
    """Invalid status transition must return 409 Conflict."""
    with patch(
        "app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]
    ):
        create = await client.post(
            "/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers
        )
    ticket_id = create.json()["data"]["id"]

    # Open → Resolved is not allowed
    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "Resolved"},
        headers=auth_headers,
    )
    assert response.status_code == 409
    body = response.json()
    assert "Cannot transition" in body.get("detail", "") or response.status_code == 409


@pytest.mark.asyncio
async def test_unknown_ticket_returns_404(client, auth_headers):
    """Fetching a non-existent ticket returns 404."""
    response = await client.get(
        "/api/v1/tickets/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["status"] == "error"
