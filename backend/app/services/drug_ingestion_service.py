"""Ingestion: fetch from permitted sources, normalise, persist, log.

Every source is isolated. One upstream being down, rate-limited, unlicensed, or
returning malformed data can never fail the request or the application — the
failure is logged against that source and the others still run. This is the
whole point of the adapter layer.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple

from ..data_sources.base import (
    DrugDataSource,
    DrugRecord,
    SourceNotPermitted,
    SourceUnavailable,
)
from ..data_sources.drugs_com_source import DrugsComSource
from ..data_sources.manual_source import ManualImportSource
from ..data_sources.openfda_source import OpenFDASource
from ..models.drug import SourceOutcome
from ..repositories import drug_repository as repo

logger = logging.getLogger(__name__)

# Per-source timeout. A slow upstream must not hold the request open.
SOURCE_TIMEOUT_SECONDS = 25.0

# Repeat failures trip a breaker so a dead source is skipped rather than
# retried on every request. Reset after the cooldown.
_FAILURE_THRESHOLD = 3
_COOLDOWN_SECONDS = 300.0
_failures: Dict[str, int] = {}
_opened_at: Dict[str, float] = {}


def _registry() -> List[DrugDataSource]:
    """Adapters in priority order. Constructed per call so env changes apply."""
    return [OpenFDASource(), DrugsComSource(), ManualImportSource()]


def available_sources() -> List[Dict[str, object]]:
    return [s.describe() for s in _registry()]


def _breaker_open(name: str) -> bool:
    if name not in _opened_at:
        return False
    if time.monotonic() - _opened_at[name] > _COOLDOWN_SECONDS:
        _opened_at.pop(name, None)
        _failures.pop(name, None)
        return False
    return True


def _record_failure(name: str) -> None:
    _failures[name] = _failures.get(name, 0) + 1
    if _failures[name] >= _FAILURE_THRESHOLD:
        _opened_at[name] = time.monotonic()
        logger.warning("Circuit opened for source %s after %d failures", name, _failures[name])


def _record_success(name: str) -> None:
    _failures.pop(name, None)
    _opened_at.pop(name, None)


async def ingest_query(query: str, source_names: Optional[List[str]] = None) -> List[SourceOutcome]:
    """Fetch `query` from every permitted source and persist what comes back."""
    term = (query or "").strip()
    if not term:
        return []

    outcomes: List[SourceOutcome] = []

    for source in _registry():
        if source_names and source.name not in source_names:
            continue

        if not source.enabled:
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False,
                message=f"Skipped — not enabled. {source.access_policy}",
            ))
            continue

        if _breaker_open(source.name):
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False,
                message="Skipped — circuit open after repeated failures.",
            ))
            continue

        written = 0
        try:
            records: List[DrugRecord] = await asyncio.wait_for(
                source.fetch(term), timeout=SOURCE_TIMEOUT_SECONDS
            )
            for record in records:
                try:
                    repo.upsert_drug(record)
                    written += 1
                except Exception:
                    logger.exception("Could not persist record from %s", source.name)

            try:
                for interaction in await asyncio.wait_for(
                    source.fetch_interactions(term), timeout=SOURCE_TIMEOUT_SECONDS
                ):
                    repo.upsert_interaction(interaction)
            except (SourceUnavailable, asyncio.TimeoutError, Exception) as exc:
                logger.info("Interactions unavailable from %s: %s", source.name, exc)

            _record_success(source.name)
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=True,
                records_written=written,
                message=f"{written} record(s) written." if written else "No matching records.",
            ))
            repo.log_ingestion(term, source.name, True, written)

        except SourceNotPermitted as exc:
            # Permanent: no retry, no breaker — the licence is simply absent.
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False, message=str(exc)
            ))
            repo.log_ingestion(term, source.name, False, 0, str(exc))

        except asyncio.TimeoutError:
            _record_failure(source.name)
            message = f"Timed out after {SOURCE_TIMEOUT_SECONDS:.0f}s."
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False, message=message
            ))
            repo.log_ingestion(term, source.name, False, 0, message)

        except SourceUnavailable as exc:
            _record_failure(source.name)
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False, message=str(exc)
            ))
            repo.log_ingestion(term, source.name, False, 0, str(exc))

        except Exception as exc:
            # An adapter bug must not surface as a 500 to the caller.
            _record_failure(source.name)
            logger.exception("Unexpected failure in source %s", source.name)
            message = f"Unexpected adapter error: {exc}"
            outcomes.append(SourceOutcome(
                source_name=source.name, query=term, succeeded=False, message=message
            ))
            repo.log_ingestion(term, source.name, False, 0, message)

    return outcomes


async def ensure_ingested(query: str) -> bool:
    """Ingest on demand when a search finds nothing cached.

    Returns whether anything was written, so the caller can tell the user the
    difference between "no such drug" and "nothing cached yet".
    """
    outcomes = await ingest_query(query)
    return any(o.records_written for o in outcomes)
