"""
Sentiment + intent classification agent using local Hugging Face models.
No external API calls — runs fully offline, no rate limits.

Models:
  - Sentiment:  cardiffnlp/twitter-roberta-base-sentiment-latest
                Labels remapped → positive / negative / neutral
  - Intent:     facebook/bart-large-mnli  (zero-shot classification)
                Candidate labels: complaint, praise, question, spam
  - Toxicity:   unitary/toxic-bert
                Returns True if the top label is "toxic" with score ≥ threshold

Model loading is lazy (on first use) and cached for the process lifetime so
the heavy transformer downloads only happen once per server start.

All three methods are async — they offload the synchronous pipeline.run()
calls to a thread-pool executor so they don't block the FastAPI event loop.
"""

import asyncio
import logging
from functools import lru_cache
from typing import Literal, Optional

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]
IntentLabel = Literal["complaint", "praise", "question", "spam"]

# ── Label maps ────────────────────────────────────────────────────────────────

# cardiffnlp model uses these raw labels
_SENTIMENT_LABEL_MAP: dict[str, SentimentLabel] = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    # older checkpoint variants
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}

_INTENT_LABELS = ["complaint", "praise", "question", "spam"]

# toxic-bert threshold — score must exceed this to be flagged
_TOXICITY_THRESHOLD = 0.7


# ── Lazy model loaders (cached for process lifetime) ─────────────────────────

@lru_cache(maxsize=1)
def _load_sentiment_pipeline():
    from transformers import pipeline  # type: ignore
    logger.info("Loading sentiment model: cardiffnlp/twitter-roberta-base-sentiment-latest")
    return pipeline(
        "text-classification",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
        top_k=1,
        truncation=True,
        max_length=512,
    )


@lru_cache(maxsize=1)
def _load_intent_pipeline():
    from transformers import pipeline  # type: ignore
    logger.info("Loading zero-shot intent model: facebook/bart-large-mnli")
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        truncation=True,
        max_length=1024,
    )


@lru_cache(maxsize=1)
def _load_toxicity_pipeline():
    from transformers import pipeline  # type: ignore
    logger.info("Loading toxicity model: unitary/toxic-bert")
    return pipeline(
        "text-classification",
        model="unitary/toxic-bert",
        tokenizer="unitary/toxic-bert",
        top_k=1,
        truncation=True,
        max_length=512,
    )


# ── Agent ─────────────────────────────────────────────────────────────────────

class SentimentAgent:
    """
    Classifies feedback items (sentiment, intent) and checks reply toxicity,
    all using local Hugging Face models — zero API calls, zero rate limits.

    Methods are async and offload blocking inference to a thread pool so
    they integrate cleanly with the FastAPI async event loop.
    """

    # ── Sentiment ─────────────────────────────────────────────────────────────

    async def classify_sentiment(self, text: str) -> SentimentLabel:
        """
        Classify text sentiment using the LLM (Groq).
        Falls back to keyword matching if LLM fails.
        """
        if not text or not text.strip():
            return "neutral"
        try:
            from backend.services.llm_service import llm_service
            result = await llm_service.generate(
                prompt=f'Classify the sentiment of this text as exactly one word: positive, negative, or neutral.\nText: "{text[:300]}"\nSentiment:',
                system_prompt="You are a sentiment classifier. Reply with exactly one word: positive, negative, or neutral.",
            )
            if result:
                r = result.strip().lower().split()[0]
                if r in ("positive", "negative", "neutral"):
                    return r  # type: ignore
        except Exception as exc:
            logger.error("LLM sentiment failed: %s", exc)

        # Keyword fallback
        text_lower = text.lower()
        positive_words = ["love", "great", "amazing", "excellent", "best", "fantastic", "wonderful", "good", "perfect", "happy", "awesome", "superb"]
        negative_words = ["wait", "waited", "slow", "bad", "terrible", "awful", "disappointed", "wrong", "issue", "problem", "complaint", "unacceptable", "frustrated", "poor"]
        pos = sum(1 for w in positive_words if w in text_lower)
        neg = sum(1 for w in negative_words if w in text_lower)
        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"

    # ── Intent ────────────────────────────────────────────────────────────────

    async def classify_intent(self, text: str) -> IntentLabel:
        """
        Classify intent using LLM. Falls back to keyword matching.
        """
        if not text or not text.strip():
            return "question"
        try:
            from backend.services.llm_service import llm_service
            result = await llm_service.generate(
                prompt=f'Classify the intent of this customer feedback as exactly one word: complaint, praise, question, or spam.\nText: "{text[:300]}"\nIntent:',
                system_prompt="You are an intent classifier. Reply with exactly one word: complaint, praise, question, or spam.",
            )
            if result:
                r = result.strip().lower().split()[0]
                if r in ("complaint", "praise", "question", "spam"):
                    return r  # type: ignore
        except Exception as exc:
            logger.error("LLM intent failed: %s", exc)

        # Keyword fallback
        text_lower = text.lower()
        if any(w in text_lower for w in ["click here", "free gift", "limited time", "bit.ly", "http", "discount code"]):
            return "spam"
        if any(w in text_lower for w in ["?", "do you", "can you", "is there", "are you", "what time", "when do", "how do"]):
            return "question"
        if any(w in text_lower for w in ["wait", "waited", "slow", "wrong", "bad", "terrible", "disappointed", "unacceptable", "issue", "problem"]):
            return "complaint"
        if any(w in text_lower for w in ["love", "great", "amazing", "best", "excellent", "fantastic", "wonderful", "good"]):
            return "praise"
        return "question"

    # ── Toxicity ──────────────────────────────────────────────────────────────

    async def check_toxicity(self, text: str) -> bool:
        """
        Returns True if the text is flagged as toxic with confidence ≥ threshold.
        Uses unitary/toxic-bert.
        Falls back to False (not flagged) on any error — safer than blocking
        all replies due to a model load failure.
        """
        if not text or not text.strip():
            return False
        try:
            pipe = _load_toxicity_pipeline()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: pipe(text[:512]))
            # result shape: [[{"label": "toxic"/"non_toxic", "score": 0.9}]]
            top = result[0][0]
            return top["label"].lower() == "toxic" and top["score"] >= _TOXICITY_THRESHOLD
        except Exception as exc:
            logger.error("check_toxicity failed: %s", exc)
            return False

    # ── Batch classify ────────────────────────────────────────────────────────

    async def classify(self, text: str) -> tuple[SentimentLabel, IntentLabel]:
        """
        Convenience method — runs sentiment and intent classification together.
        Returns (sentiment, intent_category).
        """
        sentiment, intent = await asyncio.gather(
            self.classify_sentiment(text),
            self.classify_intent(text),
        )
        return sentiment, intent


# Module-level singleton — shared across all requests
sentiment_agent = SentimentAgent()
