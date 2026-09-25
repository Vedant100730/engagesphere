"""
JWT auth middleware using Supabase.
Verifies Bearer token, returns user_id + email + business_id.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client  # type: ignore
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.db import get_db

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)

_supabase_client = None


def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        sb = get_supabase()
        response = sb.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        user = response.user
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )

    # Try user_id column first (schema_v2), fall back to id lookup
    try:
        row = await db.execute(
            text("SELECT id FROM businesses WHERE user_id = :uid LIMIT 1"),
            {"uid": str(user.id)},
        )
        business = row.fetchone()
    except Exception:
        # schema_v2 not applied yet — this won't happen if setup was followed
        business = None

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No business found. Please sign up first.",
        )

    return {
        "user_id": str(user.id),
        "email": user.email or "",
        "business_id": str(business.id),
    }
