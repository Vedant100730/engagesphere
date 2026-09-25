# Phases.md — EngageSphere

Breaking the build into manageable, independently completable phases.

## Phase 1 — Project Scaffolding & Database
- FastAPI backend folder structure (routers, models, connectors, agents, services)
- Next.js frontend scaffolding (Tailwind, TypeScript configured)
- Postgres schema: businesses, platform_connections, feedback_items, replies, suggestions
- `.env.example` with placeholder keys for all services

## Phase 2 — Mock Data Connectors (Google Maps + Twitter)
- Create `mock_google_maps_reviews.json` and `mock_twitter_mentions.json` sample datasets
- Build `google_maps_connector.py` and `twitter_connector.py` to read from these mock files and insert into `feedback_items` with `platform_connections.status = 'simulated'`
- No live API calls in this phase

## Phase 3 — Live Connectors (Facebook + Instagram)
- Set up a dummy Facebook Page + Instagram Business account
- Meta Developer App in development mode, connected to these dummy assets
- `facebook_connector.py` and `instagram_connector.py`: fetch comments via Graph API, insert into `feedback_items` with `platform_connections.status = 'live'`
- Basic reply-posting function (post a reply back to a comment) for both

## Phase 4 — Sentiment Classification (BERT)
- Integrate local BERT sentiment model (`sentiment_agent.py`)
- Batch-classify all `feedback_items` (across all platforms) on ingestion
- Store sentiment result per item

## Phase 5 — AI Reply-Generation Agent
- `reply_agent.py`: LLM-based reply generation per feedback item
- RAG grounding: business info (hours, policies, etc.) stored/embedded in Pinecone, retrieved during generation
- Failover chain: Gemini → Groq → OpenRouter (via `llm_service.py`)
- Store generated reply in `replies` table with status `pending`

## Phase 6 — Approval Workflow + Posting
- API endpoints to approve/edit a pending reply
- On approval: call the relevant connector's post-reply function (live for Facebook/Instagram, log-only for simulated platforms)
- Update `replies.status` and `posted_at`

## Phase 7 — Suggestion Agent (RAG-powered)
- Marketing/business best-practices knowledge base chunked and embedded into Pinecone (separate namespace)
- `suggestion_agent.py`: aggregate feedback across all platforms, extract recurring themes, retrieve relevant best-practice guidance, generate suggestions with evidence quotes + cited source
- Store in `suggestions` table

## Phase 8 — Unified Dashboard (Frontend)
- Landing/connect page
- Dashboard: feedback feed with platform filter tabs (All/Google Maps/Facebook/Instagram/Twitter), sentiment chart, reply cards (with approve/edit UI), suggestions panel
- Wire up to backend endpoints

## Phase 9 — Polish, Testing & Demo Prep
- End-to-end test with dummy business across all 4 platforms (2 live, 2 simulated)
- Verify approval → posting flow works live on Facebook/Instagram
- Prepare talking points on which platforms are live vs. simulated, and why
- Final UI polish and responsiveness check

**Rule for each phase:** complete and verify one phase before starting the next. Each phase should be given to the AI tool as its own focused task/prompt to avoid scope overload and rate-limit issues.
