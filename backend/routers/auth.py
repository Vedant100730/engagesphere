"""
POST /api/auth/signup   — create Supabase user + business row
POST /api/auth/login    — sign in, return JWT
POST /api/auth/logout   — sign out
GET  /api/auth/me       — get current user + business info
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client  # type: ignore

from backend.config import settings
from backend.database.db import get_db
from backend.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    business_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@router.post("/signup", summary="Create account + business")
async def signup(
    req: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Creates a Supabase auth user and a linked businesses row in one step.
    Returns the access token so the user is immediately logged in.
    """
    sb = _supabase()

    # Create Supabase auth user
    try:
        auth_resp = sb.auth.admin.create_user({
            "email": req.email,
            "password": req.password,
            "email_confirm": True,  # skip email verification for now
        })
        if not auth_resp or not auth_resp.user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        user_id = str(auth_resp.user.id)
    except HTTPException:
        raise
    except Exception as exc:
        msg = str(exc)
        if "already registered" in msg.lower() or "already been registered" in msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        logger.error("Supabase signup error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))

    # Check if business already exists for this user
    existing = await db.execute(
        text("SELECT id FROM businesses WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    )
    existing_row = existing.fetchone()  # fetch ONCE and store
    if not existing_row:
        # Create business row
        business_id = str(uuid.uuid4())
        await db.execute(
            text(
                "INSERT INTO businesses (id, name, email, user_id, created_at) "
                "VALUES (:id, :name, :email, :user_id, NOW())"
            ),
            {
                "id": business_id,
                "name": req.business_name,
                "email": req.email,
                "user_id": user_id,
            },
        )
        await db.commit()
    else:
        business_id = str(existing_row.id)  # use stored row, not second fetchone

    # Sign in to get JWT
    sign_in = sb.auth.sign_in_with_password({
        "email": req.email,
        "password": req.password,
    })

    return {
        "access_token": sign_in.session.access_token,
        "refresh_token": sign_in.session.refresh_token,
        "user": {
            "id": user_id,
            "email": req.email,
            "business_name": req.business_name,
            "business_id": business_id,
        },
    }


async def _auto_seed_env_tokens(db: AsyncSession, business_id: str) -> None:
    """
    If FACEBOOK_PAGE_ACCESS_TOKEN or INSTAGRAM_ACCESS_TOKEN are set in .env,
    store them in platform_connections for this business automatically.
    This means the owner doesn't need to go through the onboarding token flow
    when they already have tokens in their .env.
    """
    if settings.FACEBOOK_PAGE_ACCESS_TOKEN:
        await db.execute(
            text(
                """
                INSERT INTO platform_connections
                    (id, business_id, platform, status, access_token, created_at)
                VALUES (:id, :bid, 'facebook', 'live', :token, NOW())
                ON CONFLICT (business_id, platform)
                DO UPDATE SET access_token = :token
                WHERE platform_connections.access_token IS NULL
                   OR platform_connections.access_token != :token
                """
            ),
            {"id": str(uuid.uuid4()), "bid": business_id,
             "token": settings.FACEBOOK_PAGE_ACCESS_TOKEN},
        )
    if settings.INSTAGRAM_ACCESS_TOKEN:
        await db.execute(
            text(
                """
                INSERT INTO platform_connections
                    (id, business_id, platform, status, access_token, created_at)
                VALUES (:id, :bid, 'instagram', 'live', :token, NOW())
                ON CONFLICT (business_id, platform)
                DO UPDATE SET access_token = :token
                WHERE platform_connections.access_token IS NULL
                   OR platform_connections.access_token != :token
                """
            ),
            {"id": str(uuid.uuid4()), "bid": business_id,
             "token": settings.INSTAGRAM_ACCESS_TOKEN},
        )
    await db.commit()


@router.post("/login", summary="Login")
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Sign in with email + password. Returns JWT + business info."""
    sb = _supabase()
    try:
        sign_in = sb.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })
        if not sign_in.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(sign_in.user.id)

    # Get business info — create a recovery row if missing (handles orphaned accounts
    # where Supabase auth user exists but the businesses row was never committed)
    row = await db.execute(
        text("SELECT id, name FROM businesses WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    )
    business = row.fetchone()
    if not business:
        # Recover: create a business row so the user isn't permanently locked out
        business_id = str(uuid.uuid4())
        email_name = sign_in.user.email.split("@")[0].replace(".", " ").title()
        await db.execute(
            text(
                "INSERT INTO businesses (id, name, email, user_id, created_at) "
                "VALUES (:id, :name, :email, :user_id, NOW())"
            ),
            {
                "id": business_id,
                "name": f"{email_name}'s Business",
                "email": sign_in.user.email,
                "user_id": user_id,
            },
        )
        await db.commit()
        business_name = f"{email_name}'s Business"
    else:
        business_id = str(business.id)
        business_name = business.name

    # Auto-seed tokens from .env into platform_connections if present
    await _auto_seed_env_tokens(db, business_id)

    return {
        "access_token": sign_in.session.access_token,
        "refresh_token": sign_in.session.refresh_token,
        "user": {
            "id": user_id,
            "email": sign_in.user.email,
            "business_name": business_name,
            "business_id": business_id,
        },
    }


@router.get("/me", summary="Get current user info")
async def me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Returns current user + business info from JWT."""
    row = await db.execute(
        text("SELECT id, name, email FROM businesses WHERE user_id = :uid LIMIT 1"),
        {"uid": current_user["user_id"]},
    )
    business = row.fetchone()
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "business_id": current_user["business_id"],
        "business_name": business.name if business else "",
    }
