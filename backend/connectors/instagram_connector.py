"""
Live connector for Instagram Business comments via Meta Graph API.
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
_MEDIA_LIMIT = 25
_COMMENTS_LIMIT = 100


def _parse_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


class InstagramConnector(BaseConnector):
    platform = "instagram"
    status = "live"

    def __init__(self, access_token: str = "", ig_user_id: Optional[str] = None):
        self._token = access_token
        self._ig_user_id = ig_user_id

    async def fetch_feedback(self, business_id: str) -> list[FeedbackItemCreate]:
        if not self._token:
            raise RuntimeError("Instagram access token not set")

        business_uuid = uuid.UUID(business_id)
        items: list[FeedbackItemCreate] = []

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                ig_user_id = self._ig_user_id or await self._get_ig_user_id(client)
            except RuntimeError as exc:
                raise RuntimeError(f"Instagram token invalid or expired: {exc}")
            media_list = await self._get_media(client, ig_user_id)
            for media in media_list:
                comments = await self._get_comments(client, media["id"])
                for c in comments:
                    items.append(FeedbackItemCreate(
                        business_id=business_uuid,
                        platform=self.platform,
                        author_name=c.get("username"),
                        content_text=c.get("text", ""),
                        rating=None,
                        sentiment=None,
                        intent_category=None,
                        external_id=c.get("id"),
                        timestamp=_parse_ts(c.get("timestamp")),
                    ))

        logger.info("[LIVE] Instagram: fetched %d comments", len(items))
        return items

    async def post_reply(self, external_id: str, reply_text: str) -> bool:
        if not self._token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{GRAPH_API_BASE}/{external_id}/replies",
                    params={"access_token": self._token},
                    json={"message": reply_text},
                )
                self._raise_for_error(resp)
                return True
        except Exception as exc:
            logger.error("Instagram post_reply failed: %s", exc)
            return False

    async def _get_ig_user_id(self, client: httpx.AsyncClient) -> str:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me",
            params={"access_token": self._token, "fields": "id,username"},
        )
        self._raise_for_error(resp)
        return resp.json()["id"]

    async def _get_media(self, client: httpx.AsyncClient, ig_user_id: str) -> list[dict]:
        resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_user_id}/media",
            params={"access_token": self._token, "fields": "id,caption,timestamp", "limit": _MEDIA_LIMIT},
        )
        self._raise_for_error(resp)
        return resp.json().get("data", [])

    async def _get_comments(self, client: httpx.AsyncClient, media_id: str) -> list[dict]:
        comments: list[dict] = []
        url = f"{GRAPH_API_BASE}/{media_id}/comments"
        params: dict[str, Any] = {
            "access_token": self._token,
            "fields": "id,text,username,timestamp",
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
            raise RuntimeError(f"Instagram API error {err.get('code')}: {err.get('message')}")
        except (ValueError, KeyError):
            raise RuntimeError(f"Instagram API {resp.status_code}: {resp.text[:200]}")
