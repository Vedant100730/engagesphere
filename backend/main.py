from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import auth, business, classify, feedback, ingest, oauth, replies, suggestions

app = FastAPI(
    title="EngageSphere API",
    description="AI-powered multi-platform customer engagement system",
    version="2.0.0",
)

# Allow both localhost (dev) and the deployed frontend URL (prod)
_allowed_origins = list({
    "http://localhost:3000",
    settings.FRONTEND_URL,
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
    return {"status": "ok", "service": "EngageSphere API v2"}
