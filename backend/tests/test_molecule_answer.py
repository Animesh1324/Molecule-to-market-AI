"""Tests for the Claude-answered molecule route.

Network-free: Claude is stubbed. What matters here is not the model's prose but
the guarantees around it — provenance marking, compliance screening, and the
refusal to claim MLR readiness for model-sourced content.
"""
import asyncio

import pytest

from app.db.database import SessionLocal, init_db
from app.db.drug_models import DrugORM
from app.services import molecule_answer as ma
from app.services.claude_client import ClaudeUnavailable

init_db()


def _run(coro):
    """Match the suite's existing style; pytest-asyncio is not installed."""
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _seed():
    s = SessionLocal()
    s.query(DrugORM).delete()
    s.add(DrugORM(id="d1", generic_name="Testolol", brand_name="Testabrand",
                  drug_class="Beta Blocker [EPC]", search_blob="testolol testabrand",
                  indications="Indicated for hypertension."))
    s.commit(); s.close()
    yield


def _stub(monkeypatch, payload):
    async def fake(**kwargs):
        fake.prompt = kwargs.get("prompt", "")
        return payload
    monkeypatch.setattr(ma, "generate_json", fake)
    monkeypatch.setattr(ma, "is_configured", lambda: True)
    return fake


def test_fields_carry_provenance_and_citability(monkeypatch):
    _stub(monkeypatch, {
        "molecule": "Testolol", "summary": "A beta blocker.",
        "fields": [
            {"name": "drug_class", "value": "Beta Blocker [EPC]", "source": "fda"},
            {"name": "half_life", "value": "About 6 hours", "source": "model"},
        ],
        "caveats": [],
    })
    result = _run(ma.answer_molecule("testolol"))
    by_name = {f["name"]: f for f in result["fields"]}
    assert by_name["drug_class"]["mlr_citable"] is True
    # A model-sourced statement is not traceable to a regulatory document.
    assert by_name["half_life"]["mlr_citable"] is False
    assert result["model_sourced_fields"] == 1


def test_stored_record_is_passed_as_grounding_context(monkeypatch):
    fake = _stub(monkeypatch, {"molecule": "Testolol", "summary": "x", "fields": [], "caveats": []})
    result = _run(ma.answer_molecule("testolol"))
    assert result["grounded_in_catalogue"] is True
    assert "Beta Blocker [EPC]" in fake.prompt
    assert "hypertension" in fake.prompt.lower()


def test_unknown_molecule_says_so_rather_than_silently_ungrounded(monkeypatch):
    fake = _stub(monkeypatch, {"molecule": "Nope", "summary": "x", "fields": [], "caveats": []})
    result = _run(ma.answer_molecule("notarealmolecule"))
    assert result["grounded_in_catalogue"] is False
    assert "NO FDA RECORD FOUND" in fake.prompt


def test_output_is_compliance_screened(monkeypatch):
    _stub(monkeypatch, {
        "molecule": "Testolol",
        "summary": "Testolol is significantly more effective than comparators (p<0.001).",
        "fields": [{"name": "efficacy", "value": "Superior to all alternatives, HR 0.62",
                    "source": "model"}],
        "caveats": [],
    })
    result = _run(ma.answer_molecule("testolol"))
    assert result["compliance_findings"], "comparative efficacy claims must be flagged"
    assert result["compliance_notice"]


def test_never_claims_mlr_signoff(monkeypatch):
    _stub(monkeypatch, {"molecule": "Testolol", "summary": "Benign.",
                        "fields": [{"name": "x", "value": "y", "source": "fda"}], "caveats": []})
    result = _run(ma.answer_molecule("testolol"))
    assert result["mlr_compliance_signoff_ready"] is False
    assert "verified against the approved label" in result["disclaimer"]


def test_unconfigured_raises_rather_than_falling_back(monkeypatch):
    monkeypatch.setattr(ma, "is_configured", lambda: False)
    with pytest.raises(ClaudeUnavailable):
        _run(ma.answer_molecule("testolol"))


def test_blank_molecule_rejected():
    with pytest.raises(ValueError):
        _run(ma.answer_molecule("  "))
