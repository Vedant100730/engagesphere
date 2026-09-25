"""POST /api/classify — batch classify feedback for authenticated business."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.sentiment_agent import sentiment_agent
from backend.database.db import get_db
from backend.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
async def classify_feedback(
    force: bool = Query(False, description="Force reclassify all items, not just unclassified"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]

    if force:
        # Reclassify everything — useful after fixing the sentiment model
        rows = await db.execute(
            text("SELECT id, content_text FROM feedback_items WHERE business_id = :bid ORDER BY created_at ASC"),
            {"bid": business_id},
        )
    else:
        rows = await db.execute(
            text(
                """
                SELECT id, content_text FROM feedback_items
                WHERE business_id = :bid AND (sentiment IS NULL OR intent_category IS NULL)
                ORDER BY created_at ASC
                """
            ),
            {"bid": business_id},
        )

    items = rows.fetchall()
    if not items:
        return {"processed": 0, "updated": 0, "failed": 0}

    updated = failed = 0
    for row in items:
        try:
            s, intent = await sentiment_agent.classify(row.content_text or "")
            await db.execute(
                text("UPDATE feedback_items SET sentiment = :s, intent_category = :i WHERE id = :id"),
                {"s": s, "i": intent, "id": str(row.id)},
            )
            updated += 1
        except Exception as exc:
            logger.error("Failed to classify %s: %s", row.id, exc)
            failed += 1

    await db.commit()
    return {"processed": len(items), "updated": updated, "failed": failed}
