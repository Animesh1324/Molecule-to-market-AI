"""Tests for the single-page visual-aid brief and its image-generation prompt.

Mirrors the pattern in test_ai_drafting.py: no network calls, drafting is
exercised by substituting the generator so guardrails are tested
deterministically.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import visual_aid_drafting as vad

client = TestClient(app)


def _run(coro):
    return asyncio.run(coro)


def test_falls_back_to_source_needed_when_ai_not_configured(monkeypatch):
    monkeypatch.setattr(vad, "is_configured", lambda: False)
    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure"))
    assert brief.ai_drafted is False
    assert "SOURCE NEEDED" in brief.punchline
    assert "SOURCE NEEDED" in brief.composition


def test_ai_drafted_fields_are_used_when_clean(monkeypatch):
    async def fake_generate_json(**kwargs):
        return {
            "punchline": "Consistency your patients can feel",
            "clinical_message_points": [
                "Positioning should lead with mechanism, pending label confirmation.",
                "Validate the eligible patient profile with medical affairs.",
            ],
            "hero_visual_concept": "A patient managing daily life with confidence",
            "call_to_prescribe": "Consider Cardioflo at the next step-up decision.",
        }

    monkeypatch.setattr(vad, "is_configured", lambda: True)
    monkeypatch.setattr(vad, "generate_json", fake_generate_json)

    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure"))
    assert brief.ai_drafted is True
    assert brief.punchline == "Consistency your patients can feel"
    assert len(brief.clinical_message_points) == 2
    assert brief.ai_review_flags == []


def test_clinical_claims_are_quarantined_not_surfaced(monkeypatch):
    async def fake_generate_json(**kwargs):
        return {
            "punchline": "38% reduction in cardiovascular death",  # a claim, not a punchline
            "clinical_message_points": ["Well tolerated with minimal side effects."],
            "hero_visual_concept": "Superior to all competitors in every trial",
            "call_to_prescribe": "Prescribe today.",
        }

    monkeypatch.setattr(vad, "is_configured", lambda: True)
    monkeypatch.setattr(vad, "generate_json", fake_generate_json)

    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure"))
    assert "38%" not in brief.punchline
    assert "Superior" not in brief.hero_visual_concept
    assert brief.clinical_message_points == ["[SOURCE NEEDED — add a message once evidence/regulatory grounding is available]"]
    assert any("punchline" in f for f in brief.ai_review_flags)
    assert any("hero_visual_concept" in f for f in brief.ai_review_flags)


def test_ai_failure_falls_back_to_template(monkeypatch):
    async def failing(**kwargs):
        raise vad.ClaudeUnavailable("rate limited")

    monkeypatch.setattr(vad, "is_configured", lambda: True)
    monkeypatch.setattr(vad, "generate_json", failing)

    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure"))
    assert brief.ai_drafted is False
    assert any("unavailable" in f for f in brief.ai_review_flags)


def test_composition_uses_regulatory_dosing_summary_when_available(monkeypatch):
    monkeypatch.setattr(vad, "is_configured", lambda: False)
    regulatory = {"us_fda": {"status": "Approved", "dosage_and_administration_summary": "10 mg once daily, oral tablet"}}
    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure", regulatory=regulatory))
    assert "10 mg once daily, oral tablet" in brief.composition


def test_scientific_support_cites_real_evidence_and_regulatory_facts(monkeypatch):
    monkeypatch.setattr(vad, "is_configured", lambda: False)
    evidence = [{"title": "EMPA-REG OUTCOME", "pmid": "26378978"}]
    regulatory = {"us_fda": {"status": "Approved", "application_numbers": ["NDA204629"]}}
    brief = _run(vad.draft_visual_aid_brief(
        "Empagliflozin", "Cardioflo", "Heart Failure", regulatory=regulatory, evidence=evidence,
    ))
    joined = " ".join(brief.scientific_support)
    assert "EMPA-REG OUTCOME" in joined and "26378978" in joined
    assert "NDA204629" in joined


def test_image_prompt_never_contains_clinical_numbers_beyond_screened_fields(monkeypatch):
    monkeypatch.setattr(vad, "is_configured", lambda: False)
    brief = _run(vad.draft_visual_aid_brief("Empagliflozin", "Cardioflo", "Heart Failure"))
    assert "70% visual imagery, 30% text" in brief.image_generation_prompt
    assert brief.brand_name in brief.image_generation_prompt
    assert brief.main_indication in brief.image_generation_prompt


def test_endpoint_returns_a_brief_without_an_ai_key():
    response = client.get("/api/assets/visual-aid-brief?molecule=Empagliflozin&brand_name=Cardioflo")
    assert response.status_code == 200
    body = response.json()
    assert body["molecule_name"] == "Empagliflozin"
    assert "image_generation_prompt" in body
