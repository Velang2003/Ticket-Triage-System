"""
Integration test — full ticket lifecycle (SRS §8.2, §8.3).

Flow:
1. Create ticket → 201
2. Assert classification stored with correct values
3. Assert suggestion stored
4. Fetch enriched ticket → classification and suggestion present
5. Update status Open → In Progress → 200
6. Attempt invalid transition → 409
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid


@pytest.mark.asyncio
async def test_full_ticket_lifecycle(
    client,
    auth_headers,
    sample_ticket_payload,
    mock_llm_classify,
    mock_embedding,
    mock_llm_suggest,
):
    """End-to-end: create → classify → suggest → fetch → update status."""
    # ── Step 1: Create ticket ─────────────────────────────────
    fake_article = MagicMock()
    fake_article.id = uuid.uuid4()
    fake_article.title = "Account Help"
    fake_article.content = "Try resetting your password."

    with patch(
        "app.services.rag_service.knowledge_article_repo.find_similar_articles",
        return_value=[fake_article],
    ):
        create_resp = await client.post(
            "/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers
        )

    assert create_resp.status_code == 201
    ticket_id = create_resp.json()["data"]["id"]

    # ── Step 2: Classification present ───────────────────────
    classification = create_resp.json()["data"]["classification"]
    assert classification is not None
    assert classification["predicted_category"] == "Technical"
    assert classification["predicted_priority"] == "High"
    assert classification["is_pending"] is False

    # ── Step 3: Suggestion present ────────────────────────────
    suggestion = create_resp.json()["data"]["suggestion"]
    assert suggestion is not None
    assert len(suggestion["suggested_text"]) > 0

    # ── Step 4: Fetch enriched ticket ─────────────────────────
    get_resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["id"] == ticket_id
    assert data["classification"]["predicted_category"] == "Technical"
    assert data["suggestion"] is not None

    # ── Step 5: Valid status update (Open → In Progress) ──────
    patch_resp = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "In Progress"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "In Progress"

    # ── Step 6: Invalid transition (In Progress → Open is OK, Resolved → Open is OK)
    #    Let's try Resolved directly from In Progress → valid
    resolve_resp = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "Resolved"},
        headers=auth_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["data"]["status"] == "Resolved"

    # ── Step 7: Invalid — Resolved → In Progress is NOT allowed ──
    invalid_resp = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "In Progress"},
        headers=auth_headers,
    )
    assert invalid_resp.status_code == 409


@pytest.mark.asyncio
async def test_ticket_appears_in_list(
    client,
    auth_headers,
    sample_ticket_payload,
    mock_llm_classify,
    mock_embedding,
    mock_llm_suggest,
):
    """Created ticket appears in the paginated list."""
    with patch("app.services.rag_service.knowledge_article_repo.find_similar_articles", return_value=[]):
        create_resp = await client.post(
            "/api/v1/tickets", json=sample_ticket_payload, headers=auth_headers
        )
    ticket_id = create_resp.json()["data"]["id"]

    list_resp = await client.get("/api/v1/tickets", headers=auth_headers)
    assert list_resp.status_code == 200
    ids = [t["id"] for t in list_resp.json()["data"]["items"]]
    assert ticket_id in ids
