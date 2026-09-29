from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler so unhandled exceptions return a JSON 500 that passes
    through CORS middleware instead of a raw Starlette error response that
    strips the Access-Control-Allow-Origin header.
    """
    import logging, traceback
    logging.getLogger("engagesphere").error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method, request.url.path, exc, traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
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


@app.get("/debug/db")
async def debug_db():
    """
    Temporary endpoint — tests DB connection and Supabase client init.
    Remove after confirming login works in production.
    """
    import traceback
    results = {}

    # 1. Test raw DB connection
    try:
        from sqlalchemy import text
        from backend.database.db import engine
        async with engine.connect() as conn:
            row = await conn.execute(text("SELECT 1 AS ok"))
            results["db_connection"] = "ok" if row.fetchone() else "no row returned"
    except Exception as exc:
        results["db_connection"] = f"FAILED: {exc}"
        results["db_traceback"] = traceback.format_exc()

    # 2. Test businesses table exists
    try:
        from sqlalchemy import text
        from backend.database.db import engine
        async with engine.connect() as conn:
            row = await conn.execute(text("SELECT COUNT(*) FROM businesses"))
            results["businesses_table"] = f"ok — {row.scalar()} rows"
    except Exception as exc:
        results["businesses_table"] = f"FAILED: {exc}"

    # 3. Test Supabase client init
    try:
        from supabase import create_client
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        results["supabase_client"] = "ok"
        results["supabase_url"] = settings.SUPABASE_URL[:40] + "..."
    except Exception as exc:
        results["supabase_client"] = f"FAILED: {exc}"

    return results
