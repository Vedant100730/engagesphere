# Architecture.md — EngageSphere

## Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** Next.js + Tailwind CSS
- **Database:** Supabase (Postgres)
- **Vector store:** Pinecone (for RAG — business info grounding + knowledge base for suggestions)
- **LLM (reply/suggestion generation):** Groq (Llama 3.3 70B — primary, fastest free-tier inference, matters for a "live reply" demo), Gemini API (fallback), OpenRouter free models (second fallback)
- **Local NLP (classification — no API calls, no rate limits):**
  - Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest` (Hugging Face, local)
  - Intent/category (zero-shot): `facebook/bart-large-mnli` (Hugging Face, local) — classifies into custom categories (complaint, praise, question, spam) without training data
  - Safety/moderation: `unitary/toxic-bert` (Hugging Face, local) — flags any AI-generated reply for toxicity/inappropriateness before it's allowed to post live
- **Embeddings for RAG:** `sentence-transformers` (local, free) or Gemini embeddings — used for business-info grounding and the suggestion knowledge base
- **Platform APIs:**
  - Meta Graph API (Facebook Page comments, Instagram Business comments) — live
  - Google Business Profile API — not used live; mock dataset instead
  - Twitter API v2 — not used live; mock dataset instead

**Division of labor:** local BERT/BART models handle all classification (sentiment, intent, safety) — fast, free, unlimited volume. LLMs (Groq/Gemini/OpenRouter) are reserved only for tasks requiring generation/reasoning: writing replies and synthesizing suggestions.

## High-Level Flow
1. **Ingestion** — Platform connector modules fetch new reviews/comments (live for Facebook/Instagram, simulated read for Google Maps/Twitter from a mock dataset)
2. **Classification** — Local models classify every incoming item: sentiment (RoBERTa), and intent/category via zero-shot (BART-MNLI) — complaint, praise, question, spam. All local, no API calls, no rate limits.
3. **Reply Generation** — For each non-spam item, the AI Reply-Generation Agent (Groq primary, Gemini/OpenRouter fallback) generates a brand-appropriate reply, using RAG to pull business-specific facts (hours, policies, etc.) from Pinecone
4. **Safety Check** — Every generated reply is passed through a local toxicity/moderation classifier (toxic-bert) before it's allowed into the approval queue; flagged replies are marked for manual rewrite
5. **Review/Approve** — Generated reply appears in the dashboard for the owner to approve, edit, or auto-send (configurable)
6. **Posting** — Approved replies are posted back via the relevant platform connector (live for Facebook/Instagram; simulated/logged for Google Maps/Twitter)
7. **Aggregation & Suggestions** — All classified feedback across platforms feeds the Suggestion Agent, which extracts recurring themes and generates actionable, evidence-backed recommendations for the business owner (RAG-grounded in a marketing/best-practices knowledge base)
8. **Dashboard Display** — Unified view shows all feedback, replies, and suggestions across platforms

## Folder Structure
```
EngageSphere/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── database/
│   │   └── schema.sql
│   ├── models/
│   │   └── (Pydantic/ORM models: Business, FeedbackItem, Reply, Suggestion)
│   ├── routers/
│   │   ├── feedback.py       # endpoints to fetch/list feedback
│   │   ├── replies.py        # endpoints to generate/approve/post replies
│   │   └── suggestions.py    # endpoints to fetch suggestions
│   ├── connectors/
│   │   ├── facebook_connector.py
│   │   ├── instagram_connector.py
│   │   ├── google_maps_connector.py   # mock data reader
│   │   └── twitter_connector.py       # mock data reader
│   ├── agents/
│   │   ├── sentiment_agent.py     # local BERT classification
│   │   ├── reply_agent.py         # LLM-based reply generation (+ RAG)
│   │   └── suggestion_agent.py    # RAG-powered suggestion generation
│   ├── services/
│   │   ├── pinecone_service.py
│   │   └── llm_service.py         # Gemini/Groq/OpenRouter failover chain
│   ├── data/
│   │   ├── mock_google_maps_reviews.json
│   │   └── mock_twitter_mentions.json
│   └── utils/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                # landing/connect page
│   │   │   └── dashboard/page.tsx      # unified dashboard
│   │   ├── components/
│   │   │   ├── FeedbackFeed.tsx
│   │   │   ├── ReplyCard.tsx
│   │   │   ├── SentimentChart.tsx
│   │   │   ├── SuggestionsPanel.tsx
│   │   │   └── PlatformFilterTabs.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── hooks/
│   ├── tailwind.config.js
│   └── package.json
└── docs/
    ├── PRD.md
    ├── Architecture.md
    ├── Rules.md
    ├── Phases.md
    ├── Design.md
    └── Memory.md
```

## Database Schema (high-level)
- **businesses** — id, name, created_at
- **platform_connections** — id, business_id, platform (facebook/instagram/google_maps/twitter), status (live/simulated), credentials_ref
- **feedback_items** — id, business_id, platform, author_name, content_text, rating (nullable), sentiment, timestamp, created_at
- **replies** — id, feedback_item_id, generated_text, status (pending/approved/edited/posted), posted_at
- **suggestions** — id, business_id, suggestion_text, evidence_quotes (JSON), source_reference, created_at

## Key Architectural Principles
- Each platform connector is independent and pluggable — adding a new platform should not require touching the reply/sentiment/suggestion agents
- Sentiment classification is local (BERT) to avoid LLM rate limits at scale; LLM calls are reserved for generation tasks (replies, suggestions) where reasoning is required
- Live vs. simulated connectors share the same data contract/interface, so the rest of the pipeline (agents, dashboard) doesn't need to know which platform is real
- Replies default to a human-in-the-loop approval step before posting
