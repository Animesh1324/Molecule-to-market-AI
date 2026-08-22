"""Generic get-or-fetch caching for expensive external lookups.

The property that matters: a fetch actually happens on a miss and is skipped
entirely on a hit, and an expired entry is treated as a miss. Verified live
before writing this: fetch_regulatory_intelligence/fetch_molecule_intelligence
went from 5-10s to effectively 0s on a cached repeat call.
"""
import asyncio
from datetime import datetime, timedelta

import pytest

from app.db.database import SessionLocal, init_db
from app.db.response_cache_models import ResponseCacheORM
from app.services import response_cache as C

init_db()


@pytest.fixture(autouse=True)
def clean_cache():
    session = SessionLocal()
    try:
        session.query(ResponseCacheORM).filter(
            ResponseCacheORM.cache_key.like("test:%")).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
    yield


class _Counter:
    """A fake fetcher whose call count proves whether the cache was used."""
    def __init__(self, value: dict):
        self.value = value
        self.calls = 0

    async def fetch(self):
        self.calls += 1
        return dict(self.value)


def test_first_call_is_a_miss_and_calls_the_fetcher():
    counter = _Counter({"x": 1})
    result = asyncio.run(C.get_or_fetch(
        "test:a", 24, counter.fetch, lambda d: d, lambda d: d))
    assert result == {"x": 1}
    assert counter.calls == 1


def test_second_call_is_a_hit_and_does_not_call_the_fetcher():
    counter = _Counter({"x": 1})
    asyncio.run(C.get_or_fetch("test:b", 24, counter.fetch, lambda d: d, lambda d: d))
    asyncio.run(C.get_or_fetch("test:b", 24, counter.fetch, lambda d: d, lambda d: d))
    assert counter.calls == 1


def test_different_keys_are_cached_independently():
    counter = _Counter({"x": 1})
    asyncio.run(C.get_or_fetch("test:c1", 24, counter.fetch, lambda d: d, lambda d: d))
    asyncio.run(C.get_or_fetch("test:c2", 24, counter.fetch, lambda d: d, lambda d: d))
    assert counter.calls == 2


def test_an_expired_entry_is_treated_as_a_miss():
    session = SessionLocal()
    try:
        session.add(ResponseCacheORM(
            cache_key="test:expired",
            payload_json='{"x": 1}',
            fetched_at=(datetime.now() - timedelta(hours=200)).strftime("%Y-%m-%d %H:%M:%S"),
        ))
        session.commit()
    finally:
        session.close()

    counter = _Counter({"x": 2})
    result = asyncio.run(C.get_or_fetch("test:expired", 24, counter.fetch, lambda d: d, lambda d: d))
    assert counter.calls == 1
    assert result == {"x": 2}


def test_a_fresh_entry_within_ttl_is_used():
    session = SessionLocal()
    try:
        session.add(ResponseCacheORM(
            cache_key="test:fresh",
            payload_json='{"x": 99}',
            fetched_at=(datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        ))
        session.commit()
    finally:
        session.close()

    counter = _Counter({"x": 2})
    result = asyncio.run(C.get_or_fetch("test:fresh", 24, counter.fetch, lambda d: d, lambda d: d))
    assert counter.calls == 0
    assert result == {"x": 99}


def test_to_dict_and_from_dict_round_trip_a_custom_object():
    class Thing:
        def __init__(self, value):
            self.value = value

    async def fetch():
        return Thing(42)

    result = asyncio.run(C.get_or_fetch(
        "test:roundtrip", 24, fetch,
        to_dict=lambda t: {"value": t.value},
        from_dict=lambda d: Thing(d["value"]),
    ))
    assert result.value == 42

    result2 = asyncio.run(C.get_or_fetch(
        "test:roundtrip", 24, fetch,
        to_dict=lambda t: {"value": t.value},
        from_dict=lambda d: Thing(d["value"]),
    ))
    assert result2.value == 42


def test_a_none_result_is_never_cached():
    """A miss that legitimately found nothing must not freeze that absence —
    the molecule might resolve on a future attempt (a new synonym mapping, a
    newly published label). Caching None would make that permanent.
    """
    calls = {"n": 0}

    async def fetch():
        calls["n"] += 1
        return None

    asyncio.run(C.get_or_fetch("test:none", 24, fetch, lambda d: d, lambda d: d))
    asyncio.run(C.get_or_fetch("test:none", 24, fetch, lambda d: d, lambda d: d))
    assert calls["n"] == 2


# --------------------------------------------------------------------------
# Wiring: the two real call sites this was built for
# --------------------------------------------------------------------------

def test_regulatory_intelligence_is_cached_end_to_end(monkeypatch):
    from app.services import regulatory_service as R
    from app.models.regulatory import RegulatoryIntelligence, RegulatoryAgencyInfo

    calls = {"n": 0}

    async def fake_impl(molecule_name):
        calls["n"] += 1
        agency = RegulatoryAgencyInfo(agency_name="Test", status="Test status")
        return RegulatoryIntelligence(
            generic_name=molecule_name, us_fda=agency, india_cdsco=agency, eu_ema=agency,
            generic_vs_innovator_status="Test", ai_strategic_interpretation=[],
            compliance_fair_balance_notes="Test",
        )

    monkeypatch.setattr(R, "_fetch_regulatory_intelligence_impl", fake_impl)
    asyncio.run(R.fetch_regulatory_intelligence("TestMoleculeXYZ"))
    asyncio.run(R.fetch_regulatory_intelligence("TestMoleculeXYZ"))
    assert calls["n"] == 1


def test_molecule_intelligence_is_cached_end_to_end(monkeypatch):
    from app.services import pubchem_service as P
    from app.models.molecule import MoleculeProfile, Pharmacokinetics, AdverseEffects, SpecialPopulations

    calls = {"n": 0}

    async def fake_impl(molecule_name):
        calls["n"] += 1
        return MoleculeProfile(
            generic_name=molecule_name, chemical_class="Test", pharmacological_class="Test",
            mechanism_of_action="Test", pharmacodynamics="Test",
            pharmacokinetics=Pharmacokinetics(), adverse_effects=AdverseEffects(),
            special_populations=SpecialPopulations(), differentiating_science="Test",
        )

    monkeypatch.setattr(P, "_fetch_molecule_intelligence_impl", fake_impl)
    asyncio.run(P.fetch_molecule_intelligence("TestMoleculeABC"))
    asyncio.run(P.fetch_molecule_intelligence("TestMoleculeABC"))
    assert calls["n"] == 1
