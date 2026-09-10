"""API Key authentication dependency (NFR-5).

Every route injects `Depends(verify_api_key)`.
The key is read from the `X-API-Key` request header and compared
against the value in Settings.api_key.
"""

import logging
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
    settings: Settings = Depends(get_settings),
) -> None:
    """Raise HTTP 401 if the X-API-Key header is missing or wrong."""
    if api_key is None:
        logger.warning("Request rejected: missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key):
        logger.warning("Request rejected: invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
