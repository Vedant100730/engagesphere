"""
startup_check.py — Run once before demo to validate environment.

Usage:
    python startup_check.py

Checks:
  - .env file exists and all required keys are present
  - Postgres connection is reachable
  - Pinecone connection is reachable (if key is set)
  - Groq API key is valid (quick test call)
  - Mock data files exist and are non-empty
  - Prints a go/no-go summary for each check
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# ── Colours ───────────────────────────────────────────────────────────────────
OK   = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m!\033[0m"


def check(label: str, passed: bool, detail: str = "", warn: bool = False) -> bool:
    icon = OK if passed else (WARN if warn else FAIL)
    suffix = f"  {detail}" if detail else ""
    print(f"  {icon}  {label}{suffix}")
    return passed


# ── 1. .env file ──────────────────────────────────────────────────────────────

def check_env_file() -> bool:
    print("\n[1] Environment file")
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        check(".env file", False, "not found — copy .env.example and fill in your keys")
        return False
    check(".env file", True, str(env_path))

    from dotenv import load_dotenv
    load_dotenv(env_path)

    required = {
        "DATABASE_URL":  "required",
        "GROQ_API_KEY":  "required for LLM (primary)",
        "GEMINI_API_KEY": "optional (fallback LLM)",
        "OPENROUTER_API_KEY": "optional (second fallback LLM)",
        "PINECONE_API_KEY": "required for RAG",
        "PINECONE_INDEX_NAME": "required for RAG",
    }
    optional = {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "live Facebook connector",
        "INSTAGRAM_ACCESS_TOKEN": "live Instagram connector",
    }

    all_ok = True
    for key, note in required.items():
        val = os.getenv(key, "")
        ok = bool(val)
        if not ok:
            all_ok = False
        check(f"  {key}", ok, f"({note})" if not ok else "set")

    for key, note in optional.items():
        val = os.getenv(key, "")
        check(f"  {key}", bool(val), f"not set — {note} will be skipped" if not val else "set", warn=not bool(val))

    return all_ok


# ── 2. Mock data files ────────────────────────────────────────────────────────

def check_mock_data() -> bool:
    print("\n[2] Mock data files")
    data_dir = Path(__file__).parent / "data"
    files = {
        "mock_google_maps_reviews.json": 15,
        "mock_twitter_mentions.json": 15,
        "seed_business_info.json": 1,
        "best_practices_kb.json": 10,
    }
    all_ok = True
    for fname, min_items in files.items():
        path = data_dir / fname
        if not path.exists():
            check(fname, False, "missing")
            all_ok = False
            continue
        try:
            data = json.loads(path.read_text())
            count = len(data) if isinstance(data, list) else 1
            ok = count >= min_items
            if not ok:
                all_ok = False
            check(fname, ok, f"{count} items" + ("" if ok else f" (expected ≥{min_items})"))
        except json.JSONDecodeError:
            check(fname, False, "invalid JSON")
            all_ok = False
    return all_ok


# ── 3. Database connection ────────────────────────────────────────────────────

async def check_database() -> bool:
    print("\n[3] Database connection")
    try:
        import asyncpg  # type: ignore
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env")
        url = os.getenv("DATABASE_URL", "")
        # asyncpg uses postgresql://, not postgresql+asyncpg://
        pg_url = url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(pg_url, timeout=5)

        # Check tables exist
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        table_names = {r["tablename"] for r in tables}
        expected = {"businesses", "platform_connections", "feedback_items", "replies", "suggestions"}
        missing = expected - table_names

        await conn.close()

        if missing:
            check("Postgres reachable", True)
            check("Schema tables", False, f"missing: {', '.join(missing)} — run schema.sql")
            return False
        check("Postgres reachable", True)
        check("Schema tables", True, f"all {len(expected)} tables present")
        return True
    except Exception as exc:
        check("Postgres reachable", False, str(exc))
        return False


# ── 4. Pinecone connection ────────────────────────────────────────────────────

def check_pinecone() -> bool:
    print("\n[4] Pinecone connection")
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    api_key = os.getenv("PINECONE_API_KEY", "")
    index_name = os.getenv("PINECONE_INDEX_NAME", "")
    if not api_key:
        check("Pinecone", False, "PINECONE_API_KEY not set", warn=True)
        return False
    try:
        from pinecone import Pinecone  # type: ignore
        pc = Pinecone(api_key=api_key)
        indexes = [i.name for i in pc.list_indexes()]
        if index_name not in indexes:
            check("Pinecone connected", True)
            check(f"Index '{index_name}'", False,
                  f"not found — available: {indexes or 'none'}. Create it first.")
            return False
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        total = stats.get("total_vector_count", 0)
        check("Pinecone connected", True)
        check(f"Index '{index_name}'", True, f"{total} vectors stored")

        # Warn if namespaces look empty
        ns = stats.get("namespaces", {})
        for expected_ns in ("business-info", "best-practices"):
            count = ns.get(expected_ns, {}).get("vector_count", 0)
            ok = count > 0
            check(
                f"  Namespace '{expected_ns}'",
                ok,
                f"{count} vectors" if ok else "empty — seed this namespace before demo",
                warn=not ok,
            )
        return True
    except Exception as exc:
        check("Pinecone", False, str(exc))
        return False


# ── 5. Groq API ───────────────────────────────────────────────────────────────

async def check_groq() -> bool:
    print("\n[5] Groq API")
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        check("Groq API key", False, "not set — LLM generation will fall through to Gemini/OpenRouter", warn=True)
        return False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
            )
        if resp.status_code == 200:
            check("Groq API", True, "reachable and responding")
            return True
        elif resp.status_code == 429:
            check("Groq API", True, "key valid but rate-limited — will fall back during demo", warn=True)
            return True
        else:
            check("Groq API", False, f"HTTP {resp.status_code}")
            return False
    except Exception as exc:
        check("Groq API", False, str(exc))
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 52)
    print("  EngageSphere — Pre-demo Environment Check")
    print("=" * 52)

    results = []
    results.append(check_env_file())
    results.append(check_mock_data())
    results.append(await check_database())
    results.append(check_pinecone())
    results.append(await check_groq())

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 52}")
    if passed == total:
        print(f"  {OK}  All {total} checks passed — ready for demo.")
    else:
        failed = total - passed
        print(f"  {FAIL}  {failed}/{total} check(s) failed — review above before demo.")
    print("=" * 52 + "\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
