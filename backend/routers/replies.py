"""
POST /api/replies/generate  — generate AI replies
GET  /api/replies/          — list replies
PATCH /api/replies/{id}     — approve/edit
POST /api/replies/{id}/post — post to platform
"""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.reply_agent import reply_agent
from backend.database.db import get_db
from backend.middleware.auth import get_current_user
from backend.models.models import ReplyUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _row_to_dict(row: Any) -> dict:
    return dict(row._mapping)


@router.post("/generate")
async def generate_replies(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]

    rows = await db.execute(
        text(
            """
            SELECT fi.id, fi.content_text, fi.sentiment, fi.intent_category, fi.platform
            FROM   feedback_items fi
            LEFT JOIN replies r ON r.feedback_item_id = fi.id
            WHERE  fi.business_id = :bid
              AND  r.id IS NULL
              AND  (fi.intent_category IS NULL OR fi.intent_category != 'spam')
            ORDER  BY fi.created_at ASC
            """
        ),
        {"bid": business_id},
    )
    items = [_row_to_dict(r) for r in rows.fetchall()]
    if not items:
        return {"generated": 0, "skipped": 0, "failed": 0, "toxicity_flagged": 0}

    results = await reply_agent.generate_replies_for_business(
        business_id=business_id, feedback_items=items
    )

    generated = skipped = failed = flagged = 0
    errors = []
    for res in results:
        if res["skipped"]:
            skipped += 1
            if res.get("error"):
                errors.append({"item_id": res["feedback_item_id"], "error": res["error"]})
            continue
        if res["text"] is None:
            failed += 1
            errors.append({"item_id": res["feedback_item_id"], "error": res.get("error", "LLM returned None")})
            continue
        await db.execute(
            text(
                """
                INSERT INTO replies
                    (id, feedback_item_id, generated_text, status, toxicity_flagged, created_at)
                VALUES (:id, :fid, :text, 'pending', :toxic, NOW())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "fid": res["feedback_item_id"],
                "text": res["text"],
                "toxic": res["toxicity_flagged"],
            },
        )
        generated += 1
        if res["toxicity_flagged"]:
            flagged += 1

    await db.commit()
    return {
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "toxicity_flagged": flagged,
        "errors": errors,
    }


@router.get("/")
async def list_replies(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    conditions = ["fi.business_id = :bid"]
    params: dict[str, Any] = {"bid": business_id, "limit": limit, "offset": offset}

    if status:
        conditions.append("r.status = :status")
        params["status"] = status

    where = "WHERE " + " AND ".join(conditions)

    rows = await db.execute(
        text(
            f"""
            SELECT r.id, r.feedback_item_id, r.generated_text, r.status,
                   r.toxicity_flagged, r.posted_at, r.created_at,
                   fi.platform, fi.author_name, fi.content_text
            FROM   replies r
            JOIN   feedback_items fi ON fi.id = r.feedback_item_id
            {where}
            ORDER  BY r.created_at DESC
            LIMIT  :limit OFFSET :offset
            """
        ),
        params,
    )
    count_row = await db.execute(
        text(
            f"SELECT COUNT(*) FROM replies r "
            f"JOIN feedback_items fi ON fi.id = r.feedback_item_id {where}"
        ),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    )
    return {
        "items": [_row_to_dict(r) for r in rows.fetchall()],
        "total": count_row.scalar() or 0,
    }


@router.get("/{reply_id}")
async def get_reply(
    reply_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    row = await db.execute(
        text(
            """
            SELECT r.*, fi.platform, fi.author_name, fi.content_text, fi.external_id
            FROM replies r
            JOIN feedback_items fi ON fi.id = r.feedback_item_id
            WHERE r.id = :id AND fi.business_id = :bid LIMIT 1
            """
        ),
        {"id": reply_id, "bid": current_user["business_id"]},
    )
    result = row.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Reply not found")
    return _row_to_dict(result)


@router.patch("/{reply_id}")
async def update_reply(
    reply_id: str,
    update: ReplyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    set_clauses = []
    params: dict[str, Any] = {"id": reply_id}

    if update.status:
        set_clauses.append("status = :status")
        params["status"] = update.status
    if update.generated_text is not None:
        set_clauses.append("generated_text = :generated_text")
        params["generated_text"] = update.generated_text
        if not update.status:
            set_clauses.append("status = 'edited'")

    if not set_clauses:
        raise HTTPException(status_code=422, detail="No fields to update")

    await db.execute(
        text(f"UPDATE replies SET {', '.join(set_clauses)} WHERE id = :id"),
        params,
    )
    await db.commit()
    return await get_reply(reply_id, db, current_user)


@router.post("/{reply_id}/post")
async def post_reply(
    reply_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    business_id = current_user["business_id"]
    row = await db.execute(
        text(
            """
            SELECT r.id, r.generated_text, r.status, fi.platform, fi.external_id
            FROM replies r
            JOIN feedback_items fi ON fi.id = r.feedback_item_id
            WHERE r.id = :id AND fi.business_id = :bid LIMIT 1
            """
        ),
        {"id": reply_id, "bid": business_id},
    )
    result = row.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Reply not found")

    reply = _row_to_dict(result)
    if reply["status"] not in ("approved", "edited"):
        raise HTTPException(status_code=422, detail="Reply must be approved or edited first")
    if not reply["external_id"]:
        raise HTTPException(status_code=422, detail="No external_id — cannot post")

    # Get token for this platform
    token_row = await db.execute(
        text(
            "SELECT access_token, page_id, ig_user_id FROM platform_connections "
            "WHERE business_id = :bid AND platform = :platform LIMIT 1"
        ),
        {"bid": business_id, "platform": reply["platform"]},
    )
    token_data = token_row.fetchone()
    if not token_data or not token_data.access_token:
        raise HTTPException(status_code=422, detail=f"{reply['platform']} not connected")

    if reply["platform"] == "facebook":
        from backend.connectors.facebook_connector import FacebookConnector
        connector = FacebookConnector(access_token=token_data.access_token)
    elif reply["platform"] == "instagram":
        from backend.connectors.instagram_connector import InstagramConnector
        connector = InstagramConnector(access_token=token_data.access_token)
    else:
        raise HTTPException(status_code=422, detail=f"Posting not supported for {reply['platform']}")

    success = await connector.post_reply(reply["external_id"], reply["generated_text"])
    if not success:
        raise HTTPException(status_code=502, detail="Failed to post reply")

    await db.execute(
        text("UPDATE replies SET status = 'posted', posted_at = NOW() WHERE id = :id"),
        {"id": reply_id},
    )
    await db.commit()
    return await get_reply(reply_id, db, current_user)
