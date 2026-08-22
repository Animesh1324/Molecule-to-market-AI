"""PubMed corpus retrieval and the regulatory fallback.

Network is mocked throughout: these pin down parsing and completeness
accounting, which must hold regardless of what NCBI returns on the day.

The bugs being guarded against are all ones that shipped:
  * a 25-record cap presented as "the literature"
  * curated molecules never querying PubMed at all
  * an unparseable publication date defaulting to the year 2024
  * articleids[0] (the PMID) being stored in the DOI field
"""
import json
from typing import Any, Dict, List

import pytest

from app.db.database import SessionLocal, init_db
from app.db.evidence_models import PubMedPaperORM, PubMedQueryORM
from app.services import pubmed_service as P

init_db()


def _summary(pmid: str, *, pubdate="2015 Nov 26", pubtypes=None,
             doi="10.1056/NEJMoa1504720") -> Dict[str, Any]:
    return {
        "uid": pmid,
        "title": f"Study {pmid}",
        "source": "N Engl J Med",
        "pubdate": pubdate,
        "authors": [{"name": "Zinman B"}, {"name": "Wanner C"}],
        "pubtype": pubtypes if pubtypes is not None else ["Randomized Controlled Trial"],
        "articleids": [
            {"idtype": "pubmed", "value": pmid},
            {"idtype": "doi", "value": doi},
            {"idtype": "pmc", "value": "PMC123"},
        ],
    }


@pytest.fixture(autouse=True)
def clean_cache():
    session = SessionLocal()
    try:
        session.query(PubMedQueryORM).delete()
        session.query(PubMedPaperORM).delete()
        session.commit()
    finally:
        session.close()
    yield


class _FakeClient:
    """Stands in for httpx.AsyncClient, serving canned E-utilities responses."""

    def __init__(self, total: int, pubdate="2015 Nov 26"):
        self.total = total
        self.pubdate = pubdate
        self.summary_calls: List[int] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None):
        params = params or {}

        class Response:
            def __init__(self, payload, text=""):
                self._payload = payload
                self.status_code = 200
                self.text = text

            def json(self):
                return self._payload

            def raise_for_status(self):
                return None

        if "esearch" in url:
            return Response({"esearchresult": {
                "count": str(self.total), "webenv": "WE1", "querykey": "1"}})
        if "esummary" in url:
            start = int(params.get("retstart", 0))
            size = int(params.get("retmax", 200))
            self.summary_calls.append(start)
            uids = [str(1000 + i) for i in range(start, min(start + size, self.total))]
            payload = {"result": {"uids": uids}}
            for uid in uids:
                payload["result"][uid] = _summary(uid, pubdate=self.pubdate)
            return Response(payload)
        if "efetch" in url:
            ids = (params.get("id") or "").split(",")
            articles = "".join(
                f"<PubmedArticle><MedlineCitation><PMID>{i}</PMID></MedlineCitation>"
                f"<Abstract><AbstractText Label='RESULTS'>Finding for {i}.</AbstractText></Abstract>"
                f"</PubmedArticle>" for i in ids if i)
            return Response({}, text=f"<PubmedArticleSet>{articles}</PubmedArticleSet>")
        raise AssertionError(f"unexpected url {url}")


@pytest.fixture()
def fake_ncbi(monkeypatch):
    def install(total, pubdate="2015 Nov 26"):
        client = _FakeClient(total, pubdate)
        monkeypatch.setattr(P.httpx, "AsyncClient", lambda **kw: client)
        return client
    return install


# --------------------------------------------------------------------------
# Query construction
# --------------------------------------------------------------------------

def test_query_searches_mesh_as_well_as_title_abstract():
    """Title/Abstract alone silently drops papers indexed only under MeSH."""
    query = P.build_query("Rosuvastatin")
    assert "[Title/Abstract]" in query and "[MeSH Terms]" in query


def test_combination_is_searched_as_an_and_of_components():
    query = P.build_query("Empagliflozin + Metformin")
    assert "Empagliflozin" in query and "Metformin" in query and " AND " in query


# --------------------------------------------------------------------------
# Completeness accounting
# --------------------------------------------------------------------------

def test_all_pages_are_fetched_not_just_the_first(fake_ncbi):
    import asyncio
    client = fake_ncbi(450)
    result = asyncio.run(P.fetch_pubmed_corpus("Testolol", max_records=450))
    assert result["fetched_count"] == 450
    assert result["complete"] is True
    # 450 records at 200 per page is three pages, not one.
    assert client.summary_calls == [0, 200, 400]


def test_true_total_is_reported_even_when_capped(fake_ncbi):
    """A partial fetch must never read as the whole literature."""
    import asyncio
    fake_ncbi(5000)
    result = asyncio.run(P.fetch_pubmed_corpus("Testolol", max_records=200))
    assert result["total_available"] == 5000
    assert result["fetched_count"] == 200
    assert result["complete"] is False


def test_page_reports_total_alongside_returned_rows(fake_ncbi):
    import asyncio
    fake_ncbi(5000)
    asyncio.run(P.fetch_pubmed_corpus("Testolol", max_records=200))
    page = asyncio.run(P.get_evidence_page("Testolol", limit=10, offset=0))
    assert page["total_available"] == 5000
    assert page["returned"] == 10
    assert page["complete"] is False


def test_offset_pages_through_the_cached_corpus(fake_ncbi):
    import asyncio
    fake_ncbi(400)
    asyncio.run(P.fetch_pubmed_corpus("Testolol", max_records=400))
    first = asyncio.run(P.get_evidence_page("Testolol", limit=5, offset=0))
    second = asyncio.run(P.get_evidence_page("Testolol", limit=5, offset=5))
    assert [p.pmid for p in first["papers"]] != [p.pmid for p in second["papers"]]


# --------------------------------------------------------------------------
# Parsing — the fabrication guards
# --------------------------------------------------------------------------

def test_unparseable_date_is_null_not_a_default_year(fake_ncbi):
    """A guessed year on a real citation is a fabricated fact."""
    import asyncio
    fake_ncbi(1, pubdate="no date recorded")
    asyncio.run(P.fetch_pubmed_corpus("Testolol"))
    session = SessionLocal()
    try:
        row = session.query(PubMedPaperORM).first()
        assert row.publication_year is None
    finally:
        session.close()


@pytest.mark.parametrize("raw,expected", [
    ("2015 Nov 26", 2015), ("2023", 2023), ("1998 Jan", 1998),
    ("", None), ("n/a", None),
])
def test_year_parsing(raw, expected):
    assert P._parse_year(raw) == expected


def test_doi_is_taken_by_id_type_not_by_position():
    """articleids[0] is the PMID; storing it as the DOI made every DOI wrong."""
    ids = P._extract_ids(_summary("999"))
    assert ids["doi"] == "10.1056/NEJMoa1504720"
    assert ids["pmcid"] == "PMC123"


def test_missing_doi_stays_none():
    item = {"articleids": [{"idtype": "pubmed", "value": "111"}]}
    assert P._extract_ids(item)["doi"] is None


def test_abstract_is_stored_and_surfaced(fake_ncbi):
    import asyncio
    fake_ncbi(2)
    asyncio.run(P.fetch_pubmed_corpus("Testolol"))
    page = asyncio.run(P.get_evidence_page("Testolol", limit=2))
    assert any("Finding for" in p.key_findings for p in page["papers"])


def test_record_without_abstract_says_so_rather_than_claiming_findings(fake_ncbi):
    import asyncio
    fake_ncbi(1)
    asyncio.run(P.fetch_pubmed_corpus("Testolol", with_abstracts=False))
    page = asyncio.run(P.get_evidence_page("Testolol", limit=1))
    assert "without an abstract" in page["papers"][0].key_findings


@pytest.mark.parametrize("pubtypes,expected", [
    (["Meta-Analysis"], "meta-analysis"),
    (["Systematic Review"], "systematic review"),
    (["Randomized Controlled Trial"], "RCT"),
    (["Case Reports"], "case report"),
    ([], "Unrated"),
])
def test_evidence_tier_is_labelled_candidate_not_asserted(pubtypes, expected):
    _, level = P._classify(pubtypes)
    assert expected.lower() in level.lower()
    if pubtypes:
        assert "candidate" in level.lower() or "unrated" in level.lower()


# --------------------------------------------------------------------------
# Curated + live merge
# --------------------------------------------------------------------------

def test_curated_molecule_still_queries_pubmed(fake_ncbi):
    """Empagliflozin used to return 4 curated papers and never search at all."""
    import asyncio
    fake_ncbi(300)
    page = asyncio.run(P.get_evidence_page("Empagliflozin", limit=50))
    assert page["total_available"] == 300
    assert len(page["papers"]) > 4


def test_curated_papers_lead_the_list(fake_ncbi):
    import asyncio
    fake_ncbi(50)
    page = asyncio.run(P.get_evidence_page("Empagliflozin", limit=50))
    assert page["papers"][0].pmid == "26378978"      # EMPA-REG OUTCOME


def test_curated_paper_is_not_duplicated_by_the_live_result(fake_ncbi, monkeypatch):
    import asyncio
    client = _FakeClient(3)
    original = client.get

    async def get(url, params=None):
        response = await original(url, params)
        if "esummary" in url:
            payload = response.json()
            # Make one live record collide with a curated PMID.
            payload["result"]["uids"][0] = "26378978"
            payload["result"]["26378978"] = _summary("26378978")
        return response

    client.get = get
    monkeypatch.setattr(P.httpx, "AsyncClient", lambda **kw: client)
    page = asyncio.run(P.get_evidence_page("Empagliflozin", limit=50))
    pmids = [p.pmid for p in page["papers"]]
    assert pmids.count("26378978") == 1


def test_cache_serves_a_second_call_without_refetching(fake_ncbi):
    import asyncio
    client = fake_ncbi(200)
    asyncio.run(P.get_evidence_page("Testolol", limit=5))
    calls_after_first = len(client.summary_calls)
    asyncio.run(P.get_evidence_page("Testolol", limit=5))
    assert len(client.summary_calls) == calls_after_first


def test_network_failure_falls_back_to_cache_rather_than_emptying(fake_ncbi, monkeypatch):
    import asyncio
    fake_ncbi(20)
    asyncio.run(P.fetch_pubmed_corpus("Testolol"))

    class Broken:
        async def __aenter__(self): return self
        async def __aexit__(self, *e): return False
        async def get(self, *a, **k): raise RuntimeError("NCBI unreachable")

    monkeypatch.setattr(P.httpx, "AsyncClient", lambda **kw: Broken())
    page = asyncio.run(P.get_evidence_page("Testolol", limit=5, refresh=True))
    assert len(page["papers"]) > 0


# --------------------------------------------------------------------------
# _store round-trip cost
#
# The original implementation ran session.get(PubMedPaperORM, pmid) once per
# record inside the write loop — cheap on local SQLite, where a round trip is
# free, but a real network hop per paper against a remote database. A batch of
# 2000 papers meant 2000 sequential SELECTs before any write happened. The
# fix partitions new-vs-existing with one upfront IN-query and writes each
# group with a single bulk_insert_mappings/bulk_update_mappings call. These
# tests assert the SELECT count directly so a future edit that reintroduces
# a per-row lookup fails loudly instead of only showing up as latency in
# production.
# --------------------------------------------------------------------------

def _count_selects(engine, fn):
    """Run fn() and return how many SELECT statements it issued."""
    from sqlalchemy import event

    count = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal count
        if statement.strip().upper().startswith("SELECT"):
            count += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
    return count


def test_store_select_count_does_not_scale_with_batch_size(fake_ncbi):
    """A 50-paper batch must not cost 10x the SELECTs of a 5-paper one.

    fetch_pubmed_corpus also does one constant-cost lookup of its own query
    state (_save_query), so the floor is a small fixed number, not zero or one
    — what matters is that it stays FIXED as record count grows, rather than
    growing with it the way a per-row session.get() would.

    The fake client's PMIDs start at 1000 on every call, so a larger corpus
    fetched second would legitimately collide with the smaller one's IDs and
    hit the update branch instead of the insert one. The table is cleared
    between the two fetches so both are genuinely pure inserts — the
    comparison this test makes.
    """
    import asyncio
    from app.db.database import engine

    fake_ncbi(5)
    small_selects = _count_selects(
        engine, lambda: asyncio.run(P.fetch_pubmed_corpus("Testolol", max_records=5)))

    session = SessionLocal()
    try:
        session.query(PubMedPaperORM).delete()
        session.commit()
    finally:
        session.close()

    fake_ncbi(50)
    large_selects = _count_selects(
        engine, lambda: asyncio.run(P.fetch_pubmed_corpus("Testolol2", max_records=50)))

    assert small_selects == large_selects


def test_reingesting_the_same_pmids_updates_without_a_select_per_row(fake_ncbi):
    """Re-fetching an already-cached corpus exercises the update branch.

    An all-updates pass costs one more SELECT than an all-inserts pass (the
    existing-abstracts lookup), but that extra cost must stay fixed as the
    number of already-cached PMIDs grows — never one lookup per row.
    """
    import asyncio
    from app.db.database import engine

    fake_ncbi(20)
    asyncio.run(P.fetch_pubmed_corpus("Testolol3", max_records=20))
    # Every one of these 20 PMIDs now exists, so this refetch is pure update.
    small_update_selects = _count_selects(
        engine, lambda: asyncio.run(P.fetch_pubmed_corpus("Testolol3", max_records=20)))

    fake_ncbi(200)
    asyncio.run(P.fetch_pubmed_corpus("Testolol4", max_records=200))
    # 200 already-cached PMIDs — ten times the previous batch.
    large_update_selects = _count_selects(
        engine, lambda: asyncio.run(P.fetch_pubmed_corpus("Testolol4", max_records=200)))

    assert small_update_selects == large_update_selects


def test_mixed_new_and_existing_pmids_are_both_written_correctly(fake_ncbi):
    """One _store() call spanning new and already-cached PMIDs upserts both."""
    import asyncio

    fake_ncbi(10)
    asyncio.run(P.fetch_pubmed_corpus("Testolol4", max_records=10))

    # Grow the corpus: the first 10 PMIDs are now "existing", the next 10 are new.
    fake_ncbi(20)
    asyncio.run(P.fetch_pubmed_corpus("Testolol4", max_records=20))

    session = SessionLocal()
    try:
        stored = {row.pmid for row in session.query(PubMedPaperORM.pmid).all()}
    finally:
        session.close()
    assert len(stored) == 20
