"""Authentication middleware for Supabase JWT verification."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database.supabase_client import verify_jwt

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify JWT and return the current user.

    Raises:
        HTTPException: 401 if JWT is invalid or missing.
    """
    token = credentials.credentials
    user = verify_jwt(token)

    if not user:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )

    return user
