"""Functional tests for tickets API (all 6 endpoints)."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_create_ticket_success(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """POST /tickets returns 201 with ticket data."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        response = await client.post(
            "/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers
        )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["subject"] == sample_ticket_payload["subject"]
    assert body["data"]["status"] == "Open"
    assert "id" in body["data"]


@pytest.mark.asyncio
async def test_create_ticket_no_auth(client, sample_ticket_payload):
    """POST /tickets without API key returns 401."""
    response = await client.post("/api/v1/tickets", json=sample_ticket_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_ticket_success(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """GET /tickets/{id} returns the ticket."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        create = await client.post("/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers)
    ticket_id = create.json()["data"]["id"]

    response = await client.get(f"/api/v1/tickets/{ticket_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == ticket_id


@pytest.mark.asyncio
async def test_get_ticket_not_found(client, auth_headers):
    """GET /tickets/{id} with unknown UUID returns 404."""
    response = await client.get(
        "/api/v1/tickets/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_tickets(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """GET /tickets returns paginated list."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        await client.post("/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers)

    response = await client.get("/api/v1/tickets", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] >= 1
    assert isinstance(body["data"]["items"], list)


@pytest.mark.asyncio
async def test_update_ticket_status_valid(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """PATCH /tickets/{id}/status with valid transition returns 200."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        create = await client.post("/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers)
    ticket_id = create.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "In Progress"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "In Progress"


@pytest.mark.asyncio
async def test_update_ticket_status_invalid_transition(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """PATCH status with invalid transition returns 409."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        create = await client.post("/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers)
    ticket_id = create.json()["data"]["id"]

    # Open → Resolved is not a valid transition
    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "Resolved"},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_retrigger_classify(client, auth_headers, sample_ticket_payload, mock_llm_classify, mock_embedding, mock_llm_suggest):
    """POST /tickets/{id}/classify returns 200 with updated ticket."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        create = await client.post("/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers)
    ticket_id = create.json()["data"]["id"]

    response = await client.post(f"/api/v1/tickets/{ticket_id}/classify", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == ticket_id

