"""Tests for Claude-backed drafting and the compliance screen.

None of these make a network call: drafting is exercised by substituting the
generator, so the guardrails are tested deterministically and CI needs no key.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.brand_plan import CompleteBrandPlan
from app.services import ai_drafting, compliance
from app.services.ai_orchestrator import generate_strategic_brand_plan
from app.services.claude_client import ClaudeUnavailable

client = TestClient(app)


def _plan() -> CompleteBrandPlan:
    return generate_strategic_brand_plan(
        project_id="test-ai",
        molecule_name="Empagliflozin",
        brand_name="Cardioflo",
        therapy_area="Cardiometabolic",
        indication="Heart Failure",
    )


# --- compliance screen ------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Delivers a 38% relative risk reduction in cardiovascular death.",
    "The primary endpoint was met (p < 0.001).",
    "Hazard ratio: 0.62 versus placebo.",
    "Benefit sustained across the range (95% CI, 0.49 to 0.77).",
    "Positioned as the best-in-class option for these patients.",
    "It is superior to dapagliflozin in this population.",
    "The therapy is well tolerated with minimal adverse events.",
    "Dose is 10 mg once daily in the morning.",
])
def test_compliance_catches_unsourced_clinical_claims(text):
    """Text a drafting model must never produce unscreened."""
    assert compliance.scan_text("field", text), f"missed: {text}"


@pytest.mark.parametrize("text", [
    "Validate the prescriber segment sizing before committing field resources.",
    "Define the target patient profile with the medical affairs team.",
    "Sequence formulary submissions ahead of the national launch meeting.",
    "The evidence base for this indication is an open gap [SOURCE NEEDED: pivotal trial].",
    "Plan a 12-month KOL engagement cadence across three regions.",
])
def test_compliance_allows_strategy_language(text):
    """Legitimate strategy text must not be quarantined."""
    assert compliance.scan_text("field", text) == []


# --- drafting merge behavior -------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


def test_drafting_quarantines_fields_containing_claims(monkeypatch):
    """A drafted field with a clinical claim keeps template text and raises a flag."""
    async def fake_generate_json(**kwargs):
        return {
            **{f: "Validate this with the brand team before committing." for f in ai_drafting._NARRATIVE_FIELDS},
            "positioning_statement": "Cardioflo delivers a 38% reduction in CV death.",
            "sections": [],
            "open_questions": [],
        }

    monkeypatch.setattr(ai_drafting, "is_configured", lambda: True)
    monkeypatch.setattr(ai_drafting, "generate_json", fake_generate_json)
    monkeypatch.setattr(ai_drafting, "get_settings", lambda: {"claude_model": "test-model"})

    result = _run(ai_drafting.draft_brand_plan(_plan()))

    assert result.ai_status == "drafted"
    assert "38%" not in result.positioning_statement
    assert any("positioning_statement" in flag for flag in result.ai_review_flags)
    assert result.mission == "Validate this with the brand team before committing."
    assert result.mlr_compliance_signoff_ready is False


def test_drafting_failure_falls_back_to_template(monkeypatch):
    """An unavailable model returns the template plan, not an error."""
    async def failing(**kwargs):
        raise ClaudeUnavailable("rate limited")

    monkeypatch.setattr(ai_drafting, "is_configured", lambda: True)
    monkeypatch.setattr(ai_drafting, "generate_json", failing)

    template = _plan()
    result = _run(ai_drafting.draft_brand_plan(template))

    assert result.ai_status == "drafting_failed"
    assert result.ai_drafted is False
    assert result.mission == template.mission
    assert len(result.sections) == 12


def test_drafting_skipped_when_not_configured(monkeypatch):
    monkeypatch.setattr(ai_drafting, "is_configured", lambda: False)
    result = _run(ai_drafting.draft_brand_plan(_plan()))
    assert result.ai_status == "template"
    assert result.ai_drafted is False


def test_drafting_never_sets_mlr_signoff(monkeypatch):
    """Drafting must not confer MLR approval under any path."""
    async def clean(**kwargs):
        return {
            **{f: "Sequence the launch activities by quarter." for f in ai_drafting._NARRATIVE_FIELDS},
            "sections": [],
            "open_questions": ["Confirm the reimbursement pathway."],
        }

    monkeypatch.setattr(ai_drafting, "is_configured", lambda: True)
    monkeypatch.setattr(ai_drafting, "generate_json", clean)
    monkeypatch.setattr(ai_drafting, "get_settings", lambda: {"claude_model": "test-model"})

    result = _run(ai_drafting.draft_brand_plan(_plan()))
    assert result.mlr_compliance_signoff_ready is False
    assert any("Open question" in f for f in result.ai_review_flags)


def test_schema_is_valid_for_structured_outputs():
    """Structured outputs require closed objects with every property required."""
    schema = ai_drafting._plan_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"].keys())
    item = schema["properties"]["sections"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"].keys())


# --- endpoint behavior -------------------------------------------------------

def test_brand_plan_endpoint_works_without_ai_key():
    """The app must stay fully functional with no Anthropic key configured."""
    response = client.get("/api/brand-plan/generate?project_id=test-noai&molecule=Empagliflozin&refresh=true")
    assert response.status_code == 200
    body = response.json()
    assert len(body["sections"]) == 12
    assert body["ai_status"] in ("template", "drafted", "drafting_failed")


def test_root_reports_ai_status():
    body = client.get("/").json()
    assert "ai_drafting" in body
    assert isinstance(body["ai_drafting"]["enabled"], bool)
