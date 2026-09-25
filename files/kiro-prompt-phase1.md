# EngageSphere — Kiro Build Prompt (Phase 1)

Copy-paste the block below directly into Kiro.

---

```
Build a full-stack web application called "EngageSphere" — an AI-powered, 
multi-platform customer engagement system for business owners.

SUMMARY: EngageSphere ingests customer reviews and comments from Google 
Maps, Facebook, Instagram, and Twitter, classifies sentiment and intent 
locally using free NLP models, and uses an LLM-powered Reply-Generation 
Agent (grounded in the business's own info via RAG) to draft brand-
appropriate, satisfaction-focused replies for owner approval before 
posting. A Suggestion Agent analyzes aggregated feedback across all 
platforms to generate actionable, evidence-backed recommendations. 
Everything is managed from a single unified dashboard. Facebook and 
Instagram are live via the Meta Graph API on a dummy business account; 
Google Maps and Twitter are simulated with mock datasets due to 
business-verification and API-cost constraints respectively.

TECH STACK:
- Backend: FastAPI (Python)
- Frontend: Next.js + Tailwind CSS
- Database: Supabase (Postgres)
- Vector store: Pinecone (RAG for business-info grounding + suggestions 
  knowledge base)
- LLM (generation only): Groq (Llama 3.3 70B, primary — fastest free 
  inference), Gemini API (fallback), OpenRouter free models (second 
  fallback) — all behind a single failover-aware llm_service module
- Local NLP (classification, no API calls, no rate limits):
  - Sentiment: cardiffnlp/twitter-roberta-base-sentiment-latest
  - Intent/category (zero-shot): facebook/bart-large-mnli — classify 
    into complaint / praise / question / spam
  - Safety/moderation: unitary/toxic-bert — every generated reply must 
    pass this check before entering the approval queue
- Embeddings for RAG: sentence-transformers (local) or Gemini embeddings
- Platform APIs: Meta Graph API (Facebook + Instagram, live); Google 
  Maps and Twitter connectors read from local mock JSON datasets instead 
  of live APIs

SCOPE FOR THIS TASK — PHASE 1 ONLY (scaffolding + database):
1. FastAPI backend folder structure:
   backend/main.py, backend/database/, backend/models/, backend/routers/, 
   backend/connectors/, backend/agents/, backend/services/, backend/data/, 
   backend/utils/, backend/requirements.txt, backend/.env.example
2. Next.js frontend scaffolding (App Router, TypeScript, Tailwind CSS) 
   under frontend/
3. Postgres schema (backend/database/schema.sql) with these tables:
   - businesses (id, name, created_at)
   - platform_connections (id, business_id, platform, status, 
     credentials_ref, created_at) — platform is one of 
     google_maps/facebook/instagram/twitter, status is live/simulated
   - feedback_items (id, business_id, platform, author_name, 
     content_text, rating nullable, sentiment, intent_category, 
     timestamp, created_at)
   - replies (id, feedback_item_id, generated_text, status, 
     toxicity_flagged boolean, posted_at, created_at) — status is 
     pending/approved/edited/posted
   - suggestions (id, business_id, suggestion_text, evidence_quotes JSON, 
     source_reference, created_at)
4. .env.example with placeholder values only for: DATABASE_URL, 
   GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, PINECONE_API_KEY, 
   PINECONE_INDEX_NAME, PINECONE_ENVIRONMENT, plus placeholders for 
   Meta Graph API (FACEBOOK_PAGE_ACCESS_TOKEN, INSTAGRAM_ACCESS_TOKEN, 
   META_APP_ID, META_APP_SECRET)
5. Add a .gitignore that excludes .env, backend/.env, frontend/.env, 
   __pycache__/, node_modules/, and venv/

DO NOT build the connectors, sentiment/intent/safety classification, 
reply generation, suggestion agent, or dashboard UI yet — those come in 
later phases. Keep this task scoped only to scaffolding and schema so it 
completes in one pass without hitting rate limits.

START WITH: confirm the folder structure and schema, then stop — do not 
proceed to later phases automatically.
```

---

Give this to Kiro first. Once Phase 1 is confirmed working, come back for the Phase 2 prompt (mock Google Maps + Twitter connectors) — one phase per Kiro session keeps each task small enough to finish without hitting the free-tier rate limit.
