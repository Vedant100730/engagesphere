# EngageSphere — Demo Runbook

Step-by-step guide to running a complete end-to-end demo, from a cold start to a fully populated dashboard with AI-generated replies and suggestions.

---

## Pre-demo checklist

1. **Fill in `.env`** — copy `backend/.env.example` to `backend/.env` and add:
   - `DATABASE_URL` — your Supabase Postgres connection string
   - `GROQ_API_KEY` — free tier at console.groq.com
   - `PINECONE_API_KEY` + `PINECONE_INDEX_NAME` — create a free index (dimension: **384**, metric: **cosine**)
   - Optional: `GEMINI_API_KEY`, `OPENROUTER_API_KEY` (LLM fallbacks)
   - Optional: `FACEBOOK_PAGE_ACCESS_TOKEN`, `INSTAGRAM_ACCESS_TOKEN` (live connectors)

2. **Run schema** — paste `backend/database/schema.sql` into Supabase SQL Editor and run it.

3. **Run environment check**:
   ```bash
   cd backend
   python startup_check.py
   ```
   All green → proceed. Any red → fix before continuing.

4. **Start backend**:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

5. **Start frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Visit http://localhost:3000

---

## Demo flow (10–15 minutes)

### Step 1 — Create a business record

Insert a business row directly in Supabase (or via psql), note the UUID:

```sql
INSERT INTO businesses (name) VALUES ('The Daily Grind') RETURNING id;
-- copy the UUID, e.g. a1b2c3d4-...
```

### Step 2 — Seed business facts into Pinecone

```bash
curl -X POST http://localhost:8000/api/business/seed \
  -H "Content-Type: application/json" \
  -d "$(cat backend/data/seed_business_info.json | python -c "
import json, sys
data = json.load(sys.stdin)
data['business_id'] = 'YOUR_UUID_HERE'
print(json.dumps(data))
")"
```

Or open `http://localhost:8000/docs` (Swagger UI) → `POST /api/business/seed` → paste contents of `seed_business_info.json` with `business_id` added.

Verify RAG is working:
```
GET http://localhost:8000/api/business/seed/verify?business_id=YOUR_UUID&query=do+you+have+oat+milk
```
Expected: chunks about milk options and the oat milk policy retrieved.

### Step 3 — Seed best-practices knowledge base

```bash
curl -X POST http://localhost:8000/api/suggestions/seed-kb
```

Only needs to run once per Pinecone index. Returns the 18 documents upserted.

### Step 4 — Open the dashboard

Visit http://localhost:3000 → click "Go to Dashboard"

Paste the business UUID into the "Business UUID…" field → click **Set**.

### Step 5 — Ingest + generate replies

Click **"Ingest + Generate Replies"** in the dashboard.

Watch the status bar:
- `Fetching feedback from all platforms…` — Google Maps (15) + Twitter (15) loaded from mock JSON. Facebook/Instagram pulled live if tokens are set.
- `Inserted N items (N classified) — generating AI replies…` — BERT/BART classify each item, LLM generates replies.

The feed populates. Each card shows:
- Platform badge (Google Maps / Twitter / Facebook / Instagram)
- Author + star rating (where applicable)
- Sentiment badge (positive / negative / neutral)
- Intent badge (complaint / praise / question / spam)
- Full review text
- AI-generated reply with Approve / Edit / Post buttons

**Talking point:** Spam items (tw_005) appear in the feed but have no reply card — classified and visible but excluded from the queue.

### Step 6 — Approve and post a reply

Pick a positive review → click **Approve** → status changes to `approved`.

Click **Post** → for Google Maps / Twitter: reply is logged (simulated). For Facebook / Instagram (if tokens set): reply is posted live via Graph API.

**Talking point:** Human-in-the-loop is the default. Auto-post can be enabled but isn't the default — by design.

### Step 7 — Edit a negative reply

Find a complaint (red badge). Click **Edit** → modify the reply text → click **Save** → status becomes `edited`. Click **Post**.

**Talking point:** Negative feedback replies acknowledge the concern and don't dismiss or escalate — enforced by the system prompt.

### Step 8 — Generate improvement suggestions

In the Suggestions panel (right sidebar) → click **Re-generate**.

After a few seconds, 3–6 suggestion cards appear, each with:
- A concrete, actionable recommendation
- 2 evidence quotes from real feedback
- A cited best-practice source

**Talking point:** The Suggestion Agent cross-references customer feedback with a marketing/operations knowledge base — not just summarising complaints, but grounding suggestions in best practice.

### Step 9 — Filter the feed

Use the platform tabs to switch between All / Google Maps / Twitter / Facebook / Instagram.

Use the sentiment tabs to filter to Negative only — shows only complaints, useful for triage.

### Step 10 — Sentiment breakdown

The Sentiment Breakdown chart (right sidebar) shows live percentages of positive / negative / neutral across all platforms. Updates after ingest.

---

## Common questions from panellists

**"Is the Facebook/Instagram integration live?"**
Yes — if tokens are configured. For the demo we've set up a dummy Facebook Page and Instagram Business account in Meta Developer App (Development mode). The connectors call the real Graph API.

**"Why are Google Maps and Twitter simulated?"**
Google Business Profile API requires live business verification which isn't feasible in the project timeline. Twitter API v2 costs $100+/month. Both are simulated with realistic mock datasets — the pipeline treats them identically to live platforms.

**"Where do the AI replies come from?"**
Groq (Llama 3.3 70B) is the primary LLM — fastest free-tier inference, key for a "live reply" demo. If Groq is rate-limited, it falls back to Gemini, then OpenRouter. All generation is grounded in actual business facts (hours, policies, menu) via RAG — the AI can't hallucinate that "we open at 6am" if the business actually opens at 7am.

**"How does the toxicity check work?"**
Every AI-generated reply passes through `unitary/toxic-bert` before entering the queue. If flagged, the reply card shows a "⚠ Needs manual review" badge. The reply is not deleted or auto-corrected — the owner must review it. This prevents the system from silently posting inappropriate content.

**"What sentiment model are you using?"**
`cardiffnlp/twitter-roberta-base-sentiment-latest` — a RoBERTa model fine-tuned on tweets, well-suited for short social media text. Intent classification (complaint/praise/question/spam) uses `facebook/bart-large-mnli` via zero-shot classification. Both run fully locally — no API calls, no rate limits.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Feed shows "Failed to load feedback" | Backend not running or CORS issue — check `uvicorn` is on port 8000 |
| Ingest button shows "Ingesting…" forever | BART model downloading for first time (~1.5GB) — wait or check logs |
| Suggestions panel empty after generate | Seed the KB first: `POST /api/suggestions/seed-kb` |
| RAG replies are generic (no business facts) | Seed business info first: `POST /api/business/seed` |
| Facebook/Instagram not ingesting | Check tokens in `.env`, verify Meta app is in Development mode with correct permissions |
| Groq rate limit | Normal on free tier — Gemini fallback kicks in automatically |
