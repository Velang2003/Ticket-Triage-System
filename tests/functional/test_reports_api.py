"""Functional tests for reports and health endpoints."""
import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_summary_report_empty(client, auth_headers):
    """GET /reports/summary returns valid structure with zero tickets."""
    response = await client.get("/api/v1/reports/summary", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["total"] == 0
    assert isinstance(body["data"]["by_category"], dict)
    assert isinstance(body["data"]["by_priority"], dict)
    assert isinstance(body["data"]["by_status"], dict)


@pytest.mark.asyncio
async def test_summary_report_no_auth(client):
    """GET /reports/summary requires API key."""
    response = await client.get("/api/v1/reports/summary")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_check(client):
    """GET /health returns 200 (no auth required)."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "database" in body["data"]
    assert "llm_provider" in body["data"]
