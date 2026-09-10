"""Edge-case validation tests (SRS FR-8)."""
import pytest


@pytest.mark.asyncio
async def test_empty_subject_rejected(client, auth_headers):
    """Empty subject should return 400."""
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "", "description": "Valid description", "submitter_email": "a@b.com"},
        headers=auth_headers,
    )
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_blank_subject_rejected(client, auth_headers):
    """Whitespace-only subject should return 400."""
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "   ", "description": "Valid description", "submitter_email": "a@b.com"},
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_empty_description_rejected(client, auth_headers):
    """Empty description should return 400."""
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "Valid Subject", "description": "", "submitter_email": "a@b.com"},
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_oversized_description_rejected(client, auth_headers):
    """Description exceeding max length should return 400."""
    big_desc = "x" * 6000
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "Valid Subject", "description": big_desc, "submitter_email": "a@b.com"},
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_missing_required_fields(client, auth_headers):
    """Missing email field should return 422."""
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "Test", "description": "Test description"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_email_rejected(client, auth_headers):
    """Invalid email format should return 422."""
    response = await client.post(
        "/api/v1/tickets",
        json={"subject": "Test", "description": "Test description", "submitter_email": "not-an-email"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_status_value(client, auth_headers):
    """PATCH with unknown status value should return 400 or 422."""
    response = await client.patch(
        "/api/v1/tickets/00000000-0000-0000-0000-000000000001/status",
        json={"status": "FLYING"},
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_unknown_category_filter_returns_empty(client, auth_headers):
    """Filtering tickets by an invalid category query param should return 422."""
    response = await client.get(
        "/api/v1/tickets?category=UNKNOWN",
        headers=auth_headers,
    )
    assert response.status_code == 422
