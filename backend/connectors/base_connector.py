from abc import ABC, abstractmethod
from typing import List

from backend.models.models import FeedbackItemCreate


class BaseConnector(ABC):
    """
    Abstract base class for all platform connectors.
    Each connector must implement fetch_feedback and post_reply,
    giving the rest of the pipeline a uniform interface regardless
    of whether the platform is live or simulated.
    """

    platform: str = ""
    status: str = ""  # "live" or "simulated"

    @abstractmethod
    async def fetch_feedback(self, business_id: str) -> List[FeedbackItemCreate]:
        """Fetch new reviews/comments and return as FeedbackItemCreate objects."""
        ...

    @abstractmethod
    async def post_reply(self, external_id: str, reply_text: str) -> bool:
        """
        Post a reply to the platform.
        Returns True on success, False on failure.
        Simulated connectors should log the reply and return True.
        """
        ...
