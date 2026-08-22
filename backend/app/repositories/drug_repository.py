"""Persistence for drugs, sources, and interactions.

All SQL lives here so the services stay free of session handling and the API
layer never touches the ORM. Every method opens and closes its own session:
the app has no request-scoped session, and leaking one across an await is how
SQLite ends up locked.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_

from ..data_sources.base import DrugRecord, InteractionRecord
from ..db.database import SessionLocal
from ..db.drug_models import (
    DrugInteractionORM,
    DrugORM,
    DrugSourceORM,
    IngestionLogORM,
    dumps,
    loads,
)

logger = logging.getLogger(__name__)

LIST_FIELDS = ("active_ingredients", "dosage_forms", "strengths", "routes")
TEXT_FIELDS = (
    "indications", "dosage", "contraindications", "warnings", "precautions",
    "adverse_effects", "drug_interactions", "pregnancy_information",
    "lactation_information", "mechanism",
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# PostgreSQL refuses a btree index entry over roughly 2704 bytes, and
# search_blob carries one. Six of the bulk-loaded rows exceeded it — multi-
# ingredient homeopathic products whose ingredient list runs to thousands of
# characters — which raises on INSERT under Postgres while SQLite, having no
# such limit, accepts them silently. Capped well under the limit so multi-byte
# characters cannot push an entry over it.
SEARCH_BLOB_MAX_BYTES = 2000


def _truncate_bytes(text: str, limit: int) -> str:
    """Cut to `limit` UTF-8 bytes without splitting a character."""
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", "ignore")


def _search_blob(record_like: Dict[str, Any]) -> str:
    """Lower-cased haystack covering every field a user might search on.

    Ordered most- to least-identifying, so if the cap truncates anything it is
    the tail of a long ingredient list rather than the drug's own name.
    """
    parts: List[str] = []
    for key in ("generic_name", "brand_name", "drug_class", "therapeutic_class", "manufacturer"):
        value = record_like.get(key)
        if value:
            parts.append(str(value))
    for key in LIST_FIELDS:
        parts.extend(str(v) for v in (record_like.get(key) or []))
    return _truncate_bytes(" ".join(parts).lower(), SEARCH_BLOB_MAX_BYTES)


def to_dict(orm: DrugORM) -> Dict[str, Any]:
    """ORM row -> plain dict, with JSON columns decoded."""
    data: Dict[str, Any] = {
        "id": orm.id,
        "generic_name": orm.generic_name,
        "brand_name": orm.brand_name,
        "drug_class": orm.drug_class,
        "therapeutic_class": orm.therapeutic_class,
        "manufacturer": orm.manufacturer,
        "status": orm.status,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }
    for key in LIST_FIELDS:
        data[key] = loads(getattr(orm, key))
    for key in TEXT_FIELDS:
        data[key] = getattr(orm, key)
    data["sources"] = [
        {
            "id": s.id,
            "source_name": s.source_name,
            "source_url": s.source_url,
            "source_identifier": s.source_identifier,
            "data_version": s.data_version,
            "published_at": s.published_at,
            "attribution": s.attribution,
            "confidence": s.confidence,
            "retrieved_at": s.retrieved_at,
        }
        for s in (orm.sources or [])
    ]
    return data


def upsert_drug(record: DrugRecord) -> str:
    """Insert or update one drug, returning its id.

    Merge policy: a newly fetched non-empty value wins, but an empty one never
    erases a value another source already supplied. Re-ingesting from a source
    with a thin label must not blank out good data.
    """
    session = SessionLocal()
    try:
        # Canonicalise case before the uniqueness check. openFDA returns the
        # same brand as both "Ozempic" and "OZEMPIC" across label records, and
        # a case-sensitive unique constraint would store each as its own drug.
        generic = (record.generic_name or "").strip().title()
        brand = (record.brand_name or "").strip().title() or None
        if not generic:
            raise ValueError("generic_name is required")

        existing = (
            session.query(DrugORM)
            .filter(DrugORM.generic_name == generic, DrugORM.brand_name == brand)
            .one_or_none()
        )

        if existing is None:
            existing = DrugORM(id=uuid.uuid4().hex, generic_name=generic, brand_name=brand)
            session.add(existing)

        for key in LIST_FIELDS:
            incoming = getattr(record, key, None) or []
            if incoming:
                setattr(existing, key, dumps(incoming))
        for key in TEXT_FIELDS + ("drug_class", "therapeutic_class", "manufacturer"):
            incoming = getattr(record, key, None)
            if incoming:
                setattr(existing, key, incoming)
        if record.status:
            existing.status = record.status

        existing.search_blob = _search_blob({
            "generic_name": generic,
            "brand_name": brand,
            "drug_class": existing.drug_class,
            "therapeutic_class": existing.therapeutic_class,
            "manufacturer": existing.manufacturer,
            **{k: loads(getattr(existing, k)) for k in LIST_FIELDS},
        })

        # Provenance: one row per source, refreshed on re-ingestion.
        attribution = record.attribution
        if attribution:
            source_row = (
                session.query(DrugSourceORM)
                .filter(
                    DrugSourceORM.drug_id == existing.id,
                    DrugSourceORM.source_name == attribution.source_name,
                )
                .one_or_none()
            )
            if source_row is None:
                source_row = DrugSourceORM(
                    id=uuid.uuid4().hex,
                    drug_id=existing.id,
                    source_name=attribution.source_name,
                )
                session.add(source_row)
            source_row.source_url = attribution.source_url
            source_row.source_identifier = attribution.source_identifier
            source_row.data_version = attribution.data_version
            source_row.published_at = attribution.published_at
            source_row.attribution = attribution.attribution
            source_row.confidence = attribution.confidence
            source_row.retrieved_at = attribution.retrieved_at

        session.commit()
        return existing.id
    finally:
        session.close()


def get_drug(drug_id: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        orm = session.get(DrugORM, drug_id)
        return to_dict(orm) if orm else None
    finally:
        session.close()


def list_drugs(page: int = 1, page_size: int = 25, drug_class: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    session = SessionLocal()
    try:
        query = session.query(DrugORM)
        if drug_class:
            needle = f"%{drug_class.strip().lower()}%"
            query = query.filter(
                or_(
                    DrugORM.drug_class.ilike(needle),
                    DrugORM.therapeutic_class.ilike(needle),
                )
            )
        total = query.count()
        rows = (
            query.order_by(DrugORM.generic_name.asc())
            .offset(max(0, (page - 1) * page_size))
            .limit(page_size)
            .all()
        )
        return [to_dict(r) for r in rows], total
    finally:
        session.close()


def search_drugs(term: str, page: int = 1, page_size: int = 25) -> Tuple[List[Dict[str, Any]], int]:
    """Search names, ingredients, class, strength and form — best match first.

    Relevance matters here: a search for "Beta" must return the drug *named*
    Beta ahead of every drug whose class happens to contain "beta-adrenergic".
    Ranking is done in Python because the tiers are cheap to compute and this
    has to behave identically on SQLite and Postgres.
    """
    session = SessionLocal()
    try:
        clean = (term or "").strip().lower()
        needle = f"%{clean}%"
        query = session.query(DrugORM).filter(
            or_(
                DrugORM.search_blob.like(needle),
                DrugORM.generic_name.ilike(needle),
                DrugORM.brand_name.ilike(needle),
            )
        )
        total = query.count()
        rows = query.order_by(DrugORM.generic_name.asc()).all()

        def rank(row: DrugORM) -> Tuple[int, int, int, str]:
            generic = (row.generic_name or "").lower()
            brand = (row.brand_name or "").lower()
            if clean in (generic, brand):
                tier = 0                      # exact name
            elif generic.startswith(clean) or brand.startswith(clean):
                tier = 1                      # name prefix
            elif clean in generic or clean in brand:
                tier = 2                      # name substring
            else:
                tier = 3                      # matched on class/ingredient/strength

            # Within a tier, prefer the record that actually carries content.
            # The NDC directory lists bulk active-ingredient consignments from
            # chemical suppliers alongside finished products: same generic
            # name, no brand, no label, no class. Ordering a tier purely by
            # name lets those win on alphabetical luck, so "pembrolizumab"
            # returned a Boehringer ingredient row above Keytruda. These are
            # tie-breakers only — they never reorder name relevance itself.
            has_label = 0 if row.indications else 1
            has_class = 0 if row.drug_class else 1
            return tier, has_label, has_class, generic

        rows.sort(key=rank)
        start = max(0, (page - 1) * page_size)
        return [to_dict(r) for r in rows[start:start + page_size]], total
    finally:
        session.close()


def find_by_name(name: str, *, field: str = "generic") -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        needle = f"%{(name or '').strip().lower()}%"
        column = DrugORM.brand_name if field == "brand" else DrugORM.generic_name
        rows = session.query(DrugORM).filter(column.ilike(needle)).limit(50).all()
        return [to_dict(r) for r in rows]
    finally:
        session.close()


def count_drugs() -> int:
    session = SessionLocal()
    try:
        return session.query(DrugORM).count()
    finally:
        session.close()


def upsert_interaction(record: InteractionRecord) -> Optional[str]:
    """Store one interaction with the pair alphabetically normalised."""
    a = (record.drug_a or "").strip().title()
    b = (record.drug_b or "").strip().title()
    if not a or not b or a.lower() == b.lower():
        return None
    if a.lower() > b.lower():
        a, b = b, a

    source_name = record.attribution.source_name if record.attribution else "unknown"
    session = SessionLocal()
    try:
        existing = (
            session.query(DrugInteractionORM)
            .filter(
                DrugInteractionORM.drug_a == a,
                DrugInteractionORM.drug_b == b,
                DrugInteractionORM.source_name == source_name,
            )
            .one_or_none()
        )
        if existing is None:
            existing = DrugInteractionORM(
                id=uuid.uuid4().hex, drug_a=a, drug_b=b, source_name=source_name
            )
            session.add(existing)
        existing.severity = (record.severity or "unknown").lower()
        existing.description = record.description
        existing.management = record.management
        if record.attribution:
            existing.source_url = record.attribution.source_url
            existing.retrieved_at = record.attribution.retrieved_at
        session.commit()
        return existing.id
    finally:
        session.close()


def interactions_for(name: str) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        needle = (name or "").strip().title()
        rows = (
            session.query(DrugInteractionORM)
            .filter(or_(DrugInteractionORM.drug_a == needle, DrugInteractionORM.drug_b == needle))
            .all()
        )
        return [
            {
                "id": r.id,
                "drug_a": r.drug_a,
                "drug_b": r.drug_b,
                "severity": r.severity,
                "description": r.description,
                "management": r.management,
                "source_name": r.source_name,
                "source_url": r.source_url,
                "retrieved_at": r.retrieved_at,
            }
            for r in rows
        ]
    finally:
        session.close()


def log_ingestion(query: str, source_name: str, succeeded: bool, written: int, message: str = "") -> None:
    session = SessionLocal()
    try:
        session.add(
            IngestionLogORM(
                id=uuid.uuid4().hex,
                query=query,
                source_name=source_name,
                succeeded=succeeded,
                records_written=str(written),
                message=(message or "")[:1000],
                started_at=_now(),
                finished_at=_now(),
            )
        )
        session.commit()
    except Exception:
        logger.exception("Could not write ingestion log")
    finally:
        session.close()


def recent_ingestions(limit: int = 25) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(IngestionLogORM)
            .order_by(IngestionLogORM.started_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "query": r.query,
                "source_name": r.source_name,
                "succeeded": r.succeeded,
                "records_written": int(r.records_written or 0),
                "message": r.message,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
            }
            for r in rows
        ]
    finally:
        session.close()
