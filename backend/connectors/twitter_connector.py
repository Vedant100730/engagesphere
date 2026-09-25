"""
SIMULATED connector for Twitter/X mentions.

Reads from backend/data/mock_twitter_mentions.json and returns
FeedbackItemCreate objects — same data contract as all other connectors,
so the rest of the pipeline never needs to know this platform is simulated.

Live Twitter API v2 is out of scope due to API cost constraints.
platform_connections.status = 'simulated' is set in the DB accordingly.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from backend.connectors.base_connector import BaseConnector
from backend.models.models import FeedbackItemCreate

logger = logging.getLogger(__name__)

_MOCK_DATA_PATH = Path(__file__).parent.parent / "data" / "mock_twitter_mentions.json"


class TwitterConnector(BaseConnector):
    """
    SIMULATED connector for Twitter/X mentions.
    Reads from mock_twitter_mentions.json (populated in Phase 2).
    Live Twitter API v2 is out of scope due to API cost constraints.
    """

    platform = "twitter"
    status = "simulated"

    async def fetch_feedback(self, business_id: str) -> List[FeedbackItemCreate]:
        """
        Load all mentions from the mock JSON file and return them as
        FeedbackItemCreate objects ready to be inserted into feedback_items.
        """
        try:
            raw: list[dict] = json.loads(_MOCK_DATA_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.error("Mock Twitter data file not found: %s", _MOCK_DATA_PATH)
            return []
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse mock Twitter data: %s", exc)
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
                    rating=None,         # Twitter mentions never have a star rating
                    sentiment=None,      # set by SentimentAgent in Phase 4
                    intent_category=None,  # set by SentimentAgent in Phase 4
                    external_id=entry.get("external_id"),
                    timestamp=timestamp,
                )
            )

        logger.info(
            "[SIMULATED] TwitterConnector loaded %d mentions from mock dataset",
            len(items),
        )
        return items

    async def post_reply(self, external_id: str, reply_text: str) -> bool:
        """
        Simulated post — log the reply text, return True.
        No live API call is made. The reply is recorded in the DB with status 'posted'.
        """
        logger.info(
            "[SIMULATED] TwitterConnector.post_reply | external_id=%s | reply=%r",
            external_id,
            reply_text,
        )
        return True
