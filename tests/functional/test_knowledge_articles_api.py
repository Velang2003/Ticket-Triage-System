"""Functional tests for knowledge articles API."""

import pytest


@pytest.mark.asyncio
async def test_add_article(client, auth_headers, mock_embedding_article):
    """POST /knowledge-articles returns 201."""
    response = await client.post(
        "/api/v1/knowledge-articles",
        json={
            "title": "Password Reset Guide",
            "content": "Step 1: Go to login...",
            "category": "Account",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["title"] == "Password Reset Guide"
    assert body["data"]["category"] == "Account"


@pytest.mark.asyncio
async def test_add_article_no_auth(client):
    """POST /knowledge-articles without API key returns 401."""
    response = await client.post(
        "/api/v1/knowledge-articles",
        json={"title": "Test", "content": "Content"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_article(client, auth_headers, mock_embedding_article):
    """PUT /knowledge-articles/{id} updates the article."""
    create = await client.post(
        "/api/v1/knowledge-articles",
        json={"title": "Original Title", "content": "Original content."},
        headers=auth_headers,
    )
    article_id = create.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/knowledge-articles/{article_id}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_article_not_found(client, auth_headers, mock_embedding_article):
    """PUT /knowledge-articles/{unknown} returns 404."""
    response = await client.put(
        "/api/v1/knowledge-articles/00000000-0000-0000-0000-000000000000",
        json={"title": "Doesn't matter"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_articles(client, auth_headers, mock_embedding_article):
    """GET /knowledge-articles returns article list."""
    await client.post(
        "/api/v1/knowledge-articles",
        json={"title": "Billing FAQ", "content": "...", "category": "Billing"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/knowledge-articles", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) >= 1
