# EngageSphere

AI-powered multi-platform customer engagement system for business owners.

EngageSphere ingests customer reviews and comments from **Google Maps, Facebook, Instagram, and Twitter**, classifies them locally using free NLP models, and uses an LLM-powered Reply-Generation Agent to draft brand-appropriate replies for owner approval. A Suggestion Agent synthesises feedback across all channels into actionable, evidence-backed improvement recommendations — everything from a single unified dashboard.

**Live platforms:** Facebook, Instagram (Meta Graph API)
**Simulated platforms:** Google Maps, Twitter (mock JSON datasets — API constraints)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python, async) |
| Frontend | Next.js 15 + Tailwind CSS + TypeScript |
| Database | Supabase (Postgres) |
| Vector Store | Pinecone |
| LLM — generation | Groq (Llama 3.3 70B) → Gemini → OpenRouter (failover) |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest` (local) |
| Intent / category | `facebook/bart-large-mnli` zero-shot (local) |
| Safety / toxicity | `unitary/toxic-bert` (local) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |

All classification runs **fully locally** — no API calls, no rate limits, no cost.

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # fill in your API keys
python startup_check.py         # validate environment before first run
uvicorn main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 2. Database schema

Paste `backend/database/schema.sql` into the Supabase SQL Editor and run it.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Visit http://localhost:3000

---

## First-run setup (after both servers are running)

```bash
# 1. Create a business row in Supabase, note the UUID
#    INSERT INTO businesses (name) VALUES ('The Daily Grind') RETURNING id;

# 2. Seed business facts into Pinecone (replace UUID)
curl -X POST http://localhost:8000/api/business/seed \
  -H "Content-Type: application/json" \
  -d '{"business_id":"YOUR_UUID","business_name":"The Daily Grind",...}'

# 3. Seed the best-practices knowledge base (one-time)
curl -X POST http://localhost:8000/api/suggestions/seed-kb

# 4. Open the dashboard, enter the business UUID, click "Ingest + Generate Replies"
```

See `DEMO_RUNBOOK.md` for the full step-by-step demo guide.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/ingest` | Run all connectors, upsert + classify feedback |
| POST | `/api/classify` | Batch-classify unclassified items |
| GET | `/api/feedback/` | List feedback (filter by platform, sentiment) |
| GET | `/api/feedback/{id}` | Single feedback item |
| POST | `/api/replies/generate` | Generate AI replies for pending items |
| GET | `/api/replies/` | List replies (filter by status) |
| PATCH | `/api/replies/{id}` | Approve or edit a reply |
| POST | `/api/replies/{id}/post` | Post approved reply to platform |
| GET | `/api/suggestions/` | List suggestions |
| POST | `/api/suggestions/generate` | Run Suggestion Agent |
| POST | `/api/suggestions/seed-kb` | Seed best-practices KB into Pinecone |
| POST | `/api/business/seed` | Seed business facts into Pinecone |
| GET | `/api/business/seed/verify` | Verify RAG retrieval is working |
| GET | `/health` | Health check |

---

## Project Structure

```
EngageSphere/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── startup_check.py        ← pre-demo environment validator
│   ├── .env.example
│   ├── agents/
│   │   ├── sentiment_agent.py  ← BERT + BART + toxic-bert (all local)
│   │   ├── reply_agent.py      ← LLM + RAG reply generation
│   │   └── suggestion_agent.py ← RAG-powered suggestion synthesis
│   ├── connectors/
│   │   ├── base_connector.py
│   │   ├── facebook_connector.py    ← live (Meta Graph API)
│   │   ├── instagram_connector.py   ← live (Meta Graph API)
│   │   ├── google_maps_connector.py ← simulated (mock JSON)
│   │   └── twitter_connector.py     ← simulated (mock JSON)
│   ├── routers/
│   │   ├── ingest.py / classify.py / feedback.py
│   │   ├── replies.py / suggestions.py / business.py
│   ├── services/
│   │   ├── llm_service.py      ← Groq → Gemini → OpenRouter failover
│   │   └── pinecone_service.py ← embed + upsert + query
│   ├── data/
│   │   ├── mock_google_maps_reviews.json
│   │   ├── mock_twitter_mentions.json
│   │   ├── seed_business_info.json  ← "The Daily Grind" dummy business facts
│   │   └── best_practices_kb.json  ← 18 best-practice documents for RAG
│   └── database/
│       └── schema.sql
├── frontend/
│   └── src/
│       ├── app/ (page.tsx, dashboard/page.tsx, layout.tsx)
│       ├── components/ (FeedbackFeed, ReplyCard, SentimentChart,
│       │                SuggestionsPanel, PlatformFilterTabs)
│       └── lib/ (api.ts, types.ts, business-context.tsx)
├── DEMO_RUNBOOK.md             ← step-by-step demo guide
└── files/                      ← project documentation
    ├── PRD.md / Architecture.md / Design.md
    ├── Phases.md / Rules.md / Memory.md
```

---

## Build Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Scaffolding & Database | ✅ |
| 2 | Mock Data Connectors (Google Maps, Twitter) | ✅ |
| 3 | Live Connectors (Facebook, Instagram) | ✅ |
| 4 | Sentiment + Intent Classification (local BERT/BART) | ✅ |
| 5+6 | AI Reply-Generation + Approval Workflow | ✅ |
| 7 | Suggestion Agent (RAG-powered) | ✅ |
| 8 | Unified Dashboard (Frontend) | ✅ |
| 9 | Polish, Testing & Demo Prep | ✅ |
"# engagesphere" 
