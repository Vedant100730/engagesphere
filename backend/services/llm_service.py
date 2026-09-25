"""
LLM service — single generate() interface with a three-tier failover chain.

Priority order: Groq (Llama 3.3 70B) → Gemini (gemini-1.5-flash) → OpenRouter (free tier)

Rules (from Rules.md):
  - All LLM calls anywhere in the codebase go through this module only
  - Rate-limit errors trigger fallback, not immediate failure
  - Every external call is wrapped in try/except with clear logging
"""

import logging
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Model identifiers
_GROQ_MODEL = "qwen/qwen3.8-27b"
_GEMINI_MODEL = "gemini-1.5-flash"
_OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

_GROQ_API_BASE = "https://api.groq.com/openai/v1"
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
_OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# Groq / OpenRouter rate-limit HTTP status
_RATE_LIMIT_STATUS = 429


class LLMService:
    """
    Provides a single generate() interface backed by a three-tier failover chain.
    Rate-limit and API errors trigger automatic fallback to the next provider.
    Returns None only if all three providers fail.
    """

    async def generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Generate text using the failover chain: Groq → Gemini → OpenRouter.
        Returns the generated string, or None if all providers fail.
        """
        result = await self._try_groq(prompt, system_prompt)
        if result is not None:
            return result

        logger.warning("Groq failed or unavailable — falling back to Gemini")
        result = await self._try_gemini(prompt, system_prompt)
        if result is not None:
            return result

        logger.warning("Gemini failed or unavailable — falling back to OpenRouter")
        result = await self._try_openrouter(prompt, system_prompt)
        if result is not None:
            return result

        logger.error("All LLM providers failed. Prompt prefix: %s", prompt[:120])
        return None

    # ── Groq ──────────────────────────────────────────────────────────────────

    async def _try_groq(self, prompt: str, system_prompt: str) -> Optional[str]:
        if not settings.GROQ_API_KEY:
            logger.info("GROQ_API_KEY not set — skipping Groq")
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{_GROQ_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": _GROQ_MODEL,
                        "messages": _build_messages(system_prompt, prompt),
                        "temperature": 0.7,
                        "max_tokens": 512,
                    },
                )
                if resp.status_code == _RATE_LIMIT_STATUS:
                    logger.warning("Groq rate-limit hit (429)")
                    return None
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error("Groq request failed: %s", exc)
            return None

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def _try_gemini(self, prompt: str, system_prompt: str) -> Optional[str]:
        if not settings.GEMINI_API_KEY:
            logger.info("GEMINI_API_KEY not set — skipping Gemini")
            return None
        try:
            # Gemini REST API — generateContent endpoint
            url = (
                f"{_GEMINI_API_BASE}/models/{_GEMINI_MODEL}:generateContent"
                f"?key={settings.GEMINI_API_KEY}"
            )
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                contents.append({"role": "model", "parts": [{"text": "Understood."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json={"contents": contents})
                if resp.status_code == _RATE_LIMIT_STATUS:
                    logger.warning("Gemini rate-limit hit (429)")
                    return None
                resp.raise_for_status()
                candidates = resp.json().get("candidates", [])
                if not candidates:
                    logger.warning("Gemini returned empty candidates")
                    return None
                return (
                    candidates[0]["content"]["parts"][0]["text"].strip()
                )
        except Exception as exc:
            logger.error("Gemini request failed: %s", exc)
            return None

    # ── OpenRouter ────────────────────────────────────────────────────────────

    async def _try_openrouter(self, prompt: str, system_prompt: str) -> Optional[str]:
        if not settings.OPENROUTER_API_KEY:
            logger.info("OPENROUTER_API_KEY not set — skipping OpenRouter")
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{_OPENROUTER_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://engagesphere.app",
                        "X-Title": "EngageSphere",
                    },
                    json={
                        "model": _OPENROUTER_MODEL,
                        "messages": _build_messages(system_prompt, prompt),
                        "temperature": 0.7,
                        "max_tokens": 512,
                    },
                )
                if resp.status_code == _RATE_LIMIT_STATUS:
                    logger.warning("OpenRouter rate-limit hit (429)")
                    return None
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error("OpenRouter request failed: %s", exc)
            return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_messages(system_prompt: str, user_prompt: str) -> list[dict]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return messages


# Module-level singleton
llm_service = LLMService()
