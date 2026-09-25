"""
RAG-powered Suggestion Agent.

Pipeline:
  1. Aggregate — pull all classified feedback for the business from the DB
  2. Theme extraction — group feedback by intent_category and sentiment,
     identify recurring keywords/phrases across the corpus
  3. RAG retrieval — for each theme, query the "best-practices" Pinecone
     namespace to retrieve relevant marketing/service-improvement guidance
  4. LLM synthesis — generate an actionable, evidence-backed suggestion
     for each theme, grounding it in both the real customer quotes and the
     retrieved best-practice chunks
  5. Persist — store each suggestion in the suggestions table

Rules (from Rules.md):
  - Suggestions must be evidence-backed (real quotes from feedback)
  - Source reference must cite the retrieved best-practice document
  - Uses llm_service (Groq → Gemini → OpenRouter failover)
  - Uses pinecone_service for best-practices RAG
"""

import logging
from collections import Counter
from typing import Any, Optional

from backend.services.llm_service import llm_service
from backend.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)

_BEST_PRACTICES_NAMESPACE = "best-practices"

_SYSTEM_PROMPT = """You are a business improvement consultant helping a small independent coffee shop owner.
Your job is to analyse real customer feedback and produce a single, specific, actionable suggestion.

Guidelines:
- Be concrete and direct — tell the owner exactly what to do, not vague advice like "improve service"
- Ground every suggestion in the evidence quotes provided — do not invent problems not present in the data
- Reference the best-practice context provided to support your recommendation
- Keep the suggestion to 2-3 sentences maximum
- Do not use bullet points or headers — write in plain prose
- Speak directly to the owner ("Consider...", "We recommend...", "Your customers are telling you...")
- Do not repeat the customer quotes verbatim in the suggestion text — paraphrase and synthesise"""


# ── Theme definitions ─────────────────────────────────────────────────────────
# Each theme maps to: a search query for RAG, and the intent/sentiment signals
# that indicate this theme is present in the feedback.

_THEMES: list[dict[str, Any]] = [
    {
        "id": "wait_times",
        "label": "Wait times and speed of service",
        "rag_query": "how to reduce customer wait times in a coffee shop",
        "keywords": ["wait", "waited", "slow", "queue", "long", "minutes", "rush"],
    },
    {
        "id": "order_accuracy",
        "label": "Order accuracy and consistency",
        "rag_query": "improving order accuracy and consistency in a café",
        "keywords": ["wrong", "incorrect", "order", "mistake", "instead", "inconsistent"],
    },
    {
        "id": "staff_knowledge",
        "label": "Staff product knowledge and training",
        "rag_query": "staff training product knowledge specialty coffee shop",
        "keywords": ["confused", "didn't know", "unsure", "training", "knowledge", "difference"],
    },
    {
        "id": "allergen_info",
        "label": "Allergen and dietary information",
        "rag_query": "allergen information transparency food safety café",
        "keywords": ["allergy", "allergen", "nut", "dairy", "vegan", "gluten", "intolerant", "lactose"],
    },
    {
        "id": "crowd_management",
        "label": "Crowd and queue management",
        "rag_query": "queue management busy period strategies for independent café",
        "keywords": ["packed", "crowded", "chaos", "cutting", "queue", "busy", "saturday", "weekend"],
    },
    {
        "id": "menu_options",
        "label": "Menu variety and dietary options",
        "rag_query": "expanding café menu vegan plant-based options customer demand",
        "keywords": ["vegan", "plant-based", "option", "menu", "choice", "sugar-free", "decaf", "reusable"],
    },
    {
        "id": "positive_reinforcement",
        "label": "Strengths to maintain and promote",
        "rag_query": "leveraging positive customer reviews for coffee shop marketing",
        "keywords": ["love", "best", "amazing", "great", "excellent", "fantastic", "recommend", "perfect"],
    },
    {
        "id": "atmosphere_workspace",
        "label": "Atmosphere and workspace experience",
        "rag_query": "creating a welcoming workspace environment in a coffee shop",
        "keywords": ["wifi", "wi-fi", "work", "laptop", "noise", "music", "loud", "quiet", "atmosphere"],
    },
    {
        "id": "accessibility",
        "label": "Physical accessibility",
        "rag_query": "improving physical accessibility in a small café",
        "keywords": ["step", "pushchair", "wheelchair", "accessible", "entrance", "door"],
    },
]


class SuggestionAgent:
    """
    Generates actionable business improvement suggestions from aggregated feedback,
    grounded in real customer quotes and best-practice RAG context.
    """

    async def generate_suggestions(
        self,
        business_id: str,
        feedback_items: list[dict],
    ) -> list[dict]:
        """
        Analyse all feedback for the business and return a list of suggestion dicts:
            {
                "suggestion_text": str,
                "evidence_quotes": list[{quote, platform, author}],
                "source_reference": str | None,
                "theme_id": str,
                "theme_label": str,
            }

        Only themes with at least 2 matching feedback items are surfaced
        (avoids generating suggestions from a single data point).
        """
        if not feedback_items:
            logger.info("SuggestionAgent: no feedback items — nothing to analyse")
            return []

        # Filter out spam items
        usable = [
            fi for fi in feedback_items
            if fi.get("intent_category") != "spam"
        ]
        logger.info(
            "SuggestionAgent: analysing %d feedback items (from %d total) for business %s",
            len(usable), len(feedback_items), business_id,
        )

        suggestions = []

        for theme in _THEMES:
            matched = _match_theme(usable, theme)
            if len(matched) < 2:
                # Not enough signal for this theme — skip
                continue

            logger.info(
                "Theme '%s': %d matching items — generating suggestion",
                theme["label"], len(matched),
            )

            suggestion = await self._synthesise_suggestion(theme, matched)
            if suggestion:
                suggestions.append(suggestion)

        logger.info(
            "SuggestionAgent complete: %d suggestions generated for business %s",
            len(suggestions), business_id,
        )
        return suggestions

    async def _synthesise_suggestion(
        self,
        theme: dict[str, Any],
        matched_items: list[dict],
    ) -> Optional[dict]:
        """Generate a single suggestion for a theme from its matching feedback items."""

        # Build evidence quotes (up to 3, prefer negative/complaint for actionable themes,
        # positive for the reinforcement theme)
        if theme["id"] == "positive_reinforcement":
            evidence_items = [
                fi for fi in matched_items
                if fi.get("sentiment") == "positive"
            ][:3] or matched_items[:3]
        else:
            evidence_items = sorted(
                matched_items,
                key=lambda x: (x.get("sentiment") != "negative", x.get("intent_category") != "complaint"),
            )[:3]

        evidence_quotes = [
            {
                "quote": fi["content_text"],
                "platform": fi.get("platform", "unknown"),
                "author": fi.get("author_name"),
            }
            for fi in evidence_items
        ]

        # RAG — retrieve best-practice guidance for this theme
        bp_chunks = await pinecone_service.query(
            namespace=_BEST_PRACTICES_NAMESPACE,
            query_text=theme["rag_query"],
            top_k=3,
        )
        bp_context = "\n".join(
            chunk.get("text", "") for chunk in bp_chunks if chunk.get("text")
        )
        source_ref = next(
            (chunk.get("source") for chunk in bp_chunks if chunk.get("source")),
            None,
        )

        # Build prompt
        quotes_block = "\n".join(
            f'- "{q["quote"]}" ({q["platform"]}, {q["author"] or "anonymous"})'
            for q in evidence_quotes
        )
        bp_block = (
            f"\nRelevant best-practice guidance:\n{bp_context}\n"
            if bp_context.strip()
            else ""
        )

        prompt = (
            f"Theme: {theme['label']}\n\n"
            f"Customer feedback evidence ({len(matched_items)} items matched, showing top {len(evidence_quotes)}):\n"
            f"{quotes_block}\n"
            f"{bp_block}\n"
            f"Write one actionable suggestion for the business owner based on this evidence:"
        )

        generated = await llm_service.generate(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
        )

        if not generated:
            logger.error("LLM failed to generate suggestion for theme '%s'", theme["label"])
            return None

        return {
            "suggestion_text": generated,
            "evidence_quotes": evidence_quotes,
            "source_reference": source_ref,
            "theme_id": theme["id"],
            "theme_label": theme["label"],
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _match_theme(feedback_items: list[dict], theme: dict[str, Any]) -> list[dict]:
    """
    Return all feedback items whose content_text contains at least one
    keyword from the theme's keyword list (case-insensitive).
    """
    keywords = [kw.lower() for kw in theme["keywords"]]
    matched = []
    for fi in feedback_items:
        text = (fi.get("content_text") or "").lower()
        if any(kw in text for kw in keywords):
            matched.append(fi)
    return matched


# Module-level singleton
suggestion_agent = SuggestionAgent()
