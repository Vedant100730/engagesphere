"""
GET  /api/suggestions/       — list suggestions
POST /api/suggestions/generate — run suggestion agent
POST /api/suggestions/seed-kb  — seed best practices KB (admin, no auth needed)
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.suggestion_agent import suggestion_agent
from backend.database.db import get_db
from backend.middleware.auth import get_current_user
from backend.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)
router = APIRouter()

_KB_PATH = Path(__file__).parent.parent / "data" / "best_practices_kb.json"


def _row_to_dict(row: Any) -> dict:
    d = dict(row._mapping)
    if isinstance(d.get("evidence_quotes"), str):
        try:
            d["evidence_quotes"] = json.loads(d["evidence_quotes"])
        except Exception:
            pass
    return d


@router.get("/")
async def list_suggestions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    rows = await db.execute(
        text(
            """
            SELECT id, business_id, suggestion_text, evidence_quotes, source_reference, created_at
            FROM suggestions WHERE business_id = :bid
            ORDER BY created_at DESC LIMIT :limit OFFSET :offset
            """
        ),
        {"bid": business_id, "limit": limit, "offset": offset},
    )
    count_row = await db.execute(
        text("SELECT COUNT(*) FROM suggestions WHERE business_id = :bid"),
        {"bid": business_id},
    )
    return {
        "items": [_row_to_dict(r) for r in rows.fetchall()],
        "total": count_row.scalar() or 0,
    }


@router.post("/generate")
async def generate_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]

    rows = await db.execute(
        text(
            """
            SELECT id, content_text, sentiment, intent_category, platform, author_name
            FROM feedback_items
            WHERE business_id = :bid AND intent_category IS NOT NULL AND intent_category != 'spam'
            ORDER BY created_at ASC
            """
        ),
        {"bid": business_id},
    )
    feedback_items = [_row_to_dict(r) for r in rows.fetchall()]
    if not feedback_items:
        return {"generated": 0, "suggestions": [], "message": "No classified feedback yet"}

    suggestions = await suggestion_agent.generate_suggestions(
        business_id=business_id, feedback_items=feedback_items
    )

    inserted = []
    for s in suggestions:
        sid = str(uuid.uuid4())
        await db.execute(
            text(
                """
                INSERT INTO suggestions
                    (id, business_id, suggestion_text, evidence_quotes, source_reference, created_at)
                VALUES (:id, :bid, :text, CAST(:eq AS jsonb), :src, NOW())
                """
            ),
            {
                "id": sid, "bid": business_id,
                "text": s["suggestion_text"],
                "eq": json.dumps(s["evidence_quotes"]),
                "src": s.get("source_reference"),
            },
        )
        inserted.append({"id": sid, **s})

    await db.commit()
    return {"generated": len(inserted), "suggestions": inserted}


@router.post("/seed-kb", summary="Seed best-practices KB (run once)")
async def seed_kb() -> dict[str, Any]:
    """No auth required — run once at setup time."""
    docs: list[dict] = json.loads(_KB_PATH.read_text(encoding="utf-8"))
    vectors = []
    for doc in docs:
        if not doc.get("id") or not doc.get("text"):
            continue
        emb = await pinecone_service.embed(doc["text"])
        vectors.append({
            "id": doc["id"],
            "values": emb,
            "metadata": {"text": doc["text"], "source": doc.get("source", "")},
        })

    await pinecone_service.upsert(namespace="best-practices", vectors=vectors)
    return {"upserted": len(vectors)}
