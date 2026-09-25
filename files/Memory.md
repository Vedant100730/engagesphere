# Memory.md — EngageSphere Build Progress

This file is NOT filled in at project start. Begin updating it once the AI 
tool (Kiro or otherwise) starts writing code, so that progress persists 
across chat sessions/tool switches without needing to re-read the whole 
codebase each time.

Update this file after completing each phase from `Phases.md`, or after 
any significant decision/change. Keep entries short and factual.

---

## Template for each entry

### [Date] — Phase X: <name>
- **Status:** In progress / Complete / Blocked
- **What was built:** (files/modules created or changed)
- **Key decisions made:** (e.g., chose mock dataset over live API for X)
- **Known issues / TODO:** 
- **Next step:**

---

## Progress Log

- **Next step:** Project complete — ready for demo

### [September 6, 2026] — Phase 9: Polish, Testing & Demo Prep
- **Status:** Complete
- **What was built:**
  - `backend/startup_check.py` — pre-demo environment validator; checks .env completeness, mock data files, Postgres connectivity + schema tables, Pinecone connectivity + namespace vector counts, Groq API reachability; prints go/no-go per check with colour output
  - `DEMO_RUNBOOK.md` — full step-by-step demo guide: pre-demo checklist, 10-step demo flow with talking points, common panellist Q&A, troubleshooting table
  - `README.md` — complete rewrite: full tech stack table, quick start commands, first-run setup, full API endpoint table, project structure tree, phase status table
  - `frontend/src/app/page.tsx` — polished landing page: UUID input with validation, platform badges showing Live/Simulated status, 6-feature grid, skip link
- **Key decisions made:**
  - `startup_check.py` validates Pinecone namespace vector counts (warns if business-info or best-practices are empty) — catches the most common demo-day failure before it happens
  - Landing page UUID input validates format client-side before storing — avoids confusing API 422 errors during a live demo
  - `DEMO_RUNBOOK.md` includes the exact panellist questions anticipated and scripted answers
- **Known issues / TODO:** None — project is demo-ready
- **Next step:** Project complete — ready for demo

### [September 6, 2026] — Phase 1: Project Scaffolding & Database
- **Status:** Complete
- **What was built:**
  - `backend/main.py` — FastAPI app with CORS middleware and router registration
  - `backend/config.py` — pydantic-settings `Settings` class loading all env vars
  - `backend/requirements.txt` — all dependencies pinned (FastAPI, SQLAlchemy async, Pydantic, Groq, Gemini, Pinecone, transformers, etc.)
  - `backend/.env.example` — placeholder-only (no real secrets)
  - `backend/database/db.py` — async SQLAlchemy engine + `get_db` dependency
  - `backend/database/schema.sql` — full Postgres schema: businesses, platform_connections, feedback_items, replies, suggestions (with all constraints and indexes)
  - `backend/models/models.py` — Pydantic models for all entities
  - `backend/routers/` — stub routers for feedback, replies, suggestions (returning empty lists; full implementation in Phases 4–7)
  - `backend/connectors/` — `BaseConnector` ABC + Facebook, Instagram (live stubs), Google Maps, Twitter (simulated stubs)
  - `backend/agents/` — SentimentAgent, ReplyAgent, SuggestionAgent (stubs with clear Phase 4/5/7 TODOs)
  - `backend/services/` — LLMService (3-tier failover chain: Groq→Gemini→OpenRouter, stub), PineconeService (stub)
  - `backend/data/mock_google_maps_reviews.json`, `mock_twitter_mentions.json` — empty arrays (filled in Phase 2)
  - `frontend/` — Next.js App Router + TypeScript + Tailwind CSS (create-next-app, npm packages installed)
  - `frontend/src/lib/types.ts` — all shared TypeScript types
  - `frontend/src/lib/api.ts` — typed API client
  - `frontend/src/app/page.tsx` — landing page with branding
  - `frontend/src/app/dashboard/page.tsx` — dashboard shell with filter state
  - `frontend/src/components/` — PlatformFilterTabs, FeedbackFeed, ReplyCard, SentimentChart, SuggestionsPanel
  - `.gitignore` — excludes .env, __pycache__, node_modules, venv, .next
  - `README.md` — project overview + phase table
- **Key decisions made:**
  - `feedback_items` includes `intent_category` column (for BART-MNLI classification in Phase 4)
  - `replies` includes `toxicity_flagged` boolean (for toxic-bert safety check in Phase 5)
  - `platform_connections.credentials_ref` is a reference key only — raw tokens never stored in DB
  - LLM failover order: Groq (primary) → Gemini → OpenRouter (matches Architecture.md)
  - Frontend uses `"use client"` only where needed; landing page is server component
- **Known issues / TODO:** None for Phase 1
- **Next step:** Phase 9 — Polish, testing & demo prep

### [September 6, 2026] — Phase 8: Unified Dashboard (Frontend)
- **Status:** Complete
- **What was built:**
  - `frontend/src/lib/types.ts` — added `SentimentStats`, `IngestResult`, `GenerateRepliesResult`, `GenerateSuggestionsResult`; added joined fields to `Reply`
  - `frontend/src/lib/api.ts` — full rewrite: typed imports, `buildQuery` helper, all endpoints wired (`getFeedback`, `getFeedbackItem`, `getSentimentStats`, `getReplies`, `getReply`, `updateReply`, `postReply`, `generateReplies`, `getSuggestions`, `generateSuggestions`, `ingestFeedback`, `classifyFeedback`)
  - `frontend/src/lib/business-context.tsx` — React context + `BusinessProvider` + `useBusinessId` hook; persists business_id to sessionStorage
  - `frontend/src/app/layout.tsx` — wrapped with `BusinessProvider`; updated metadata title/description
  - `frontend/src/app/dashboard/page.tsx` — live header metrics (total feedback, pending replies); business ID input + Set button; "Ingest + Generate Replies" pipeline button with step-by-step status messages; `feedKey` pattern to force child re-renders after pipeline completes
  - `frontend/src/components/FeedbackFeed.tsx` — fetches feedback + replies in parallel; builds `replyMap` keyed on `feedback_item_id`; shows intent badge + sentiment badge + star rating (filled/empty); timestamp display; updated empty state messaging; passes `onUpdate` callback to ReplyCard
  - `frontend/src/components/ReplyCard.tsx` — `onUpdate` callback to bubble reply state up; posted_at display; loading state text on buttons; error display per action
  - `frontend/src/components/SentimentChart.tsx` — live data via `getSentimentStats`; animated CSS transition bars; item count display; loading skeleton
  - `frontend/src/components/SuggestionsPanel.tsx` — live data; "Re-generate" button calls `generateSuggestions`; success count toast; quote truncation at 120 chars; source reference with book emoji; scrollable list
- **Key decisions made:**
  - `feedKey` integer bumped after pipeline run — passed as `key` prop to FeedbackFeed, SentimentChart, SuggestionsPanel — forces React to remount and refetch without a global state manager
  - Sentiment stats computed client-side from the feedback list (no extra endpoint needed)
  - business_id stored in sessionStorage (not localStorage) — clears on tab close, appropriate for a demo/dev context
  - Zero TypeScript diagnostics across all changed files
- **Known issues / TODO:** None for Phase 8
- **Next step:** Phase 9 — Polish, testing & demo prep

### [September 6, 2026] — Phase 7: Suggestion Agent (RAG-powered)
- **Status:** Complete
- **What was built:**
  - `backend/agents/suggestion_agent.py` — full pipeline: aggregate feedback → keyword theme matching (9 themes) → RAG retrieval from `best-practices` namespace → LLM synthesis per theme → returns structured suggestion dicts with evidence_quotes and source_reference
  - `backend/data/best_practices_kb.json` — 18 best-practice documents across 9 topic areas (wait times, order accuracy, staff training, allergen info, crowd management, menu/dietary options, positive reinforcement, workspace/atmosphere, accessibility, sustainability), each with a cited source
  - `backend/routers/suggestions.py` — full implementation:
    - `GET /api/suggestions/?business_id=` — list stored suggestions with pagination
    - `POST /api/suggestions/generate?business_id=` — runs agent, persists results, returns newly generated suggestions
    - `POST /api/suggestions/seed-kb` — embeds + upserts best_practices_kb.json into Pinecone `best-practices` namespace; safe to re-run
- **Key decisions made:**
  - Theme matching uses keyword presence in content_text (not sentiment/intent alone) — more accurate for multi-signal themes like allergens or accessibility
  - Minimum 2 matching feedback items required before a suggestion is generated — avoids single-data-point recommendations
  - Evidence quotes prioritise negative/complaint items for actionable themes; positive items for the positive-reinforcement theme
  - History preserved — re-running generate does not delete previous suggestions (useful for tracking improvement over time)
  - `seed-kb` is a separate endpoint from business seed — can be run once at deploy time without needing a business_id
- **Known issues / TODO:** Run `POST /api/suggestions/seed-kb` once before first `/generate` call so RAG context is available
- **Next step:** Phase 8 — Unified Dashboard (Frontend)

### [September 6, 2026] — Business Info Seed Endpoint
- **Status:** Complete
- **What was built:**
  - `backend/routers/business.py` — two endpoints:
    - `POST /api/business/seed` — accepts structured `BusinessSeedRequest` (hours, menu sections, policies, contact, about, extra), chunks by category, embeds each chunk locally with `all-MiniLM-L6-v2`, upserts to Pinecone `business-info` namespace. Vector IDs are deterministic (`{business_id}::{category}::{md5slug}`) so re-seeding overwrites, never duplicates. Returns upserted count + chunk previews.
    - `GET /api/business/seed/verify?business_id=&query=` — queries the namespace with any question and returns retrieved chunks; confirms RAG is pulling real facts before reply generation
  - `backend/data/seed_business_info.json` — complete sample facts for "The Daily Grind" dummy business: hours (Mon–Sun + holidays), full menu (hot drinks, cold drinks, seasonal specials, milk options, food with allergen info), 12 policy statements (oat milk, allergens, Wi-Fi, loyalty card, reusable cup discount, decaf, accessible entrance, sugar-free syrups), contact info, 9 extra facts
  - `backend/main.py` — registered business router at `/api/business`
- **Key decisions made:**
  - Menu split into one chunk per section (hot drinks / cold drinks / food etc.) so a question about cold brew doesn't retrieve the entire menu
  - Allergen info embedded directly into food item descriptions — most likely to be retrieved when a customer asks about allergies
  - Policies each get their own chunk — granular retrieval means a question about oat milk pulls the milk policy, not the loyalty card policy
  - Post-filter by `business_id` in metadata on verify endpoint (Pinecone metadata filtering not available on all plans)
- **Known issues / TODO:** `seed_business_info.json` business_id field intentionally omitted — caller provides it at seed time via the API body
- **Next step:** Phase 7 — Suggestion Agent (RAG-powered)

### [September 6, 2026] — Phase 5 + 6: AI Reply-Generation Agent + Approval Workflow
- **Status:** Complete
- **What was built:**
  - `backend/services/llm_service.py` — full Groq → Gemini → OpenRouter failover; each provider wrapped in try/except; 429 rate-limits trigger fallback; returns None only if all three fail
  - `backend/services/pinecone_service.py` — lazy Pinecone client init; local `sentence-transformers/all-MiniLM-L6-v2` for embeddings (no API cost); `upsert`, `upsert_text`, `query` methods; all blocking calls offloaded to thread-pool executor
  - `backend/agents/reply_agent.py` — full pipeline: spam skip → RAG retrieval (business-info namespace) → LLM generation → toxicity check; `generate_replies_for_business()` batch method; toxic replies flagged not discarded
  - `backend/routers/replies.py` — full implementation:
    - `POST /api/replies/generate?business_id=` — generates + inserts pending replies for all non-spam, reply-less items
    - `GET /api/replies/` — list with optional status filter + pagination, joins feedback_items for context
    - `GET /api/replies/{id}` — single reply with platform/author context
    - `PATCH /api/replies/{id}` — approve or edit; editing auto-sets status to 'edited'
    - `POST /api/replies/{id}/post` — posts to platform via connector (live for FB/IG, simulated for GM/TW); updates status to 'posted' + sets posted_at
- **Key decisions made:**
  - Phases 5 and 6 combined — the approval/post flow is tightly coupled to generation so splitting them would leave broken stubs
  - System prompt enforces all Rules.md constraints directly (no fabrication, no escalation, no dismissive language)
  - Pinecone namespace `business-info` for RAG context; falls back gracefully to empty context if Pinecone not configured
  - Connector map in replies.py instantiated once at module level — same instances used for both ingest and posting
- **Known issues / TODO:** `business-info` Pinecone namespace needs to be seeded with actual business facts (hours, menu, policies) before RAG grounding is meaningful
- **Next step:** Phase 7 — Suggestion Agent (RAG-powered)

### [September 6, 2026] — Phase 4: Sentiment Classification (BERT)
- **Status:** Complete
- **What was built:**
  - `backend/agents/sentiment_agent.py` — full implementation with 3 lazy-loaded local models:
    - Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest` → positive/negative/neutral
    - Intent: `facebook/bart-large-mnli` (zero-shot) → complaint/praise/question/spam
    - Toxicity: `unitary/toxic-bert` → bool flag with configurable threshold (0.7)
    - All models cached via `@lru_cache` — loaded once per server process
    - All inference offloaded to thread-pool executor via `asyncio.run_in_executor` — non-blocking
    - `classify()` convenience method runs sentiment + intent concurrently via `asyncio.gather`
  - `backend/routers/classify.py` — `POST /api/classify` batch-classifies all items where sentiment/intent_category IS NULL; safe to re-run
  - `backend/routers/ingest.py` — updated: after each connector upserts new items, `_classify_new_items()` immediately runs classification on the new IDs; ingest response now includes `classified` and `classification_failed` counts per platform
  - `backend/main.py` — registered classify router at `/api/classify`
- **Key decisions made:**
  - Lazy model loading: models are not loaded at import time — first request triggers download/load; subsequent requests use the cached pipeline
  - Spam items are classified and stored but excluded from reply queue in Phase 5 (not deleted — visible in dashboard per PRD)
  - Toxicity check is for replies only (Phase 5); classify endpoint covers feedback items only
  - Error on a single item during batch classification is caught and counted as `failed` — doesn't abort the batch
- **Known issues / TODO:** First ingest after server cold-start will be slow (model download ~1-2GB for BART); subsequent runs use cache
- **Next step:** Phase 5 — AI Reply-Generation Agent (LLM + RAG)

### [September 6, 2026] — Phase 3: Live Connectors (Facebook + Instagram)
- **Status:** Complete
- **What was built:**
  - `backend/connectors/facebook_connector.py` — fetches Page post comments via Graph API (`/{page_id}/feed` → `/{post_id}/comments`); posts replies via `/{comment_id}/comments`; full pagination, rate-limit detection, error isolation
  - `backend/connectors/instagram_connector.py` — fetches media comments via Graph API (`/{ig_user_id}/media` → `/{media_id}/comments`); posts replies via `/{comment_id}/replies`; same error-handling pattern
  - `backend/routers/ingest.py` — updated to include live connectors; live connectors only run when their tokens are present in settings (graceful skip otherwise); extracted `_run_connector()` helper to keep per-connector error isolation DRY
- **Key decisions made:**
  - Both live connectors use `httpx.AsyncClient` with explicit timeouts (20s fetch, 15s post)
  - Graph API version pinned to `v19.0` in both connectors
  - Rate-limit codes (32, 613) logged as warnings rather than hard errors — caller decides retry policy
  - Live connectors silently skip (with a log message) if their token env var is empty — no crash, no noise during local dev without real credentials
  - `_raise_for_graph_error()` is a static method on each connector (not shared util) to keep connectors self-contained per the architecture rules
- **Known issues / TODO:** Tokens must be configured in `.env` to exercise live connectors; Graph API app must be in Development mode with correct permissions
- **Next step:** Phase 4 — Sentiment + intent classification (local BERT/BART models)

### [September 6, 2026] — Phase 2: Mock Data Connectors (Google Maps + Twitter)
- **Status:** Complete
- **What was built:**
  - `backend/data/mock_google_maps_reviews.json` — 15 realistic reviews (mix of praise, complaints, questions; ratings 1–5, some null)
  - `backend/data/mock_twitter_mentions.json` — 15 mentions (mix of praise, complaints, questions, one clear spam entry for testing)
  - `backend/connectors/google_maps_connector.py` — reads mock JSON, returns `FeedbackItemCreate` list; `post_reply` logs and returns True
  - `backend/connectors/twitter_connector.py` — same pattern as Google Maps connector
  - `backend/routers/ingest.py` — `POST /api/ingest?business_id=<uuid>` runs both simulated connectors, upserts new rows into `feedback_items`, returns per-platform summary (fetched/inserted/skipped)
  - `backend/routers/feedback.py` — `GET /api/feedback/` now queries DB with optional `platform`/`sentiment` filters + pagination; `GET /api/feedback/{id}` fetches single item
  - `backend/main.py` — registered `ingest` router at `/api/ingest`
- **Key decisions made:**
  - Upsert dedup keyed on `(platform, external_id)` — re-running ingest is idempotent
  - Single connector failure during ingest is caught and logged; other platforms continue unaffected
  - Raw SQL via `sqlalchemy.text()` — consistent with existing `db.py`, no ORM models needed yet
  - Twitter mock includes one obvious spam entry (`tw_005`) to exercise the spam classifier in Phase 4
- **Known issues / TODO:** None for Phase 2
- **Next step:** Phase 3 — Facebook + Instagram live connectors via Meta Graph API

<!-- 
Add new dated entries below this line as work progresses.
Keep the most recent 5-10 entries in detail; older entries can be 
condensed into a one-line summary to keep this file from growing 
unmanageably large.
-->
