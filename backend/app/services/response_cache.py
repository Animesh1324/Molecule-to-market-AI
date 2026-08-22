"""Get-or-fetch caching for expensive external lookups.

See db/response_cache_models.py for why this exists. Usage is always the
same shape: try the cache, and only call the real (slow, network-bound)
fetcher on a miss or an expired entry.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional

from ..db.database import SessionLocal
from ..db.response_cache_models import ResponseCacheORM

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read(cache_key: str, ttl_hours: int) -> Optional[dict]:
    session = SessionLocal()
    try:
        row = session.get(ResponseCacheORM, cache_key)
        if not row:
            return None
        try:
            fetched = datetime.strptime(row.fetched_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        if datetime.now() - fetched > timedelta(hours=ttl_hours):
            return None
        try:
            return json.loads(row.payload_json)
        except (TypeError, ValueError):
            return None
    finally:
        session.close()


def _write(cache_key: str, payload: dict) -> None:
    session = SessionLocal()
    try:
        row = session.get(ResponseCacheORM, cache_key)
        values = dict(payload_json=json.dumps(payload), fetched_at=_now())
        if row is None:
            session.add(ResponseCacheORM(cache_key=cache_key, **values))
        else:
            for field, value in values.items():
                setattr(row, field, value)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to write response cache entry %s", cache_key)
    finally:
        session.close()


async def get_or_fetch(
    cache_key: str,
    ttl_hours: int,
    fetch: Callable[[], Awaitable[Any]],
    to_dict: Callable[[Any], dict],
    from_dict: Callable[[dict], Any],
) -> Any:
    """Return the cached value if fresh, otherwise fetch, cache, and return it.

    `to_dict`/`from_dict` convert to and from a plain JSON-serialisable dict —
    kept explicit rather than assuming every cached value is a Pydantic model,
    since this cache is meant to be reusable for whatever the next slow
    external lookup turns out to be.

    A fetch failure is never masked by a stale-but-expired cache entry here —
    the caller already has its own fallback behaviour (e.g. degrading to
    "not available") and re-raising lets that path run, exactly as it would
    without caching in front of it.
    """
    cached = _read(cache_key, ttl_hours)
    if cached is not None:
        return from_dict(cached)

    result = await fetch()
    if result is not None:
        try:
            _write(cache_key, to_dict(result))
        except Exception:
            logger.exception("Failed to serialise response cache entry %s", cache_key)
    return result
