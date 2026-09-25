"""
Pinecone vector-store service for RAG.

Namespaces:
  - "business-info"   — business facts (hours, policies, menu) used by ReplyAgent
  - "best-practices"  — marketing / service knowledge base used by SuggestionAgent

Embeddings are generated locally using sentence-transformers (no API cost).
The client is initialised lazily on first use so the server starts even when
PINECONE_API_KEY is not yet configured.
"""

import asyncio
import logging
from functools import lru_cache
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

_EMBED_MODEL = "all-MiniLM-L6-v2"   # fast, 384-dim, good quality for retrieval


# ── Lazy loaders ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_embedder():
    from sentence_transformers import SentenceTransformer  # type: ignore
    logger.info("Loading embedding model: %s", _EMBED_MODEL)
    return SentenceTransformer(_EMBED_MODEL)


@lru_cache(maxsize=1)
def _load_pinecone_index():
    from pinecone import Pinecone  # type: ignore
    if not settings.PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set")
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    logger.info("Pinecone index '%s' connected", settings.PINECONE_INDEX_NAME)
    return index


# ── Service ───────────────────────────────────────────────────────────────────

class PineconeService:
    """
    Wraps Pinecone upsert and query behind async methods.
    Embedding is done locally (sentence-transformers) — no external embedding API.
    All blocking calls are offloaded to a thread-pool executor.
    """

    async def embed(self, text: str) -> list[float]:
        """Embed a single string using the local sentence-transformers model."""
        loop = asyncio.get_event_loop()
        embedder = _load_embedder()
        vector = await loop.run_in_executor(
            None, lambda: embedder.encode(text, normalize_embeddings=True).tolist()
        )
        return vector

    async def upsert(self, namespace: str, vectors: list[dict]) -> bool:
        """
        Upsert pre-built vector dicts into the given namespace.
        Each dict must have: {"id": str, "values": list[float], "metadata": dict}
        Returns True on success, False on failure.
        """
        try:
            index = _load_pinecone_index()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: index.upsert(vectors=vectors, namespace=namespace)
            )
            logger.info("Pinecone upsert: %d vectors → namespace='%s'", len(vectors), namespace)
            return True
        except Exception as exc:
            logger.error("Pinecone upsert failed (namespace=%s): %s", namespace, exc)
            return False

    async def upsert_text(self, namespace: str, doc_id: str, text: str, metadata: Optional[dict] = None) -> bool:
        """
        Convenience method — embeds text locally then upserts to Pinecone.
        metadata is stored alongside the vector for retrieval context.
        """
        try:
            vector = await self.embed(text)
            return await self.upsert(
                namespace=namespace,
                vectors=[{
                    "id": doc_id,
                    "values": vector,
                    "metadata": {**(metadata or {}), "text": text},
                }],
            )
        except Exception as exc:
            logger.error("Pinecone upsert_text failed: %s", exc)
            return False

    async def query(
        self,
        namespace: str,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Embed query_text locally, then retrieve top-k matching chunks from Pinecone.
        Returns a list of metadata dicts from matching vectors.
        Falls back to [] on any error so callers can proceed without RAG context.
        """
        try:
            query_vector = await self.embed(query_text)
            index = _load_pinecone_index()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: index.query(
                    vector=query_vector,
                    top_k=top_k,
                    namespace=namespace,
                    include_metadata=True,
                ),
            )
            chunks = [
                match["metadata"]
                for match in result.get("matches", [])
                if match.get("metadata")
            ]
            logger.debug(
                "Pinecone query: namespace='%s' top_k=%d → %d chunks returned",
                namespace, top_k, len(chunks),
            )
            return chunks
        except Exception as exc:
            logger.error("Pinecone query failed (namespace=%s): %s", namespace, exc)
            return []


# Module-level singleton
pinecone_service = PineconeService()
