# EngageSphere — Project Presentation Content

---

## 1. Methodology

### Problem Statement
Small and medium business owners receive customer feedback scattered across Google Maps, Facebook, Instagram, and Twitter. Responding manually to each platform is time-consuming, inconsistent, and often neglected — directly hurting customer satisfaction and brand reputation.

### Proposed Solution
EngageSphere is an AI-powered, multi-platform customer engagement system that:
- Automatically ingests customer reviews and comments from all platforms
- Classifies sentiment and intent using NLP
- Generates brand-appropriate AI replies grounded in business-specific facts
- Surfaces actionable improvement suggestions from aggregated feedback
- Allows the business owner to approve/edit before posting

### Development Methodology: Agile Phased Development

| Phase | Description | Status |
|---|---|---|
| 1 | Project scaffolding + database schema | Complete |
| 2 | Mock data connectors (Google Maps, Twitter) | Complete |
| 3 | Live connectors (Facebook, Instagram via Meta Graph API) | Complete |
| 4 | Sentiment + intent classification | Complete |
| 5+6 | AI reply generation + approval workflow | Complete |
| 7 | Suggestion Agent (RAG-powered) | Complete |
| 8 | Unified dashboard frontend | Complete |
| 9 | Polish, testing, demo preparation | Complete |

---

## 2. Algorithm / Block Diagram

### System Pipeline

```
DATA INGESTION
Google Maps (Simulated) | Facebook (Live) | Instagram (Live) | Twitter (Simulated)
                              ↓
CLASSIFICATION LAYER
Sentiment: positive / negative / neutral
Intent: complaint / praise / question / spam
(Groq LLM + keyword fallback)
                              ↓
            ┌─────────────────────────────┐
            ↓                             ↓
      REPLY AGENT                 SUGGESTION AGENT
  RAG retrieval (Pinecone)      Theme extraction
  LLM generation                Best-practice RAG
  Groq → Gemini → OpenRouter    LLM synthesis
  Toxicity check (toxic-bert)   Evidence-backed output
            ↓                             ↓
            └─────────────┬───────────────┘
                          ↓
                 APPROVAL WORKFLOW
          Owner reviews → Approve / Edit / Reject
          Approved reply posted back to platform
                          ↓
                 UNIFIED DASHBOARD
          Next.js + Tailwind CSS
          Platform filter | Sentiment chart
          Reply cards | Suggestions panel
```

### LLM Failover Chain
```
Request → Groq (Llama 3) → [fail] → Gemini → [fail] → OpenRouter → [fail] → Error
```

### Toxicity Gate
```
Generated Reply → toxic-bert classifier
  Score ≥ 0.7 → Flag for manual review
  Score < 0.7 → Enter approval queue
```

---

## 3. Implementation

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python, async) |
| Frontend | Next.js 15 + Tailwind CSS + TypeScript |
| Database | Supabase (PostgreSQL) |
| Authentication | Supabase Auth (JWT-based) |
| LLM — Generation | Groq (Llama 3) → Gemini → OpenRouter (failover) |
| Sentiment + Intent | Groq LLM + keyword fallback |
| Safety / Toxicity | unitary/toxic-bert (local, Hugging Face) |
| Vector Store | Pinecone (RAG for business info + best practices) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| Live Platforms | Facebook + Instagram (Meta Graph API) |
| Simulated Platforms | Google Maps + Twitter (mock JSON datasets) |

### Key Implementation Details
- **Multi-tenant architecture** — each business has isolated data and own platform connections
- **Human-in-the-loop** — no reply is ever auto-posted without owner approval
- **RAG grounding** — replies grounded in actual business facts (hours, menu, policies) via Pinecone
- **Dedup on ingestion** — same comment never ingested twice
- **Connector isolation** — one connector failing never crashes the pipeline for other platforms
- **OAuth flow** — business owners connect social accounts via standard OAuth

### Database Schema (5 tables)
- `businesses` — business accounts
- `platform_connections` — per-business OAuth tokens per platform
- `feedback_items` — all ingested comments/reviews
- `replies` — AI-generated replies with approval status
- `suggestions` — AI-generated improvement recommendations

---

## 4. Demonstration

### Demo Flow
1. **Sign up / Login** — Email + password authentication
2. **Fetch Comments** — System pulls from all connected platforms (30 items)
3. **Sentiment filter** — Filter by Positive / Negative / Neutral
4. **Platform filter** — Switch between Google Maps / Twitter / Facebook / Instagram
5. **Generate Replies** — AI generates brand-appropriate reply per comment
6. **Approve + Post** — Owner approves → reply posted live
7. **Suggestions** — 3–5 evidence-backed improvement recommendations generated

### Key Points
- Each reply is grounded in real business info — no hallucinated prices or hours
- Spam automatically detected and excluded from reply queue
- No reply posted without owner approval — human-in-the-loop by design
- Google Maps and Twitter simulated due to API constraints; Facebook/Instagram fully built pending Meta App Review

---

## 5. Intellectual Property Rights (IPR) Status

**Current Status: Not filed**

Open-source components used:
- FastAPI — MIT License
- Next.js — MIT License
- Supabase — Apache 2.0
- Hugging Face Transformers — Apache 2.0
- sentence-transformers — Apache 2.0
- unitary/toxic-bert — MIT License

**Potential IPR Opportunities:**
- Multi-platform aggregation + RAG-grounded reply generation pipeline
- Theme-based suggestion agent with evidence-quote extraction
- Eligible for provisional patent application

---

## 6. Hackathons / Project Competitions

**Current Status: Not yet participated**

| Event | Type | Venue | Date | Status |
|---|---|---|---|---|
| Smart India Hackathon (SIH) | National Hackathon | TBD | 2026 | Planned |
| HackWithInfy | Industry Hackathon | TBD | 2026 | Planned |
| Hack This Fall | Open Hackathon | Online | 2026 | Planned |
| IEEE Student Project Competition | Technical Competition | TBD | 2026 | Planned |

*Update with actual events participated in or registered for.*

---

## 7. Conclusion

EngageSphere successfully demonstrates:

1. **Multi-platform ingestion** from 4 platforms through a unified pipeline
2. **Automated NLP classification** — sentiment, intent, and spam detection
3. **RAG-grounded AI reply generation** — brand-appropriate, factually accurate, toxicity-checked
4. **Evidence-backed suggestion generation** — actionable recommendations from aggregated feedback
5. **Production-ready architecture** — multi-tenant, JWT-authenticated, human-in-the-loop

### Impact
- Reduces response time from hours/days to seconds
- Ensures consistency in brand voice across all platforms
- Surfaces recurring issues the owner may not have noticed
- Scalable to any number of businesses and platforms

### Future Scope
- WhatsApp Business API integration
- Automated reply scheduling
- Sentiment trend analytics over time
- Multi-language reply generation
- Mobile app for on-the-go approval

---

## 8. References

1. Brown, T. et al. (2020). *Language Models are Few-Shot Learners*. NeurIPS.
2. Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS.
3. Liu, Y. et al. (2019). *RoBERTa: A Robustly Optimized BERT Pretraining Approach*. arXiv.
4. Houlsby, N. et al. (2019). *Parameter-Efficient Transfer Learning for NLP*. ICML.
5. Meta Platforms Inc. (2024). *Meta Graph API Documentation*. https://developers.facebook.com/docs/graph-api/
6. Supabase Inc. (2024). *Supabase Documentation*. https://supabase.com/docs
7. Pinecone Systems Inc. (2024). *Pinecone Vector Database Documentation*. https://docs.pinecone.io
8. Groq Inc. (2024). *Groq API Documentation*. https://console.groq.com/docs
9. Hugging Face (2024). *cardiffnlp/twitter-roberta-base-sentiment-latest*. https://huggingface.co/cardiffnlp
10. Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP.
