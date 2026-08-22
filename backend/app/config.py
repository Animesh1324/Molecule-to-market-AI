import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)


def _split_csv(value: Optional[str], default: str = "") -> List[str]:
    if not value:
        return [] if not default else [item.strip() for item in default.split(",") if item.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> dict:
    configured = os.getenv("CORS_ORIGINS")
    origins = _split_csv(
        configured,
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return {
        "app_env": os.getenv("APP_ENV", "development").strip().lower(),
        "port": int(os.getenv("PORT", "8000")),
        "cors_origins": origins,
        "cors_origins_configured": bool(configured and configured.strip()),
        "database_url": os.getenv("DATABASE_URL", "").strip(),
        "anthropic_api_key": anthropic_key,
        # AI drafting is opt-in and additive: with no key the app keeps using
        # the deterministic template, so a missing key degrades the output
        # rather than breaking the endpoint.
        "ai_enabled": bool(anthropic_key) and os.getenv("AI_DRAFTING", "on").strip().lower() not in ("off", "0", "false"),
        "claude_model": os.getenv("CLAUDE_MODEL", "claude-opus-5").strip(),
        "claude_effort": os.getenv("CLAUDE_EFFORT", "high").strip().lower(),
        # openFDA works without a key; the key only raises the request ceiling
        # (1,000/day -> 120,000/day). It does NOT lift the skip=25,000 paging
        # cap, so a key alone never makes a query-based fetch complete —
        # whole-corpus loading still comes from the bulk partitions.
        "openfda_api_key": os.getenv("OPENFDA_API_KEY", "").strip(),
        # NCBI E-utilities: 3 requests/second anonymous, 10 with a free key.
        # Only affects how fast the literature loads, never how much of it.
        "ncbi_api_key": os.getenv("NCBI_API_KEY", "").strip(),
    }
