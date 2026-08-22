"""Market intelligence: ingestion, normalisation, and competitor merging.

The properties worth pinning down here are the ones a wrong answer would make
expensive: that a molecule absent from every extract yields nothing rather than
a plausible guess, that combination products still count as competitors, and
that re-ingesting a period replaces it instead of doubling the market.
"""
import csv
import os

import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.services import market_data_service as market

# Tables must exist before the first direct service call; TestClient lifespan
# does not fire early enough for fixtures that bypass the HTTP layer.
init_db()

client = TestClient(app)


ROWS = [
    # molecule,                    brand,      company,        group,             subgroup,             MAT AUG'24, MAT AUG'23
    ("EMPAGLIFLOZIN",              "JARDIANCE", "BOEHRINGER",  "A10B ORAL ANTIDIABETICS", "A10B13 EMPAGLIFLOZIN", 228.42, 219.6),
    ("EMPAGLIFLOZIN",              "GIBTULIO",  "LUPIN",       "A10B ORAL ANTIDIABETICS", "A10B13 EMPAGLIFLOZIN", 84.83, 89.0),
    ("EMPAGLIFLOZIN + LINAGLIPTIN","GLYXAMBI",  "BOEHRINGER",  "A10B ORAL ANTIDIABETICS", "A10B28 EMPA+LINA",     153.88, 164.0),
    ("SITAGLIPTIN PHOSPHATE",      "JANUVIA",   "MSD",         "A10B ORAL ANTIDIABETICS", "A10B09 SITAGLIPTIN",   300.00, 280.0),
    ("ROSUVASTATIN CALCIUM",       "ROSUVAS",   "SUN",         "C10A STATINS",            "C10A04 ROSUVASTATIN",  473.76, 386.4),
]


@pytest.fixture()
def extract(tmp_path):
    """A minimal CSV in the shape of an audit extract."""
    path = tmp_path / "TEST_EXTRACT.csv"
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MOLECULE_DESC", "BRANDS", "COMPANY", "GROUP", "SUBGROUP",
                         "MAT AUG'24", "MAT AUG'23"])
        writer.writerows(ROWS)
    return str(path)


@pytest.fixture()
def ingested(extract):
    summary = market.ingest_market_file(extract, source_label="Test extract", market="India")
    yield summary
    market.delete_dataset(summary["dataset_id"])


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("ROSUVASTATIN CALCIUM", "ROSUVASTATIN"),
    ("PANTOPRAZOLE SODIUM SALT", "PANTOPRAZOLE"),
    ("EMPAGLIFLOZIN + LINAGLIPTIN", "EMPAGLIFLOZIN+LINAGLIPTIN"),
    ("Semaglutide", "SEMAGLUTIDE"),
    ("", ""),
])
def test_normalise_molecule(raw, expected):
    assert market.normalise_molecule(raw) == expected


def test_salt_only_name_is_not_stripped_to_nothing():
    """"SODIUM CHLORIDE" is a molecule, not a salt form of one."""
    assert market.normalise_molecule("SODIUM CHLORIDE") == "SODIUMCHLORIDE"


# --------------------------------------------------------------------------
# Ingestion
# --------------------------------------------------------------------------

def test_ingest_reads_every_row(ingested):
    assert ingested["rows_ingested"] == len(ROWS)
    assert ingested["brands"] == len(ROWS)
    assert ingested["period_label"] == "MAT AUG'24"


def test_latest_period_is_chosen_over_earlier_one(ingested):
    """Columns are not in a guaranteed order; the newest MAT must win."""
    result = market.brand_competitors("Empagliflozin")
    jardiance = next(b for b in result["brands"] if b["brand"] == "JARDIANCE")
    assert jardiance["value_latest"] == pytest.approx(228.42)
    assert jardiance["value_prev"] == pytest.approx(219.6)


def test_reingesting_same_file_replaces_rather_than_doubles(extract):
    first = market.ingest_market_file(extract, source_label="Test extract")
    second = market.ingest_market_file(extract, source_label="Test extract")
    try:
        assert second["replaced_datasets"] == 1
        result = market.brand_competitors("Rosuvastatin")
        # One dataset's worth of value, not two.
        assert result["market_size"] == pytest.approx(473.76)
    finally:
        market.delete_dataset(second["dataset_id"])
        market.delete_dataset(first["dataset_id"])


def test_unparseable_file_is_rejected_not_silently_empty(tmp_path):
    path = tmp_path / "notes.csv"
    path.write_text("some,unrelated,columns\n1,2,3\n")
    assert market.looks_like_market_extract(str(path)) is False
    with pytest.raises(ValueError):
        market.ingest_market_file(str(path))


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------

def test_combination_brand_counts_as_a_competitor(ingested):
    """Glyxambi contains empagliflozin and competes for the same script."""
    brands = {b["brand"] for b in market.brand_competitors("Empagliflozin")["brands"]}
    assert {"JARDIANCE", "GIBTULIO", "GLYXAMBI"} <= brands


def test_market_share_sums_to_one_hundred(ingested):
    result = market.brand_competitors("Empagliflozin")
    total = sum(b["market_share_percent"] for b in result["brands"])
    assert total == pytest.approx(100.0, abs=0.1)


def test_growth_is_computed_against_prior_period(ingested):
    result = market.brand_competitors("Empagliflozin")
    gibtulio = next(b for b in result["brands"] if b["brand"] == "GIBTULIO")
    # 84.83 from 89.0 is a decline.
    assert gibtulio["growth_percent"] < 0


def test_class_rivals_exclude_the_subject_molecule(ingested):
    rivals = market.class_competitors("Empagliflozin")
    assert rivals["group"] == "A10B ORAL ANTIDIABETICS"
    keys = [r["molecule_key"] for r in rivals["molecules"]]
    assert "SITAGLIPTIN" in keys
    assert not any("EMPAGLIFLOZIN" in (k or "") for k in keys)


def test_company_leaderboard_aggregates_across_brands(ingested):
    companies = {c["company"]: c for c in market.company_leaderboard("Empagliflozin")}
    # Boehringer holds Jardiance and Glyxambi.
    assert companies["BOEHRINGER"]["brand_count"] == 2
    assert companies["BOEHRINGER"]["value_latest"] == pytest.approx(228.42 + 153.88)


def test_unknown_molecule_returns_empty_not_a_guess(ingested):
    result = market.brand_competitors("Fictitiousmab")
    assert result["brands"] == []
    assert result["market_size"] == 0.0


# --------------------------------------------------------------------------
# Competitor module integration
# --------------------------------------------------------------------------

def test_competitor_endpoint_exposes_market_brands(ingested):
    response = client.get("/api/competitors/landscape", params={"molecule": "Rosuvastatin"})
    assert response.status_code == 200
    body = response.json()
    assert body["market_summary"]["has_data"] is True
    assert body["market_summary"]["market_size"] == pytest.approx(473.76)
    market_rows = [c for c in body["competitors"] if c["data_source"] == "secondary_market"]
    assert market_rows and market_rows[0]["brand_name"] == "ROSUVAS"
    assert market_rows[0]["company"] == "SUN"


def test_market_rows_carry_no_invented_strategy_text(ingested):
    """An audit extract measures sales; it says nothing about positioning."""
    body = client.get("/api/competitors/landscape",
                      params={"molecule": "Rosuvastatin"}).json()
    row = next(c for c in body["competitors"] if c["data_source"] == "secondary_market")
    assert row["positioning"] == ""
    assert row["doctor_messaging"] == ""
    assert row["key_claims"] == []


def test_curated_molecule_keeps_its_curated_rows(ingested):
    body = client.get("/api/competitors/landscape",
                      params={"molecule": "Empagliflozin"}).json()
    sources = {c["data_source"] for c in body["competitors"]}
    assert sources == {"curated", "secondary_market"}
    assert "Curated competitor research" in body["data_sources"]


def test_molecule_with_no_extract_reports_no_data(ingested):
    body = client.get("/api/competitors/landscape",
                      params={"molecule": "Fictitiousmab"}).json()
    assert body["market_summary"]["has_data"] is False
    assert body["competitors"] == []
    assert "No source-backed competitor matrix" in body["positioning_gap_summary"]


def test_market_endpoints_are_reachable(ingested):
    assert client.get("/api/market/datasets").status_code == 200
    assert client.get("/api/market/brands", params={"molecule": "Rosuvastatin"}).status_code == 200
    assert client.get("/api/market/companies", params={"molecule": "Rosuvastatin"}).status_code == 200
    assert client.get("/api/market/class", params={"molecule": "Rosuvastatin"}).status_code == 200
    assert client.get("/api/market/search", params={"q": "ROSUVAS"}).status_code == 200


def test_search_matches_brand_molecule_and_company(ingested):
    assert any(r["brand"] == "ROSUVAS" for r in market.search_brands("rosuvas"))
    assert any(r["brand"] == "JANUVIA" for r in market.search_brands("sitagliptin"))
    assert any(r["company"] == "LUPIN" for r in market.search_brands("lupin"))


def test_ingest_path_endpoint_rejects_a_missing_file():
    response = client.post("/api/market/ingest/path", json={"path": "/no/such/file.xlsx"})
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Period isolation
#
# Two extracts covering different periods must never be summed. Before this was
# enforced, loading a June'26 refresh alongside an Aug'24 base produced a market
# size that was the sum of both periods and listed the same brand twice.
# --------------------------------------------------------------------------

NEWER_ROWS = [
    ("SEMAGLUTIDE", "RYBELSUS", "ABBOTT", "A10S GLP1", "A10S01 SEMAGLUTIDE", 649.00, 395.00),
    ("SEMAGLUTIDE", "SEMAVIA", "DR REDDYS", "A10S GLP1", "A10S01 SEMAGLUTIDE", 88.50, 0.0),
]
OLDER_ROWS = [
    ("SEMAGLUTIDE", "RYBELSUS", "ABBOTT", "A10S GLP1", "A10S01 SEMAGLUTIDE", 330.52, 200.0),
]


def _write(tmp_path, name, rows, latest, prev):
    path = tmp_path / name
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["MOLECULE_DESC", "BRANDS", "COMPANY", "GROUP", "SUBGROUP", latest, prev])
        writer.writerows(rows)
    return str(path)


@pytest.fixture()
def two_periods(tmp_path):
    older = market.ingest_market_file(
        _write(tmp_path, "BASE_AUG24.csv", OLDER_ROWS, "MAT AUG'24", "MAT AUG'23"))
    newer = market.ingest_market_file(
        _write(tmp_path, "REFRESH_JUN26.csv", NEWER_ROWS, "MAT JUN'26", "MAT JUN'25"))
    yield older, newer
    market.delete_dataset(newer["dataset_id"])
    market.delete_dataset(older["dataset_id"])


def test_newest_period_wins_and_older_is_not_added(two_periods):
    result = market.brand_competitors("Semaglutide")
    assert result["period"] == "MAT JUN'26"
    # 649 + 88.5 from the newer file only — not 1122 across both periods.
    assert result["market_size"] == pytest.approx(737.5)


def test_a_brand_is_never_listed_twice_across_periods(two_periods):
    brands = [b["brand"] for b in market.brand_competitors("Semaglutide")["brands"]]
    assert brands.count("RYBELSUS") == 1


def test_upload_order_does_not_decide_which_period_is_current(tmp_path):
    """An older extract loaded last must not override a newer period."""
    newer = market.ingest_market_file(
        _write(tmp_path, "R_JUN26.csv", NEWER_ROWS, "MAT JUN'26", "MAT JUN'25"))
    older = market.ingest_market_file(
        _write(tmp_path, "B_AUG24.csv", OLDER_ROWS, "MAT AUG'24", "MAT AUG'23"))
    try:
        assert market.brand_competitors("Semaglutide")["period"] == "MAT JUN'26"
    finally:
        market.delete_dataset(older["dataset_id"])
        market.delete_dataset(newer["dataset_id"])


def test_older_dataset_still_answers_molecules_the_newer_one_lacks(two_periods, extract):
    """Scoping to one dataset per molecule must not hide unrelated coverage."""
    other = market.ingest_market_file(extract, source_label="Test extract")
    try:
        # Rosuvastatin exists only in the third file and must still resolve.
        assert market.brand_competitors("Rosuvastatin")["market_size"] == pytest.approx(473.76)
        # Semaglutide still reads from the newest file that carries it.
        assert market.brand_competitors("Semaglutide")["period"] == "MAT JUN'26"
    finally:
        market.delete_dataset(other["dataset_id"])


def test_company_and_class_views_use_the_same_period(two_periods):
    companies = market.company_leaderboard("Semaglutide")
    assert {c["company"] for c in companies} == {"ABBOTT", "DR REDDYS"}
    assert sum(c["market_share_percent"] for c in companies) == pytest.approx(100.0, abs=0.1)
