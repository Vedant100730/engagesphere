from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import auth, business, classify, feedback, ingest, oauth, replies, suggestions

app = FastAPI(
    title="EngageSphere API",
    description="AI-powered multi-platform customer engagement system",
    version="2.0.0",
)

# Allow localhost (dev) + deployed Vercel frontend (prod).
# The explicit Vercel URL is hardcoded as a safety net in case FRONTEND_URL
# env var is not yet set on Render.
_allowed_origins = list({
    "http://localhost:3000",
    "https://engagesphere-dun.vercel.app",
    settings.FRONTEND_URL,   # picks up any custom domain set later
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/auth",        tags=["auth"])
app.include_router(oauth.router,       prefix="/api/oauth",       tags=["oauth"])
app.include_router(ingest.router,      prefix="/api/ingest",      tags=["ingest"])
app.include_router(classify.router,    prefix="/api/classify",    tags=["classify"])
app.include_router(business.router,    prefix="/api/business",    tags=["business"])
app.include_router(feedback.router,    prefix="/api/feedback",    tags=["feedback"])
app.include_router(replies.router,     prefix="/api/replies",     tags=["replies"])
app.include_router(suggestions.router, prefix="/api/suggestions", tags=["suggestions"])


@app.get("/health")
async def health_check():
    """Health check — also surfaces missing critical env vars."""
    missing = [
        var for var in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "DATABASE_URL")
        if not getattr(settings, var, "")
        or getattr(settings, var) == "postgresql+asyncpg://user:password@localhost:5432/engagesphere"
    ]
    return {
        "status": "ok",
        "service": "EngageSphere API v2",
        "warnings": [f"Missing env var: {v}" for v in missing] if missing else [],
    }
