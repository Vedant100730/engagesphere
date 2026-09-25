"""
OAuth flow for Facebook + Instagram.

Step 1 — Frontend redirects user to:
  GET /api/oauth/facebook/start  → returns { auth_url }
  GET /api/oauth/instagram/start → returns { auth_url }

Step 2 — User logs in on Facebook and clicks Allow.

Step 3 — Facebook redirects to:
  GET /api/oauth/facebook/callback?code=...&state=...
  GET /api/oauth/instagram/callback?code=...&state=...

Step 4 — Backend exchanges code for access token, resolves page/IG user ID,
          stores in platform_connections, redirects browser to /dashboard.

The business owner never sees a token at any point.
"""

import logging
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.db import get_db
from backend.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

# Callback URLs are derived from BACKEND_URL env var so they work both locally
# and on Render without code changes. Must match Meta App → Valid OAuth Redirect URIs.
def _callback(platform: str) -> str:
    base = settings.BACKEND_URL.rstrip("/")
    return f"{base}/api/oauth/{platform}/callback"

FACEBOOK_SCOPES = "pages_read_engagement,pages_manage_posts,pages_show_list"
INSTAGRAM_SCOPES = "instagram_basic,instagram_manage_comments"


# ── Start OAuth ───────────────────────────────────────────────────────────────

@router.get("/facebook/start", summary="Start Facebook OAuth flow")
async def facebook_oauth_start(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Returns the Facebook OAuth URL. Frontend redirects user there.
    State encodes the business_id so the callback knows who's connecting.
    """
    if not settings.META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID not configured")

    state = current_user["business_id"]
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": _callback("facebook"),
        "scope": FACEBOOK_SCOPES,
        "state": state,
        "response_type": "code",
    }
    auth_url = "https://www.facebook.com/v19.0/dialog/oauth?" + urlencode(params)
    return {"auth_url": auth_url, "platform": "facebook"}


@router.get("/instagram/start", summary="Start Instagram OAuth flow")
async def instagram_oauth_start(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Returns the Instagram OAuth URL. Uses Facebook's OAuth dialog with
    Instagram-specific scopes (Instagram is part of the Meta platform).
    """
    if not settings.META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID not configured")

    state = current_user["business_id"]
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": _callback("instagram"),
        "scope": INSTAGRAM_SCOPES,
        "state": state,
        "response_type": "code",
    }
    auth_url = "https://www.facebook.com/v19.0/dialog/oauth?" + urlencode(params)
    return {"auth_url": auth_url, "platform": "instagram"}


# ── Facebook Callback ─────────────────────────────────────────────────────────

@router.get("/facebook/callback", summary="Facebook OAuth callback")
async def facebook_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),  # business_id
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receives the authorization code from Facebook.
    Exchanges it for an access token, resolves the Page token,
    stores it in platform_connections, and redirects to dashboard.
    """
    if error:
        logger.warning("Facebook OAuth error: %s", error)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=facebook_denied")

    business_id = state
    try:
        uuid.UUID(business_id)
    except ValueError:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=invalid_state")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Exchange code for user access token
            token_resp = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "redirect_uri": _callback("facebook"),
                    "code": code,
                },
            )
            if not token_resp.is_success:
                raise Exception(f"Token exchange failed: {token_resp.text}")
            token_data = token_resp.json()
            user_token = token_data.get("access_token")
            if not user_token:
                raise Exception("No access_token in response")

            # Step 2: Get the user's Pages and their tokens
            pages_resp = await client.get(
                f"{GRAPH_API_BASE}/me/accounts",
                params={"access_token": user_token, "fields": "id,name,access_token"},
            )
            if not pages_resp.is_success:
                raise Exception(f"Failed to fetch pages: {pages_resp.text}")
            pages = pages_resp.json().get("data", [])

            if not pages:
                # No pages — store user token directly
                page_id = None
                page_token = user_token
                page_name = "Facebook"
            else:
                # Use the first page's token (Page Access Token is long-lived)
                page = pages[0]
                page_id = page["id"]
                page_token = page.get("access_token", user_token)
                page_name = page.get("name", "Facebook Page")

        # Store in platform_connections
        await db.execute(
            text(
                """
                INSERT INTO platform_connections
                    (id, business_id, platform, status, access_token, page_id, created_at)
                VALUES (:id, :bid, 'facebook', 'live', :token, :page_id, NOW())
                ON CONFLICT (business_id, platform)
                DO UPDATE SET access_token = :token, page_id = :page_id
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "bid": business_id,
                "token": page_token,
                "page_id": page_id,
            },
        )
        await db.commit()
        logger.info("Facebook OAuth complete for business %s, page=%s", business_id, page_name)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?success=facebook")

    except Exception as exc:
        logger.error("Facebook OAuth callback failed: %s", exc)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=facebook_failed")


# ── Instagram Callback ────────────────────────────────────────────────────────

@router.get("/instagram/callback", summary="Instagram OAuth callback")
async def instagram_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),  # business_id
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receives the authorization code from Instagram (via Meta OAuth).
    Exchanges for a token, resolves the IG user ID, stores in DB.
    """
    if error:
        logger.warning("Instagram OAuth error: %s", error)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=instagram_denied")

    business_id = state
    try:
        uuid.UUID(business_id)
    except ValueError:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=invalid_state")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Exchange code for token
            token_resp = await client.get(
                f"{GRAPH_API_BASE}/oauth/access_token",
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "redirect_uri": _callback("instagram"),
                    "code": code,
                },
            )
            if not token_resp.is_success:
                raise Exception(f"Token exchange failed: {token_resp.text}")
            user_token = token_resp.json().get("access_token")
            if not user_token:
                raise Exception("No access_token in response")

            # Resolve IG user ID
            me_resp = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={"access_token": user_token, "fields": "id,username"},
            )
            if not me_resp.is_success:
                raise Exception(f"Failed to resolve IG user: {me_resp.text}")
            ig_data = me_resp.json()
            ig_user_id = ig_data.get("id")
            username = ig_data.get("username", "")

        await db.execute(
            text(
                """
                INSERT INTO platform_connections
                    (id, business_id, platform, status, access_token, ig_user_id, created_at)
                VALUES (:id, :bid, 'instagram', 'live', :token, :ig_uid, NOW())
                ON CONFLICT (business_id, platform)
                DO UPDATE SET access_token = :token, ig_user_id = :ig_uid
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "bid": business_id,
                "token": user_token,
                "ig_uid": ig_user_id,
            },
        )
        await db.commit()
        logger.info("Instagram OAuth complete for business %s, user=%s", business_id, username)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?success=instagram")

    except Exception as exc:
        logger.error("Instagram OAuth callback failed: %s", exc)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?error=instagram_failed")
