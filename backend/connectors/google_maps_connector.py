"""
SIMULATED connector for Google Maps reviews.

Reads from backend/data/mock_google_maps_reviews.json and returns
FeedbackItemCreate objects — identical data contract to the live connectors,
so the rest of the pipeline (classification, reply generation, dashboard)
never needs to know this platform is simulated.

platform_connections.status = 'simulated' is set in the DB to make it clear
no live Google Business Profile API is involved.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.connectors.base_connector import BaseConnector
from backend.models.models import FeedbackItemCreate

logger = logging.getLogger(__name__)

# Path is relative to the package root — works regardless of where uvicorn is launched from
_MOCK_DATA_PATH = Path(__file__).parent.parent / "data" / "mock_google_maps_reviews.json"


class GoogleMapsConnector(BaseConnector):
    """
    SIMULATED connector for Google Maps reviews.
    Reads from mock_google_maps_reviews.json (populated in Phase 2).
    Live Google Business Profile API is out of scope due to business-verification constraints.
    """

    platform = "google_maps"
    status = "simulated"

    async def fetch_feedback(self, business_id: str) -> List[FeedbackItemCreate]:
        """
        Load all reviews from the mock JSON file and return them as
        FeedbackItemCreate objects ready to be inserted into feedback_items.
        """
        try:
            raw: list[dict] = json.loads(_MOCK_DATA_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.error("Mock Google Maps data file not found: %s", _MOCK_DATA_PATH)
            return []
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse mock Google Maps data: %s", exc)
            return []

        items: List[FeedbackItemCreate] = []
        business_uuid = uuid.UUID(business_id)

        for entry in raw:
            timestamp: Optional[datetime] = None
            if entry.get("timestamp"):
                try:
                    timestamp = datetime.fromisoformat(
                        entry["timestamp"].replace("Z", "+00:00")
                    )
                except ValueError:
                    logger.warning("Could not parse timestamp: %s", entry.get("timestamp"))

            items.append(
                FeedbackItemCreate(
                    business_id=business_uuid,
                    platform=self.platform,
                    author_name=entry.get("author_name"),
                    content_text=entry["content_text"],
                    rating=entry.get("rating"),      # nullable — some entries have no rating
                    sentiment=None,                   # set by SentimentAgent in Phase 4
                    intent_category=None,             # set by SentimentAgent in Phase 4
                    external_id=entry.get("external_id"),
                    timestamp=timestamp,
                )
            )

        logger.info(
            "[SIMULATED] GoogleMapsConnector loaded %d reviews from mock dataset",
            len(items),
        )
        return items

    async def post_reply(self, external_id: str, reply_text: str) -> bool:
        """
        Simulated post — log the reply text, return True.
        No live API call is made. The reply is recorded in the DB with status 'posted'.
        """
        logger.info(
            "[SIMULATED] GoogleMapsConnector.post_reply | external_id=%s | reply=%r",
            external_id,
            reply_text,
        )
        return True
