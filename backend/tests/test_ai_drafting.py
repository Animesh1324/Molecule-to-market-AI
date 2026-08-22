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


# --- regulatory grounding ----------------------------------------------------

def test_grounding_renders_regulatory_status_when_supplied():
    """The regulatory dossier must reach the drafting prompt, not just PubChem/PubMed."""
    regulatory = {
        "us_fda": {
            "status": "Approved",
            "approval_year": 2014,
            "innovator_brand_name": "Jardiance",
            "application_numbers": ["NDA204629"],
            "boxed_warnings": [],
            "approved_indications": ["Type 2 diabetes mellitus"],
        },
        "india_cdsco": {"status": "Approved", "approval_year": 2015},
        "eu_ema": {"status": "Investigational"},
        "generic_vs_innovator_status": "Innovator Exclusivity",
        "patent_expiry_timeline": "Composition-of-matter patent expires 2028",
    }
    prompt = ai_drafting._format_grounding(_plan(), None, None, None, regulatory)

    assert "Verified regulatory status" in prompt
    assert "US FDA: Approved, approved 2014, innovator brand Jardiance" in prompt
    assert "1 application(s) on file" in prompt
    assert "India CDSCO: Approved, approved 2015" in prompt
    assert "EU EMA" not in prompt  # Investigational status is skipped as uninformative
    assert "Innovator Exclusivity" in prompt
    assert "Composition-of-matter patent expires 2028" in prompt


def test_grounding_flags_missing_regulatory_data_as_a_gap():
    prompt = ai_drafting._format_grounding(_plan(), None, None, None, None)
    assert "Treat approval status and exclusivity timing as an open gap." in prompt


def test_draft_brand_plan_forwards_regulatory_into_the_prompt(monkeypatch):
    """draft_brand_plan must thread its `regulatory` argument into the prompt sent to Claude."""
    captured = {}

    async def fake_generate_json(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return {
            **{f: "Sequence the launch activities by quarter." for f in ai_drafting._NARRATIVE_FIELDS},
            "sections": [],
            "open_questions": [],
        }

    monkeypatch.setattr(ai_drafting, "is_configured", lambda: True)
    monkeypatch.setattr(ai_drafting, "generate_json", fake_generate_json)
    monkeypatch.setattr(ai_drafting, "get_settings", lambda: {"claude_model": "test-model"})

    regulatory = {"us_fda": {"status": "Approved", "approval_year": 2014}}
    _run(ai_drafting.draft_brand_plan(_plan(), regulatory=regulatory))

    assert "US FDA: Approved, approved 2014" in captured["prompt"]


def test_grounding_renders_curated_swot_when_supplied():
    competitors = {
        "swot_analysis": {
            "strengths": ["Landmark outcomes trial demonstrating mortality benefit."],
            "weaknesses": ["Requires patient counseling on a known class side effect."],
            "opportunities": ["Guideline endorsement expanding first-line use."],
            "threats": ["A faster-growing competitor class capturing specialist share."],
        }
    }
    prompt = ai_drafting._format_grounding(_plan(), None, None, competitors, None)
    assert "SWOT on file" in prompt
    assert "[Strengths] Landmark outcomes trial demonstrating mortality benefit." in prompt
    assert "[Threats] A faster-growing competitor class capturing specialist share." in prompt


def test_grounding_omits_swot_section_when_all_empty():
    prompt = ai_drafting._format_grounding(_plan(), None, None, {"swot_analysis": {}}, None)
    assert "SWOT on file" not in prompt


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
