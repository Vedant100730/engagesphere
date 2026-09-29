from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# Supabase requires SSL. Add ssl=require if not already in the URL.
_db_url = settings.DATABASE_URL
if "ssl=" not in _db_url and "sslmode=" not in _db_url:
    _separator = "&" if "?" in _db_url else "?"
    _db_url += f"{_separator}ssl=require"

engine = create_async_engine(
    _db_url,
    echo=False,
    # Conservative pool settings for Render free tier (512MB RAM, single worker)
    pool_size=3,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=300,       # recycle connections every 5 min to avoid Supabase idle timeout
    pool_pre_ping=True,     # test connection before use — catches stale connections
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
