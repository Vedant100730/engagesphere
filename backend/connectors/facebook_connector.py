"""
Live connector for Facebook Page comments via Meta Graph API.
Token is passed per-instance (stored in DB per business) — not from .env.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from backend.connectors.base_connector import BaseConnector
from backend.models.models import FeedbackItemCreate

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
_COMMENTS_LIMIT = 100
_POSTS_LIMIT = 25


def _parse_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


class FacebookConnector(BaseConnector):
    platform = "facebook"
    status = "live"

    def __init__(self, access_token: str = "", page_id: Optional[str] = None):
        self._token = access_token
        self._page_id = page_id

    async def fetch_feedback(self, business_id: str) -> list[FeedbackItemCreate]:
        if not self._token:
            raise RuntimeError("Facebook access token not set")

        business_uuid = uuid.UUID(business_id)
        items: list[FeedbackItemCreate] = []

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                page_id = self._page_id or await self._get_page_id(client)
            except RuntimeError as exc:
                raise RuntimeError(f"Facebook token invalid or expired: {exc}")
            posts = await self._get_posts(client, page_id)
            for post in posts:
                comments = await self._get_comments(client, post["id"])
                for c in comments:
                    items.append(FeedbackItemCreate(
                        business_id=business_uuid,
                        platform=self.platform,
                        author_name=c.get("from", {}).get("name"),
                        content_text=c.get("message", ""),
                        rating=None,
                        sentiment=None,
                        intent_category=None,
                        external_id=c.get("id"),
                        timestamp=_parse_ts(c.get("created_time")),
                    ))

        logger.info("[LIVE] Facebook: fetched %d comments", len(items))
        return items

    async def post_reply(self, external_id: str, reply_text: str) -> bool:
        if not self._token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{GRAPH_API_BASE}/{external_id}/comments",
                    params={"access_token": self._token},
                    json={"message": reply_text},
                )
                self._raise_for_error(resp)
                return True
        except Exception as exc:
            logger.error("Facebook post_reply failed: %s", exc)
            return False

    async def _get_page_id(self, client: httpx.AsyncClient) -> str:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me",
            params={"access_token": self._token, "fields": "id,name"},
        )
        self._raise_for_error(resp)
        return resp.json()["id"]

    async def _get_posts(self, client: httpx.AsyncClient, page_id: str) -> list[dict]:
        resp = await client.get(
            f"{GRAPH_API_BASE}/{page_id}/feed",
            params={"access_token": self._token, "fields": "id,message,created_time", "limit": _POSTS_LIMIT},
        )
        self._raise_for_error(resp)
        return resp.json().get("data", [])

    async def _get_comments(self, client: httpx.AsyncClient, post_id: str) -> list[dict]:
        comments: list[dict] = []
        url = f"{GRAPH_API_BASE}/{post_id}/comments"
        params: dict[str, Any] = {
            "access_token": self._token,
            "fields": "id,message,from,created_time",
            "limit": _COMMENTS_LIMIT,
        }
        while url:
            resp = await client.get(url, params=params)
            self._raise_for_error(resp)
            body = resp.json()
            comments.extend(body.get("data", []))
            url = body.get("paging", {}).get("next")
            params = {}
        return comments

    @staticmethod
    def _raise_for_error(resp: httpx.Response) -> None:
        if resp.is_success:
            return
        try:
            err = resp.json().get("error", {})
            raise RuntimeError(f"Facebook API error {err.get('code')}: {err.get('message')}")
        except (ValueError, KeyError):
            raise RuntimeError(f"Facebook API {resp.status_code}: {resp.text[:200]}")
