"""
GET /api/feedback/     — list feedback for authenticated business
GET /api/feedback/{id} — single item
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _row_to_dict(row: Any) -> dict:
    return dict(row._mapping)


@router.get("/")
async def list_feedback(
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    conditions = ["business_id = :business_id"]
    params: dict[str, Any] = {"business_id": business_id, "limit": limit, "offset": offset}

    if platform:
        conditions.append("platform = :platform")
        params["platform"] = platform
    if sentiment:
        conditions.append("sentiment = :sentiment")
        params["sentiment"] = sentiment

    where = "WHERE " + " AND ".join(conditions)

    rows = await db.execute(
        text(
            f"""
            SELECT id, business_id, platform, author_name, content_text,
                   rating, sentiment, intent_category, external_id, timestamp, created_at
            FROM   feedback_items
            {where}
            ORDER  BY created_at DESC
            LIMIT  :limit OFFSET :offset
            """
        ),
        params,
    )
    count_row = await db.execute(
        text(f"SELECT COUNT(*) FROM feedback_items {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    total: int = count_row.scalar() or 0
    return {"items": [_row_to_dict(r) for r in rows.fetchall()], "total": total}


@router.get("/{feedback_id}")
async def get_feedback_item(
    feedback_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    row = await db.execute(
        text(
            "SELECT * FROM feedback_items WHERE id = :id AND business_id = :bid LIMIT 1"
        ),
        {"id": feedback_id, "bid": current_user["business_id"]},
    )
    result = row.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Feedback item not found")
    return _row_to_dict(result)
