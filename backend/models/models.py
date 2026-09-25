import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Shared ──────────────────────────────────────────────────────────────────

class UUIDModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Business ─────────────────────────────────────────────────────────────────

class BusinessCreate(BaseModel):
    name: str


class Business(UUIDModel):
    name: str


# ── Platform Connection ───────────────────────────────────────────────────────

class PlatformConnection(UUIDModel):
    business_id: uuid.UUID
    platform: str        # google_maps | facebook | instagram | twitter
    status: str          # live | simulated
    credentials_ref: Optional[str] = None


# ── Feedback Item ─────────────────────────────────────────────────────────────

class FeedbackItemCreate(BaseModel):
    business_id: uuid.UUID
    platform: str
    author_name: Optional[str] = None
    content_text: str
    rating: Optional[int] = None
    sentiment: Optional[str] = None
    intent_category: Optional[str] = None
    external_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class FeedbackItem(UUIDModel, FeedbackItemCreate):
    pass


# ── Reply ─────────────────────────────────────────────────────────────────────

class ReplyCreate(BaseModel):
    feedback_item_id: uuid.UUID
    generated_text: str


class Reply(UUIDModel, ReplyCreate):
    status: str = "pending"          # pending | approved | edited | posted
    toxicity_flagged: bool = False
    posted_at: Optional[datetime] = None


class ReplyUpdate(BaseModel):
    generated_text: Optional[str] = None
    status: Optional[str] = None


# ── Suggestion ────────────────────────────────────────────────────────────────

class SuggestionCreate(BaseModel):
    business_id: uuid.UUID
    suggestion_text: str
    evidence_quotes: Optional[list[dict]] = None
    source_reference: Optional[str] = None


class Suggestion(UUIDModel, SuggestionCreate):
    pass
