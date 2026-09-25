"""
AI Reply-Generation Agent.

Pipeline per feedback item:
  1. Skip spam — items classified as spam get no reply (but stay visible in dashboard)
  2. RAG retrieval — pull relevant business-info chunks from Pinecone
                     (hours, policies, menu, etc.) to ground the reply
  3. LLM generation — Groq → Gemini → OpenRouter failover chain
  4. Toxicity check — every generated reply passes through toxic-bert before
                      entering the approval queue; flagged replies are marked
                      toxicity_flagged=True but NOT discarded (owner must review)

Rules enforced (from Rules.md):
  - Never fabricate business facts not present in RAG context
  - Never argue with, mock, or escalate against a customer
  - Negative feedback must acknowledge the concern
  - Replies default to pending (human approval before posting)
  - Spam items → no reply generated
"""

import logging
from typing import Optional

from backend.agents.sentiment_agent import sentiment_agent
from backend.services.llm_service import llm_service
from backend.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)

_BUSINESS_INFO_NAMESPACE = "business-info"

_SYSTEM_PROMPT = """You are a professional customer relations representative for a local coffee shop.
Your job is to write warm, genuine, brand-appropriate replies to customer reviews and comments.

Guidelines you must always follow:
- Keep replies concise (2-4 sentences), friendly, and conversational — not corporate or robotic
- For positive feedback: express genuine gratitude and reinforce what the customer enjoyed
- For negative feedback: sincerely acknowledge the concern, apologise where appropriate,
  and mention a concrete intention to improve — never be dismissive or defensive
- For questions: answer directly using only facts provided in the business context below;
  if the answer is not in the context, invite the customer to contact the business directly
- Never fabricate business information (hours, prices, policies) not provided in the context
- Never argue with, mock, or belittle a customer regardless of their tone
- Do not use filler phrases like "We value your feedback" or "Thank you for your patronage"
- Sign off naturally — no need for a formal sign-off unless it fits the tone
- Write in plain English, no markdown formatting"""


def _build_prompt(
    feedback_text: str,
    sentiment: str,
    intent: str,
    rag_context: str,
) -> str:
    context_block = (
        f"Business context (use only these facts if relevant):\n{rag_context}\n\n"
        if rag_context.strip()
        else ""
    )
    return (
        f"{context_block}"
        f"Customer feedback (sentiment: {sentiment}, category: {intent}):\n"
        f"\"{feedback_text}\"\n\n"
        f"Write a reply to this customer:"
    )


class ReplyAgent:
    """
    Generates AI replies for feedback items using LLM + RAG.
    Uses the module-level llm_service and pinecone_service singletons.
    """

    async def generate_reply(
        self,
        feedback_text: str,
        sentiment: str,
        intent: str,
        business_id: str,
    ) -> Optional[dict]:
        """
        Generate a reply for a single feedback item.

        Returns a dict:
            {
                "text": str,            # the generated reply
                "toxicity_flagged": bool # True if toxic-bert flagged it
            }
        Returns None if:
          - intent is "spam" (no reply should be generated)
          - all LLM providers fail
        """
        # Rule: never generate replies for spam
        if intent == "spam":
            logger.info("Skipping reply generation — item classified as spam")
            return None

        # Step 1: RAG — retrieve relevant business-info chunks
        rag_chunks = await pinecone_service.query(
            namespace=_BUSINESS_INFO_NAMESPACE,
            query_text=feedback_text,
            top_k=4,
        )
        rag_context = "\n".join(
            chunk.get("text", "") for chunk in rag_chunks if chunk.get("text")
        )

        # Step 2: Build prompt and call LLM
        prompt = _build_prompt(feedback_text, sentiment, intent, rag_context)
        generated = await llm_service.generate(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
        )

        if not generated:
            logger.error(
                "Reply generation failed for feedback (sentiment=%s, intent=%s): all LLM providers exhausted",
                sentiment,
                intent,
            )
            return None

        # Step 3: Toxicity check — flag but never silently discard
        is_toxic = await sentiment_agent.check_toxicity(generated)
        if is_toxic:
            logger.warning(
                "Generated reply flagged as toxic — marking for manual review. "
                "Preview: %s",
                generated[:100],
            )

        return {
            "text": generated,
            "toxicity_flagged": is_toxic,
        }

    async def generate_replies_for_business(
        self,
        business_id: str,
        feedback_items: list[dict],
    ) -> list[dict]:
        """
        Batch generate replies for a list of feedback item dicts.
        Each dict must have: id, content_text, sentiment, intent_category.

        Returns a list of result dicts:
            {
                "feedback_item_id": str,
                "text": str | None,
                "toxicity_flagged": bool,
                "skipped": bool,   # True if spam or generation failed
            }
        """
        results = []
        for item in feedback_items:
            item_id = str(item["id"])
            text = item.get("content_text", "")
            sentiment = item.get("sentiment") or "neutral"
            intent = item.get("intent_category") or "question"

            result = await self.generate_reply(
                feedback_text=text,
                sentiment=sentiment,
                intent=intent,
                business_id=business_id,
            )

            if result is None:
                results.append({
                    "feedback_item_id": item_id,
                    "text": None,
                    "toxicity_flagged": False,
                    "skipped": True,
                    "error": f"intent={intent} — spam skipped or all LLM providers failed",
                })
            else:
                results.append({
                    "feedback_item_id": item_id,
                    "text": result["text"],
                    "toxicity_flagged": result["toxicity_flagged"],
                    "skipped": False,
                    "error": None,
                })

        return results


# Module-level singleton
reply_agent = ReplyAgent()
