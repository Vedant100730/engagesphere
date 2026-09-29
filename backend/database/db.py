from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# Supabase on Render free tier requires the SESSION POOLER URL (port 5432 on pooler host)
# because Render free tier doesn't support IPv6, and Supabase direct connections
# (db.xxx.supabase.co:5432) are IPv6-only on the free plan.
#
# Set DATABASE_URL in Render to the Session Pooler URI from:
# Supabase → Settings → Database → Connection pooling → Session mode
# Format: postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres

_db_url = settings.DATABASE_URL

# Ensure asyncpg driver prefix
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Add SSL if not present
if "ssl=" not in _db_url and "sslmode=" not in _db_url:
    _separator = "&" if "?" in _db_url else "?"
    _db_url += f"{_separator}ssl=require"

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_pre_ping=True,      # test connection before use
    pool_recycle=300,        # recycle every 5 min before pooler kills idle connections
    pool_size=3,
    max_overflow=2,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
