# Rules.md — EngageSphere

Boundaries and conventions for AI-assisted development on this project (for Kiro or any AI coding tool).

## Libraries & Tools — Use
- Backend: FastAPI, SQLAlchemy (async, with asyncpg for Postgres), Pydantic
- Classification (all local, via Hugging Face `transformers` + `torch`, no external API):
  - Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest`
  - Intent/category (zero-shot): `facebook/bart-large-mnli`
  - Safety/moderation: `unitary/toxic-bert`
- Embeddings: `sentence-transformers` (local) or Gemini embeddings — for RAG only
- LLM calls (generation only — replies, suggestions): Groq SDK (primary), official Gemini SDK/REST (fallback), OpenRouter REST (second fallback) — always behind a single `llm_service.py` abstraction with failover, tried in that order
- Vector store: official `pinecone` Python client
- Frontend: Next.js (App Router), Tailwind CSS, TypeScript
- Meta integration: official Graph API via HTTPS requests (no unofficial scraping libraries)

## Libraries & Tools — Avoid
- No web scraping of Facebook/Instagram/Twitter/Google outside official APIs (ToS risk)
- No unofficial/reverse-engineered API wrappers for any platform
- No client-side secret storage — all API keys/tokens stay server-side, never exposed to frontend
- No `localStorage`/`sessionStorage` for sensitive tokens

## Error Handling
- Every external API call (Meta Graph API, Gemini, Groq, OpenRouter, Pinecone) must be wrapped in try/except with clear logging
- LLM calls must use the failover chain (Gemini → Groq → OpenRouter) rather than failing outright
- Platform connector failures (e.g., Facebook token expired) must not crash the whole pipeline — log the failure, mark that platform's data as stale, and continue processing other platforms
- Rate-limit errors must trigger backoff/retry, not immediate failure

## Data & Secrets
- All credentials (API keys, access tokens) go in `.env` (git-ignored), never in `.env.example` or committed code
- `.env.example` must only ever contain placeholder values
- Mock datasets (Google Maps, Twitter) are clearly labeled as simulated in both code comments and the database (`platform_connections.status = 'simulated'`)

## AI Reply Generation Rules
- Replies must never be posted live without going through the approval/edit step by default (auto-post is opt-in, not default)
- Replies must not fabricate business facts not present in the RAG-retrieved business info — no hallucinated policies, prices, or promises
- Replies to negative feedback must acknowledge the concern and avoid dismissive or generic language
- No reply should ever argue with, mock, or escalate against a customer, regardless of the tone of their original comment
- Every generated reply must pass through the local toxicity/moderation classifier (`toxic-bert`) before entering the approval queue; any reply flagged must be marked for manual rewrite rather than silently discarded or auto-corrected
- Items classified as spam by the intent classifier should be excluded from the reply queue entirely (no reply generated), but still visible in the dashboard for the owner's awareness

## Scope Discipline
- The AI should implement one module/phase at a time as defined in `Phases.md`, not attempt the entire system in a single pass
- Do not modify the frontend UI/data contract when working on backend-only tasks, and vice versa, unless explicitly instructed
- Do not introduce new platforms, features, or dependencies not listed in `PRD.md`/`Architecture.md` without flagging it first

## Code Style
- Python: type-annotated, async/await throughout the FastAPI layer
- TypeScript: strict typing, shared types between API responses and frontend components via `lib/types.ts`
- Keep connector, agent, and service layers separate — no business logic inside route handlers beyond orchestration
