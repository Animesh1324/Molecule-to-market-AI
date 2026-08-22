"""Bulk load of the FDA catalogue datasets that are not drug monographs.

`openfda_bulk_ingest` turns drug/ndc and drug/label into `DrugRecord`s. These
three datasets describe different things — an approval application, a recall
event, a supply shortage — so they get their own tables and their own loader
rather than being bent into the drug shape.

Partition discovery, download, and the streaming decoder are reused from
`openfda_bulk_ingest`; only the mapping and the write differ.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from ..db.database import SessionLocal
from ..db.fda_catalog_models import (
    DrugRecallORM,
    DrugShortageORM,
    FDAApplicationORM,
    FDAApplicationProductORM,
    FDASubmissionORM,
)
from .openfda_bulk_ingest import (
    BulkUnavailable,
    download_partition,
    iter_json_array,
    list_partitions,
)

logger = logging.getLogger(__name__)

CATALOG_DATASETS = ("drugsfda", "enforcement", "shortages")

# Rows are written in batches; a per-row commit turns a 30k-row load into 30k
# fsyncs and dominates the runtime.
BATCH = 500


def _key(*parts: Any) -> str:
    """Stable synthetic id, so re-running updates rather than duplicating."""
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _text(value: Any, limit: int = 4000) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        value = " ".join(str(v) for v in value if v)
    value = " ".join(str(value).split())
    return value[:limit] or None


@dataclass
class CatalogResult:
    dataset: str
    read: int = 0
    written: Dict[str, int] = field(default_factory=dict)
    failed: int = 0

    def bump(self, table: str, n: int = 1) -> None:
        self.written[table] = self.written.get(table, 0) + n

    def as_dict(self) -> Dict[str, Any]:
        return {"dataset": self.dataset, "read": self.read,
                "written": self.written, "failed": self.failed}


# --------------------------------------------------------------------------
# Mappers: raw record -> list of (ORM class, primary-key dict, values dict)
# --------------------------------------------------------------------------

def _map_drugsfda(raw: Dict[str, Any], version: Optional[str]) -> List[tuple]:
    app_no = (raw.get("application_number") or "").strip()
    if not app_no:
        return []
    out: List[tuple] = []
    products = raw.get("products") or []

    brands, generics = [], []
    for p in products:
        b = (p.get("brand_name") or "").strip()
        if b and b not in brands:
            brands.append(b)
        for ing in p.get("active_ingredients") or []:
            n = (ing.get("name") or "").strip()
            if n and n not in generics:
                generics.append(n)

    out.append((FDAApplicationORM, {"application_number": app_no}, {
        "sponsor_name": _text(raw.get("sponsor_name"), 300),
        "brand_names": json.dumps(brands[:40]),
        "generic_names": json.dumps(generics[:40]),
        "data_version": version,
    }))

    for p in products:
        pn = (p.get("product_number") or "").strip()
        ings = p.get("active_ingredients") or []
        out.append((FDAApplicationProductORM, {"id": _key(app_no, pn)}, {
            "application_number": app_no,
            "product_number": pn or None,
            "brand_name": _text(p.get("brand_name"), 300),
            "active_ingredients": json.dumps([i.get("name") for i in ings if i.get("name")][:20]),
            "strengths": json.dumps([i.get("strength") for i in ings if i.get("strength")][:20]),
            "dosage_form": _text(p.get("dosage_form"), 200),
            "route": _text(p.get("route"), 200),
            "marketing_status": _text(p.get("marketing_status"), 100),
            "reference_drug": _text(p.get("reference_drug"), 20),
            "reference_standard": _text(p.get("reference_standard"), 20),
        }))

    for s in raw.get("submissions") or []:
        st, sn = (s.get("submission_type") or ""), (s.get("submission_number") or "")
        out.append((FDASubmissionORM, {"id": _key(app_no, st, sn)}, {
            "application_number": app_no,
            "submission_type": st or None,
            "submission_number": sn or None,
            "submission_status": _text(s.get("submission_status"), 100),
            "submission_status_date": s.get("submission_status_date"),
            "submission_class_code": _text(s.get("submission_class_code"), 50),
            "submission_class_description": _text(s.get("submission_class_code_description"), 300),
            "review_priority": _text(s.get("review_priority"), 50),
        }))
    return out


def _map_enforcement(raw: Dict[str, Any], version: Optional[str]) -> List[tuple]:
    number = (raw.get("recall_number") or "").strip()
    if not number:
        return []
    blob = " ".join(filter(None, [
        _text(raw.get("product_description"), 1000),
        _text(raw.get("reason_for_recall"), 500),
        _text(raw.get("recalling_firm"), 200),
    ])).lower()
    return [(DrugRecallORM, {"recall_number": number}, {
        "event_id": _text(raw.get("event_id"), 50),
        "product_description": _text(raw.get("product_description")),
        "reason_for_recall": _text(raw.get("reason_for_recall")),
        "classification": _text(raw.get("classification"), 50),
        "status": _text(raw.get("status"), 50),
        "recalling_firm": _text(raw.get("recalling_firm"), 300),
        "product_type": _text(raw.get("product_type"), 50),
        "product_quantity": _text(raw.get("product_quantity"), 300),
        "voluntary_mandated": _text(raw.get("voluntary_mandated"), 100),
        "distribution_pattern": _text(raw.get("distribution_pattern"), 1000),
        "country": _text(raw.get("country"), 100),
        "state": _text(raw.get("state"), 50),
        "city": _text(raw.get("city"), 100),
        "recall_initiation_date": raw.get("recall_initiation_date"),
        "report_date": raw.get("report_date"),
        "termination_date": raw.get("termination_date"),
        "search_blob": blob[:4000],
        "data_version": version,
    })]


def _map_shortages(raw: Dict[str, Any], version: Optional[str]) -> List[tuple]:
    generic = _text(raw.get("generic_name"), 300)
    company = _text(raw.get("company_name"), 300)
    presentation = _text(raw.get("presentation"), 500)
    posted = raw.get("initial_posting_date")
    if not (generic or company):
        return []
    return [(DrugShortageORM, {"id": _key(generic, company, presentation, posted)}, {
        "generic_name": generic,
        "company_name": company,
        "status": _text(raw.get("status"), 100),
        "availability": _text(raw.get("availability")),
        "shortage_reason": _text(raw.get("shortage_reason")),
        "therapeutic_category": _text(raw.get("therapeutic_category"), 200),
        "dosage_form": _text(raw.get("dosage_form"), 200),
        "presentation": presentation,
        "package_ndc": _text(raw.get("package_ndc"), 50),
        "initial_posting_date": posted,
        "update_date": raw.get("update_date"),
        "update_type": _text(raw.get("update_type"), 50),
        "contact_info": _text(raw.get("contact_info"), 500),
        "data_version": version,
    })]


_MAPPERS: Dict[str, Callable[[Dict[str, Any], Optional[str]], List[tuple]]] = {
    "drugsfda": _map_drugsfda,
    "enforcement": _map_enforcement,
    "shortages": _map_shortages,
}


# --------------------------------------------------------------------------
# Ingestion
# --------------------------------------------------------------------------

def ingest_dataset(
    dataset: str,
    *,
    cache_dir: str,
    limit: Optional[int] = None,
    keep_files: bool = False,
    progress: Optional[Callable[[CatalogResult], None]] = None,
) -> CatalogResult:
    mapper = _MAPPERS.get(dataset)
    if mapper is None:
        raise BulkUnavailable(f"no catalogue mapper for drug/{dataset}")

    result = CatalogResult(dataset=dataset)
    session = SessionLocal()
    pending = 0
    try:
        for partition in list_partitions(dataset):
            json_path = download_partition(partition, cache_dir)
            try:
                for raw in iter_json_array(json_path):
                    result.read += 1
                    # SAVEPOINT per row. PostgreSQL invalidates the entire
                    # transaction when any statement fails, so catching an
                    # exception and continuing — correct on SQLite — would let
                    # every later statement fail too, while these counters
                    # happily reported success. The nested block rolls back
                    # just the bad row and leaves the transaction usable.
                    written: List[str] = []
                    try:
                        with session.begin_nested():
                            for orm_class, pk, values in mapper(raw, partition.export_date):
                                session.merge(orm_class(**pk, **values))
                                written.append(orm_class.__tablename__)
                            # Inside the savepoint: merge only stages the row,
                            # the INSERT lands at flush. Flushing after the
                            # block would put the failing statement outside it.
                            session.flush()
                    except Exception:  # noqa: BLE001 - one bad row is not a failed load
                        result.failed += 1
                        logger.debug("row failed in %s", dataset, exc_info=True)
                    else:
                        for table in written:
                            result.bump(table)
                        pending += len(written)
                    if pending >= BATCH:
                        session.commit()
                        pending = 0
                    if progress and result.read % 2000 == 0:
                        progress(result)
                    if limit is not None and result.read >= limit:
                        session.commit()
                        return result
            finally:
                if not keep_files and os.path.exists(json_path):
                    os.unlink(json_path)
        session.commit()
        return result
    finally:
        session.close()


def ingest(
    datasets: Iterable[str] = CATALOG_DATASETS,
    *,
    cache_dir: Optional[str] = None,
    limit: Optional[int] = None,
    keep_files: bool = False,
    progress: Optional[Callable[[CatalogResult], None]] = None,
) -> Dict[str, CatalogResult]:
    from ..repositories import drug_repository as repo

    cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "openfda-bulk")
    results: Dict[str, CatalogResult] = {}
    for dataset in datasets:
        try:
            result = ingest_dataset(dataset, cache_dir=cache_dir, limit=limit,
                                    keep_files=keep_files, progress=progress)
            results[dataset] = result
            repo.log_ingestion(query=f"bulk:{dataset}", source_name="openFDA",
                               succeeded=True, written=sum(result.written.values()),
                               message=json.dumps(result.as_dict()))
        except BulkUnavailable as exc:
            results[dataset] = CatalogResult(dataset=dataset)
            repo.log_ingestion(query=f"bulk:{dataset}", source_name="openFDA",
                               succeeded=False, written=0, message=str(exc))
            logger.warning("catalogue ingest of drug/%s failed: %s", dataset, exc)
    return results
