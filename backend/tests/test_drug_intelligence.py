"""Tests for the Drug Intelligence module.

Network-free: the openFDA adapter is substituted with a fake so the suite is
deterministic and CI needs no outbound access. The tests that matter most here
are the failure paths — an upstream being down, unlicensed, or slow must never
take the application with it.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.data_sources.base import (
    DrugRecord,
    InteractionRecord,
    SourceAttribution,
    SourceNotPermitted,
    SourceUnavailable,
)
from app.data_sources.drugs_com_source import DrugsComSource
from app.data_sources.manual_source import ManualImportSource
from app.main import app
from app.repositories import drug_repository as repo
from app.services import drug_ingestion_service as ingestion

client = TestClient(app)


def _record(generic="Testolol", brand="Testabrand", **kwargs) -> DrugRecord:
    record = DrugRecord(
        generic_name=generic,
        brand_name=brand,
        active_ingredients=[generic],
        drug_class="Beta-Adrenergic Blocker [EPC]",
        therapeutic_class="Antihypertensive",
        dosage_forms=["TABLET"],
        strengths=["10 mg"],
        routes=["ORAL"],
        indications="Indicated for hypertension.",
        dosage="10 mg once daily.",
        contraindications="Severe bradycardia.",
        warnings="Do not stop abruptly.",
        adverse_effects="Fatigue, dizziness.",
        pregnancy_information="Risk summary text.",
        mechanism="Blocks beta-1 receptors.",
        manufacturer="Test Pharma Ltd",
        attribution=SourceAttribution(
            source_name="openFDA",
            source_url="https://open.fda.gov/apis/drug/label/",
            source_identifier="TEST-1",
            confidence="verified",
        ),
    )
    for key, value in kwargs.items():
        setattr(record, key, value)
    return record


class _FakeSource:
    """Stand-in adapter whose behaviour each test dictates."""

    name = "openFDA"
    enabled = True
    access_policy = "test double"

    def __init__(self, records=None, error=None, interactions=None, delay=0.0):
        self._records = records or []
        self._error = error
        self._interactions = interactions or []
        self._delay = delay

    async def fetch(self, query):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._error:
            raise self._error
        return self._records

    async def fetch_interactions(self, query):
        return self._interactions

    def describe(self):
        return {"name": self.name, "enabled": self.enabled,
                "access_policy": self.access_policy, "supports_interactions": True}


@pytest.fixture(autouse=True)
def _clean_drug_tables():
    """Each test starts from an empty drug table."""
    from app.db.database import SessionLocal
    from app.db.drug_models import DrugInteractionORM, DrugORM

    session = SessionLocal()
    session.query(DrugORM).delete()
    session.query(DrugInteractionORM).delete()
    session.commit()
    session.close()
    ingestion._failures.clear()
    ingestion._opened_at.clear()
    yield


def _run(coro):
    return asyncio.run(coro)


# --- persistence, attribution, dedup ----------------------------------------

def test_drug_creation_and_retrieval():
    drug_id = repo.upsert_drug(_record())
    stored = repo.get_drug(drug_id)
    assert stored["generic_name"] == "Testolol"
    assert stored["strengths"] == ["10 mg"]
    assert stored["indications"].startswith("Indicated")


def test_source_attribution_is_always_recorded():
    drug_id = repo.upsert_drug(_record())
    sources = repo.get_drug(drug_id)["sources"]
    assert len(sources) == 1
    assert sources[0]["source_name"] == "openFDA"
    assert sources[0]["confidence"] == "verified"
    assert sources[0]["retrieved_at"]


def test_duplicate_ingestion_updates_rather_than_duplicating():
    first = repo.upsert_drug(_record())
    second = repo.upsert_drug(_record())
    assert first == second
    assert repo.count_drugs() == 1


def test_brand_case_variants_do_not_create_duplicates():
    """openFDA returns both 'Ozempic' and 'OZEMPIC'; they are one drug."""
    repo.upsert_drug(_record(brand="Testabrand"))
    repo.upsert_drug(_record(brand="TESTABRAND"))
    assert repo.count_drugs() == 1


def test_empty_values_never_erase_existing_data():
    """A thin re-ingest must not blank a field another source populated."""
    repo.upsert_drug(_record())
    repo.upsert_drug(_record(indications=None, warnings=None))
    stored = repo.find_by_name("Testolol")[0]
    assert stored["indications"].startswith("Indicated")
    assert stored["warnings"] == "Do not stop abruptly."


def test_generic_name_is_required():
    with pytest.raises(ValueError):
        ManualImportSource.to_record({"brand_name": "OnlyBrand"})


# --- search ------------------------------------------------------------------

def test_search_matches_brand_generic_class_and_strength():
    repo.upsert_drug(_record())
    for term in ("Testolol", "Testabrand", "Antihypertensive", "10 mg", "TABLET"):
        rows, total = repo.search_drugs(term.lower())
        assert total >= 1, term


def test_search_tolerates_case_and_whitespace():
    repo.upsert_drug(_record())
    for term in ("TESTOLOL", "  testolol  ", "TeStOlOl"):
        result = _run(_search(term))
        assert result.total >= 1, term


async def _search(term, **kwargs):
    from app.services import drug_search_service
    kwargs.setdefault("ingest_if_missing", False)
    return await drug_search_service.search(term, **kwargs)


def test_search_expands_class_shorthand_and_inn_names():
    from app.services.drug_search_service import expand_terms
    assert any("glucagon-like" in t for t in expand_terms("GLP-1"))
    assert "acetaminophen" in expand_terms("paracetamol")
    assert "metformin" in expand_terms("metformin hydrochloride")
    # A combination expands to its components.
    assert "empagliflozin" in expand_terms("Empagliflozin + Metformin")


def test_empty_search_returns_guidance_not_error():
    result = _run(_search(""))
    assert result.total == 0
    assert result.note


def test_pagination_reports_totals_and_has_more():
    for i in range(5):
        repo.upsert_drug(_record(generic=f"Testdrug{i}", brand=f"Brand{i}"))
    response = client.get("/api/drugs?page=1&page_size=2")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["has_more"] is True


def test_class_filter_endpoint():
    repo.upsert_drug(_record())
    response = client.get("/api/drugs/class/Antihypertensive")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


# --- comparison --------------------------------------------------------------

def test_comparison_reports_missing_fields_rather_than_inventing():
    repo.upsert_drug(_record(generic="Alpha", brand="AlphaBrand"))
    repo.upsert_drug(_record(generic="Beta", brand="BetaBrand", mechanism=None))
    response = client.post(
        "/api/drugs/compare",
        json={"drug_a": "Alpha", "drug_b": "Beta", "ingest_if_missing": False},
    )
    assert response.status_code == 200
    body = response.json()
    mechanism = next(f for f in body["fields"] if f["field"] == "mechanism")
    assert mechanism["drug_b_value"] == "Information not available"
    assert mechanism["both_available"] is False
    # A missing value must never be reported as a difference.
    assert mechanism["differs"] is False
    assert "not a clinical assessment" in body["caveat"]


def test_comparison_handles_one_missing_drug():
    repo.upsert_drug(_record(generic="Alpha", brand="AlphaBrand"))
    response = client.post(
        "/api/drugs/compare",
        json={"drug_a": "Alpha", "drug_b": "NoSuchMolecule", "ingest_if_missing": False},
    )
    assert response.status_code == 200
    assert "one-sided" in response.json()["comparison_note"]


# --- interactions ------------------------------------------------------------

def test_interaction_pair_is_normalised_and_deduped():
    attribution = SourceAttribution(source_name="test-feed")
    repo.upsert_interaction(InteractionRecord(
        drug_a="Zebra", drug_b="Alpha", severity="major",
        description="Test", attribution=attribution,
    ))
    repo.upsert_interaction(InteractionRecord(
        drug_a="Alpha", drug_b="Zebra", severity="major",
        description="Test", attribution=attribution,
    ))
    rows = repo.interactions_for("Alpha")
    assert len(rows) == 1
    assert rows[0]["drug_a"] == "Alpha" and rows[0]["drug_b"] == "Zebra"


def test_interactions_endpoint_explains_absence():
    drug_id = repo.upsert_drug(_record())
    body = client.get(f"/api/drugs/{drug_id}/interactions").json()
    assert body["total"] == 0
    assert "licensed interaction feed" in body["coverage_note"]


# --- source policy and failure handling --------------------------------------

def test_drugs_com_is_disabled_without_a_licence(monkeypatch):
    monkeypatch.delenv("DRUGS_COM_API_KEY", raising=False)
    source = DrugsComSource()
    assert source.enabled is False
    with pytest.raises(SourceNotPermitted):
        _run(source.fetch("semaglutide"))


def test_drugs_com_policy_states_no_scraping():
    policy = DrugsComSource().access_policy.lower()
    assert "licensed" in policy
    assert "never scraped" in policy or "no scraping" in policy


def test_source_registry_lists_adapters_and_policy():
    body = client.get("/api/drugs/sources/registry").json()
    names = {s["name"] for s in body["sources"]}
    assert {"openFDA", "Drugs.com", "Manual import"} <= names
    assert "never scraped" in body["policy"].lower()


def test_source_failure_does_not_crash_the_application(monkeypatch):
    """An upstream outage degrades the result; it must not raise."""
    monkeypatch.setattr(
        ingestion, "_registry",
        lambda: [_FakeSource(error=SourceUnavailable("upstream down"))],
    )
    outcomes = _run(ingestion.ingest_query("anything"))
    assert outcomes[0].succeeded is False
    assert "upstream down" in outcomes[0].message
    # And the API still answers.
    assert client.get("/api/drugs?page=1&page_size=5").status_code == 200


def test_source_timeout_is_bounded(monkeypatch):
    monkeypatch.setattr(ingestion, "SOURCE_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(ingestion, "_registry", lambda: [_FakeSource(delay=0.5)])
    outcomes = _run(ingestion.ingest_query("slow"))
    assert outcomes[0].succeeded is False
    assert "timed out" in outcomes[0].message.lower()


def test_adapter_bug_is_contained(monkeypatch):
    """A programming error inside an adapter must not become a 500."""
    monkeypatch.setattr(
        ingestion, "_registry",
        lambda: [_FakeSource(error=ValueError("adapter bug"))],
    )
    outcomes = _run(ingestion.ingest_query("anything"))
    assert outcomes[0].succeeded is False
    assert "adapter error" in outcomes[0].message.lower()


def test_circuit_opens_after_repeated_failures(monkeypatch):
    monkeypatch.setattr(
        ingestion, "_registry",
        lambda: [_FakeSource(error=SourceUnavailable("down"))],
    )
    for _ in range(ingestion._FAILURE_THRESHOLD):
        _run(ingestion.ingest_query("q"))
    outcomes = _run(ingestion.ingest_query("q"))
    assert "circuit open" in outcomes[0].message.lower()


def test_successful_ingestion_persists_and_logs(monkeypatch):
    monkeypatch.setattr(ingestion, "_registry", lambda: [_FakeSource(records=[_record()])])
    outcomes = _run(ingestion.ingest_query("testolol"))
    assert outcomes[0].succeeded is True
    assert outcomes[0].records_written == 1
    assert repo.count_drugs() == 1
    assert any(e["source_name"] == "openFDA" for e in repo.recent_ingestions())


# --- manual import and PMT ---------------------------------------------------

def test_manual_import_is_marked_user_entered():
    response = client.post("/api/drugs/manual", json={
        "generic_name": "Indiaonlymol",
        "brand_name": "Localbrand",
        "indications": "Approved in India only.",
        "source_note": "From CDSCO approval PDF",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["sources"][0]["confidence"] == "user-entered"


def test_manual_import_ignores_unexpected_fields():
    record = ManualImportSource.to_record(
        {"generic_name": "Testolol", "id": "injected", "status": "active"}
    )
    assert record.generic_name == "Testolol"
    assert "id" not in record.extra


def test_pmt_analysis_is_labelled_as_generated():
    repo.upsert_drug(_record())
    body = client.get("/api/drugs/pmt/Testolol").json()
    assert body["analysis_type"] == "AI/Software Analysis"
    assert "not a statement from any regulator" in body["disclaimer"].lower()
    assert body["source_records_used"]


def test_pmt_reports_gap_when_drug_is_unknown():
    body = client.get("/api/drugs/pmt/NoSuchMoleculeAtAll").json()
    assert body["evidence_gaps"]
    assert not body["positioning_observations"]


# --- API contract ------------------------------------------------------------

def test_invalid_drug_id_returns_404():
    assert client.get("/api/drugs/doesnotexist").status_code == 404
    assert client.get("/api/drugs/doesnotexist/sources").status_code == 404


def test_page_size_is_capped():
    assert client.get("/api/drugs?page_size=9999").status_code == 422


def test_response_schema_shape():
    drug_id = repo.upsert_drug(_record())
    body = client.get(f"/api/drugs/{drug_id}").json()
    for key in ("id", "generic_name", "brand_name", "sources", "indications",
                "contraindications", "pregnancy_information", "mechanism"):
        assert key in body, key


def test_api_docs_are_not_public_in_production(monkeypatch):
    """The schema enumerates every route; it must not be readable unauthenticated."""
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_ACCESS_TOKEN", "token-for-test")
    try:
        import importlib
        from app import main as main_module

        reloaded = importlib.reload(main_module)
        assert reloaded.app.openapi_url is None
        assert reloaded.app.docs_url is None
    finally:
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
        get_settings.cache_clear()
        import importlib
        from app import main as main_module
        importlib.reload(main_module)


def test_search_prefers_records_carrying_label_content():
    """A bulk-ingredient listing must not outrank the finished product.

    The NDC directory lists raw active-ingredient consignments under the same
    generic name as the marketed drug, with no brand, class, or label. Before
    the completeness tie-break these won their tier on alphabetical order.
    """
    repo.upsert_drug(DrugRecord(
        generic_name="Rankolimus",
        brand_name=None,
        manufacturer="Aaa Bulk Chemicals Ltd",
        attribution=SourceAttribution(source_name="test-bulk"),
    ))
    repo.upsert_drug(DrugRecord(
        generic_name="Rankolimus",
        brand_name="Zzzbrand",
        drug_class="Kinase Inhibitor [EPC]",
        indications="Indicated for a documented condition.",
        attribution=SourceAttribution(source_name="test-finished"),
    ))

    rows, total = repo.search_drugs("rankolimus", page_size=10)
    assert total >= 2
    assert rows[0]["brand_name"] == "Zzzbrand"
    assert rows[0]["indications"]


def test_search_completeness_never_overrides_name_relevance():
    """Tie-breakers rank within a tier, never across tiers."""
    repo.upsert_drug(DrugRecord(
        generic_name="Exactonel",
        brand_name=None,
        attribution=SourceAttribution(source_name="test-exact"),
    ))
    repo.upsert_drug(DrugRecord(
        generic_name="Exactonel Extended Release Complex",
        brand_name="Richbrand",
        drug_class="Some Class [EPC]",
        indications="A rich record that is nonetheless a weaker name match.",
        attribution=SourceAttribution(source_name="test-rich"),
    ))

    rows, _ = repo.search_drugs("exactonel", page_size=10)
    # Exact name wins despite carrying no label content.
    assert rows[0]["generic_name"] == "Exactonel"
