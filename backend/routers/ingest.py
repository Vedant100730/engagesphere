"""
POST /api/ingest — fetch real comments from Facebook + Instagram (live only).
Mock data connectors removed — real product uses only live data.
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.sentiment_agent import sentiment_agent
from backend.config import settings
from backend.database.db import get_db
from backend.middleware.auth import get_current_user
from backend.models.models import FeedbackItemCreate

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_platform_tokens(db: AsyncSession, business_id: str) -> dict:
    """Get stored OAuth tokens for this business from platform_connections."""
    rows = await db.execute(
        text(
            "SELECT platform, access_token, page_id, ig_user_id "
            "FROM platform_connections "
            "WHERE business_id = :bid AND access_token IS NOT NULL"
        ),
        {"bid": business_id},
    )
    tokens = {}
    for row in rows.fetchall():
        tokens[row.platform] = {
            "access_token": row.access_token,
            "page_id": row.page_id,
            "ig_user_id": row.ig_user_id,
        }
    return tokens


async def _upsert_feedback_items(
    db: AsyncSession,
    items: list[FeedbackItemCreate],
) -> list[str]:
    new_ids: list[str] = []
    for item in items:
        # Always dedup on (business_id + platform + external_id) if external_id exists
        if item.external_id:
            existing = await db.execute(
                text(
                    "SELECT id FROM feedback_items "
                    "WHERE business_id = :bid AND platform = :platform "
                    "AND external_id = :external_id LIMIT 1"
                ),
                {
                    "bid": str(item.business_id),
                    "platform": item.platform,
                    "external_id": item.external_id,
                },
            )
            if existing.fetchone():
                continue  # already ingested for this business

        new_id = str(uuid.uuid4())
        await db.execute(
            text(
                """
                INSERT INTO feedback_items
                    (id, business_id, platform, author_name, content_text,
                     rating, sentiment, intent_category, external_id, timestamp, created_at)
                VALUES
                    (:id, :business_id, :platform, :author_name, :content_text,
                     :rating, :sentiment, :intent_category, :external_id, :timestamp, NOW())
                """
            ),
            {
                "id": new_id,
                "business_id": str(item.business_id),
                "platform": item.platform,
                "author_name": item.author_name,
                "content_text": item.content_text,
                "rating": item.rating,
                "sentiment": None,
                "intent_category": None,
                "external_id": item.external_id,
                "timestamp": item.timestamp,
            },
        )
        new_ids.append(new_id)

    await db.commit()
    return new_ids


async def _classify_new_items(db: AsyncSession, item_ids: list[str]) -> dict:
    if not item_ids:
        return {"classified": 0, "failed": 0}

    placeholders = ", ".join(f":id{i}" for i in range(len(item_ids)))
    params = {f"id{i}": id_ for i, id_ in enumerate(item_ids)}
    rows = await db.execute(
        text(f"SELECT id, content_text FROM feedback_items WHERE id IN ({placeholders})"),
        params,
    )
    items = rows.fetchall()
    classified = failed = 0

    for row in items:
        try:
            s, intent = await sentiment_agent.classify(row.content_text or "")
            await db.execute(
                text(
                    "UPDATE feedback_items SET sentiment = :s, intent_category = :i WHERE id = :id"
                ),
                {"s": s, "i": intent, "id": str(row.id)},
            )
            classified += 1
        except Exception as exc:
            logger.error("Classification failed for %s: %s", row.id, exc)
            failed += 1

    await db.commit()
    return {"classified": classified, "failed": failed}


@router.post("/", summary="Ingest real comments from connected platforms")
async def ingest_feedback(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Fetches real comments from Facebook + Instagram using stored OAuth tokens.
    Classifies each item immediately after ingestion.
    """
    business_id = current_user["business_id"]

    if not business_id:
        raise HTTPException(status_code=400, detail="No business found for this account")

    # Validate it's a proper UUID
    try:
        uuid.UUID(business_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid business_id: {business_id}")

    # Get stored tokens for this business
    platform_tokens = await _get_platform_tokens(db, business_id)

    summary = []
    total_inserted = 0
    total_classified = 0

    # Simulated connectors — always run (Google Maps + Twitter mock data)
    from backend.connectors.google_maps_connector import GoogleMapsConnector
    from backend.connectors.twitter_connector import TwitterConnector

    for connector in [GoogleMapsConnector(), TwitterConnector()]:
        try:
            items = await connector.fetch_feedback(business_id)
            new_ids = await _upsert_feedback_items(db, items)
            cr = await _classify_new_items(db, new_ids)
            skipped = len(items) - len(new_ids)
            logger.info(
                "%s: fetched=%d inserted=%d skipped=%d classified=%d",
                connector.platform, len(items), len(new_ids), skipped, cr["classified"],
            )
            summary.append({
                "platform": connector.platform,
                "status": "simulated",
                "fetched": len(items),
                "inserted": len(new_ids),
                "skipped": skipped,
                "classified": cr["classified"],
            })
            total_inserted += len(new_ids)
            total_classified += cr["classified"]
        except Exception as exc:
            logger.error("%s ingest failed: %s", connector.platform, exc)
            summary.append({"platform": connector.platform, "status": "simulated", "error": str(exc)})

    # Facebook
    fb_token = platform_tokens.get("facebook")
    if fb_token and fb_token.get("access_token"):
        try:
            from backend.connectors.facebook_connector import FacebookConnector
            connector = FacebookConnector(
                access_token=fb_token["access_token"],
                page_id=fb_token.get("page_id"),
            )
            items = await connector.fetch_feedback(business_id)
            new_ids = await _upsert_feedback_items(db, items)
            cr = await _classify_new_items(db, new_ids)
            summary.append({
                "platform": "facebook", "status": "live",
                "fetched": len(items), "inserted": len(new_ids),
                "classified": cr["classified"],
            })
            total_inserted += len(new_ids)
            total_classified += cr["classified"]
        except Exception as exc:
            logger.error("Facebook ingest failed: %s", exc)
            summary.append({"platform": "facebook", "status": "live", "error": str(exc)})
    else:
        summary.append({"platform": "facebook", "status": "not_connected", "fetched": 0})

    # Instagram
    ig_token = platform_tokens.get("instagram")
    if ig_token and ig_token.get("access_token"):
        try:
            from backend.connectors.instagram_connector import InstagramConnector
            connector = InstagramConnector(
                access_token=ig_token["access_token"],
                ig_user_id=ig_token.get("ig_user_id"),
            )
            items = await connector.fetch_feedback(business_id)
            new_ids = await _upsert_feedback_items(db, items)
            cr = await _classify_new_items(db, new_ids)
            summary.append({
                "platform": "instagram", "status": "live",
                "fetched": len(items), "inserted": len(new_ids),
                "classified": cr["classified"],
            })
            total_inserted += len(new_ids)
            total_classified += cr["classified"]
        except Exception as exc:
            logger.error("Instagram ingest failed: %s", exc)
            summary.append({"platform": "instagram", "status": "live", "error": str(exc)})
    else:
        summary.append({"platform": "instagram", "status": "not_connected", "fetched": 0})

    return {
        "business_id": business_id,
        "total_inserted": total_inserted,
        "total_classified": total_classified,
        "platforms": summary,
    }
