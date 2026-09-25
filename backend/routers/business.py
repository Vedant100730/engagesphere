"""
Business + platform connection management.

POST /api/business/connect/facebook   — save Facebook Page token
POST /api/business/connect/instagram  — save Instagram token
GET  /api/business/connections        — list connected platforms
POST /api/business/seed               — seed business info into Pinecone
GET  /api/business/seed/verify        — verify RAG retrieval
"""

import hashlib
import logging
import uuid
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.db import get_db
from backend.middleware.auth import get_current_user
from backend.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)
router = APIRouter()
_NAMESPACE = "business-info"
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


# ── Platform connection models ────────────────────────────────────────────────

class FacebookConnectRequest(BaseModel):
    access_token: str = Field(..., description="Facebook Page Access Token")


class InstagramConnectRequest(BaseModel):
    access_token: str = Field(..., description="Instagram User Access Token")


# ── Connect Facebook ──────────────────────────────────────────────────────────

@router.post("/connect/facebook", summary="Connect Facebook Page")
async def connect_facebook(
    req: FacebookConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Validates the Facebook Page token, resolves the Page ID,
    and stores the token in platform_connections.
    """
    business_id = current_user["business_id"]

    # Validate token and get Page ID
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={"access_token": req.access_token, "fields": "id,name"},
            )
            if not resp.is_success:
                err = resp.json().get("error", {})
                raise HTTPException(status_code=400, detail=f"Invalid Facebook token: {err.get('message', resp.text)}")
            data = resp.json()
            if "error" in data:
                raise HTTPException(status_code=400, detail=data["error"].get("message", "Token error"))
            page_id = data["id"]
            page_name = data.get("name", "")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Facebook validation failed: {exc}")

    # Upsert into platform_connections
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
            "token": req.access_token,
            "page_id": page_id,
        },
    )
    await db.commit()
    logger.info("Facebook connected for business %s: page_id=%s", business_id, page_id)
    return {"platform": "facebook", "connected": True, "page_id": page_id, "page_name": page_name}


# ── Connect Instagram ─────────────────────────────────────────────────────────

@router.post("/connect/instagram", summary="Connect Instagram Business account")
async def connect_instagram(
    req: InstagramConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Validates the Instagram token, resolves the IG user ID,
    and stores the token in platform_connections.
    """
    business_id = current_user["business_id"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/me",
                params={"access_token": req.access_token, "fields": "id,username"},
            )
            if not resp.is_success:
                raise HTTPException(status_code=400, detail="Invalid Instagram token")
            data = resp.json()
            ig_user_id = data["id"]
            username = data.get("username", "")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Instagram validation failed: {exc}")

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
            "token": req.access_token,
            "ig_uid": ig_user_id,
        },
    )
    await db.commit()
    logger.info("Instagram connected for business %s: ig_user_id=%s", business_id, ig_user_id)
    return {"platform": "instagram", "connected": True, "ig_user_id": ig_user_id, "username": username}


# ── List connections ──────────────────────────────────────────────────────────

@router.get("/connections", summary="List connected platforms")
async def list_connections(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    rows = await db.execute(
        text(
            """
            SELECT platform, status,
                   CASE WHEN access_token IS NOT NULL THEN true ELSE false END as connected,
                   page_id, ig_user_id, created_at
            FROM platform_connections WHERE business_id = :bid
            """
        ),
        {"bid": current_user["business_id"]},
    )
    platforms = [dict(r._mapping) for r in rows.fetchall()]
    return {"platforms": platforms}


# ── Seed business info ────────────────────────────────────────────────────────

class HoursEntry(BaseModel):
    day: str
    hours: str


class MenuItem(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[str] = None


class MenuSection(BaseModel):
    section: str
    items: list[MenuItem]


class BusinessSeedRequest(BaseModel):
    business_name: str
    tagline: Optional[str] = None
    hours: list[HoursEntry] = Field(default_factory=list)
    menu: list[MenuSection] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    contact: Optional[dict[str, str]] = None
    about: Optional[str] = None
    extra: list[str] = Field(default_factory=list)


def _make_id(business_id: str, category: str, content: str) -> str:
    slug = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{business_id}::{category}::{slug}"


def _build_chunks(req: BusinessSeedRequest, business_id: str) -> list[dict]:
    chunks = []
    if req.about or req.tagline:
        text_ = f"{req.business_name}\n" + "\n".join(filter(None, [req.tagline, req.about]))
        chunks.append({"category": "about", "text": text_, "id": _make_id(business_id, "about", text_)})

    if req.hours:
        text_ = f"{req.business_name} opening hours:\n" + "\n".join(f"{e.day}: {e.hours}" for e in req.hours)
        chunks.append({"category": "hours", "text": text_, "id": _make_id(business_id, "hours", text_)})

    for section in req.menu:
        lines = [f"  - {i.name}" + (f": {i.description}" if i.description else "") + (f" ({i.price})" if i.price else "") for i in section.items]
        text_ = f"{req.business_name} — {section.section} menu:\n" + "\n".join(lines)
        chunks.append({"category": f"menu_{section.section}", "text": text_, "id": _make_id(business_id, f"menu_{section.section}", text_)})

    for i, policy in enumerate(req.policies):
        text_ = f"{req.business_name} policy: {policy}"
        chunks.append({"category": "policy", "text": text_, "id": _make_id(business_id, f"policy_{i}", text_)})

    if req.contact:
        text_ = f"{req.business_name} contact:\n" + "\n".join(f"{k}: {v}" for k, v in req.contact.items())
        chunks.append({"category": "contact", "text": text_, "id": _make_id(business_id, "contact", text_)})

    for i, fact in enumerate(req.extra):
        text_ = f"{req.business_name}: {fact}"
        chunks.append({"category": "extra", "text": text_, "id": _make_id(business_id, f"extra_{i}", text_)})

    return chunks


@router.post("/seed", summary="Seed business facts into Pinecone")
async def seed_business_info(
    req: BusinessSeedRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    chunks = _build_chunks(req, business_id)
    if not chunks:
        raise HTTPException(status_code=422, detail="No content to seed")

    vectors = []
    for chunk in chunks:
        emb = await pinecone_service.embed(chunk["text"])
        vectors.append({
            "id": chunk["id"],
            "values": emb,
            "metadata": {
                "text": chunk["text"],
                "category": chunk["category"],
                "business_id": business_id,
            },
        })

    await pinecone_service.upsert(namespace=_NAMESPACE, vectors=vectors)
    return {
        "business_id": business_id,
        "upserted": len(vectors),
        "chunks": [{"category": c["category"], "preview": c["text"][:100]} for c in chunks],
    }


@router.get("/seed/verify", summary="Verify RAG retrieval")
async def verify_seed(
    query: str = "What are your opening hours?",
    top_k: int = 3,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    chunks = await pinecone_service.query(namespace=_NAMESPACE, query_text=query, top_k=top_k)
    relevant = [c for c in chunks if c.get("business_id") == business_id]
    return {"query": query, "chunks_retrieved": len(relevant), "chunks": relevant}
