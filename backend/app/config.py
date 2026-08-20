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
    origins = _split_csv(
        os.getenv("CORS_ORIGINS"),
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return {
        "app_env": os.getenv("APP_ENV", "development").strip().lower(),
        "port": int(os.getenv("PORT", "8000")),
        "cors_origins": origins,
        "database_url": os.getenv("DATABASE_URL", "").strip(),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
    }
