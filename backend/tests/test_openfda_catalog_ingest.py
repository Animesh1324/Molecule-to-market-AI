"""Tests for the FDA catalogue bulk loader (drugsfda, enforcement, shortages).

Network-free: partition discovery and download are substituted with a local
file. These write to the real (test) database, so they also cover the merge
behaviour that makes re-running a load safe.
"""
import json
import os

import pytest

from app.db.database import SessionLocal, init_db
from app.db.fda_catalog_models import (
    DrugRecallORM,
    DrugShortageORM,
    FDAApplicationORM,
    FDAApplicationProductORM,
    FDASubmissionORM,
)
from app.services import openfda_bulk_ingest as bulk
from app.services import openfda_catalog_ingest as catalog

init_db()


DRUGSFDA_ROW = {
    "application_number": "NDA021223",
    "sponsor_name": "BRISTOL MYERS SQUIBB",
    "products": [{
        "product_number": "001",
        "brand_name": "ELIQUIS",
        "active_ingredients": [{"name": "APIXABAN", "strength": "2.5MG"}],
        "dosage_form": "TABLET", "route": "ORAL",
        "marketing_status": "Prescription",
        "reference_drug": "Yes", "reference_standard": "Yes",
    }],
    "submissions": [
        {"submission_type": "ORIG", "submission_number": "1",
         "submission_status": "AP", "submission_status_date": "20121228",
         "submission_class_code": "TYPE 1", "review_priority": "PRIORITY"},
        {"submission_type": "SUPPL", "submission_number": "12",
         "submission_status": "AP", "submission_status_date": "20190315"},
    ],
}

ENFORCEMENT_ROW = {
    "recall_number": "D-1234-2026",
    "event_id": "99999",
    "product_description": "Metformin HCl ER Tablets 500 mg, 100-count bottle",
    "reason_for_recall": "NDMA levels above the acceptable daily intake limit",
    "classification": "Class II", "status": "Ongoing",
    "recalling_firm": "Example Pharma Inc", "product_type": "Drugs",
    "country": "United States", "state": "NJ", "city": "Princeton",
    "recall_initiation_date": "20260101", "report_date": "20260115",
}

SHORTAGE_ROW = {
    "generic_name": "Amoxicillin Oral Suspension",
    "company_name": "Example Labs",
    "status": "Current", "availability": "Limited supply",
    "shortage_reason": "Demand increase for the drug",
    "therapeutic_category": "Anti-Infective",
    "dosage_form": "Powder for suspension",
    "presentation": "250 mg/5 mL 100 mL bottle",
    "initial_posting_date": "20251001", "update_type": "Update",
}


@pytest.fixture
def local_partition(tmp_path, monkeypatch):
    def _install(dataset, rows):
        path = os.path.join(tmp_path, f"{dataset}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"meta": {}, "results": rows}, handle)
        part = bulk.Partition(dataset=dataset, url="http://local", export_date="2026-08-21")
        monkeypatch.setattr(catalog, "list_partitions", lambda ds, **kw: [part])
        monkeypatch.setattr(catalog, "download_partition", lambda p, cache_dir, **kw: path)
        return path
    return _install


def _clean(*models):
    session = SessionLocal()
    for model in models:
        session.query(model).delete()
    session.commit()
    session.close()


def test_drugsfda_writes_application_products_and_submissions(local_partition, tmp_path):
    _clean(FDAApplicationORM, FDAApplicationProductORM, FDASubmissionORM)
    local_partition("drugsfda", [DRUGSFDA_ROW])
    result = catalog.ingest_dataset("drugsfda", cache_dir=str(tmp_path), keep_files=True)

    assert result.read == 1
    assert result.failed == 0
    session = SessionLocal()
    app = session.get(FDAApplicationORM, "NDA021223")
    assert app.sponsor_name == "BRISTOL MYERS SQUIBB"
    assert "ELIQUIS" in json.loads(app.brand_names)
    assert "APIXABAN" in json.loads(app.generic_names)
    assert session.query(FDAApplicationProductORM).count() == 1
    # Approval history is what answers "first approved when".
    assert session.query(FDASubmissionORM).count() == 2
    orig = session.query(FDASubmissionORM).filter_by(submission_type="ORIG").one()
    assert orig.submission_status_date == "20121228"
    assert orig.review_priority == "PRIORITY"
    session.close()


def test_reingesting_updates_rather_than_duplicating(local_partition, tmp_path):
    _clean(FDAApplicationORM, FDAApplicationProductORM, FDASubmissionORM)
    local_partition("drugsfda", [DRUGSFDA_ROW])
    catalog.ingest_dataset("drugsfda", cache_dir=str(tmp_path), keep_files=True)
    catalog.ingest_dataset("drugsfda", cache_dir=str(tmp_path), keep_files=True)

    session = SessionLocal()
    assert session.query(FDAApplicationORM).count() == 1
    assert session.query(FDAApplicationProductORM).count() == 1
    assert session.query(FDASubmissionORM).count() == 2
    session.close()


def test_enforcement_builds_searchable_recall(local_partition, tmp_path):
    _clean(DrugRecallORM)
    local_partition("enforcement", [ENFORCEMENT_ROW])
    catalog.ingest_dataset("enforcement", cache_dir=str(tmp_path), keep_files=True)

    session = SessionLocal()
    recall = session.get(DrugRecallORM, "D-1234-2026")
    assert recall.classification == "Class II"
    assert "NDMA" in recall.reason_for_recall
    # search_blob is lower-cased so one indexed LIKE covers all three columns.
    assert "metformin" in recall.search_blob
    assert "example pharma" in recall.search_blob
    session.close()


def test_shortages_are_loaded(local_partition, tmp_path):
    _clean(DrugShortageORM)
    local_partition("shortages", [SHORTAGE_ROW])
    catalog.ingest_dataset("shortages", cache_dir=str(tmp_path), keep_files=True)

    session = SessionLocal()
    row = session.query(DrugShortageORM).one()
    assert row.generic_name == "Amoxicillin Oral Suspension"
    assert row.status == "Current"
    assert row.therapeutic_category == "Anti-Infective"
    session.close()


def test_rows_without_a_natural_key_are_skipped(local_partition, tmp_path):
    _clean(DrugRecallORM)
    local_partition("enforcement", [ENFORCEMENT_ROW, {"product_description": "no recall number"}])
    result = catalog.ingest_dataset("enforcement", cache_dir=str(tmp_path), keep_files=True)

    assert result.read == 2
    session = SessionLocal()
    assert session.query(DrugRecallORM).count() == 1
    session.close()


def test_limit_is_honoured(local_partition, tmp_path):
    _clean(DrugRecallORM)
    rows = [dict(ENFORCEMENT_ROW, recall_number=f"D-{n}-2026") for n in range(30)]
    local_partition("enforcement", rows)
    result = catalog.ingest_dataset("enforcement", cache_dir=str(tmp_path), limit=8, keep_files=True)
    assert result.read == 8


def test_unknown_dataset_is_rejected(tmp_path):
    """Orange Book routes to services/orange_book.py, not here."""
    with pytest.raises(catalog.BulkUnavailable):
        catalog.ingest_dataset("orangebook", cache_dir=str(tmp_path))


def test_partition_file_is_deleted_after_load(local_partition, tmp_path):
    _clean(DrugShortageORM)
    path = local_partition("shortages", [SHORTAGE_ROW])
    catalog.ingest_dataset("shortages", cache_dir=str(tmp_path))
    assert not os.path.exists(path)
