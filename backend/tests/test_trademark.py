"""Tests for brand-naming intelligence: real collision data, AI-drafted names,
and the deterministic fallback used when no Anthropic key is configured.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import trademark_service

client = TestClient(app)


def _run(coro):
    return asyncio.run(coro)


def test_falls_back_to_template_names_without_ai_key(monkeypatch):
    monkeypatch.setattr(trademark_service, "is_configured", lambda: False)
    result = _run(trademark_service.generate_trademark_intelligence("Empagliflozin"))
    assert result.ai_generated is False
    assert len(result.suggested_brand_names) >= 3
    assert all(s.uspto_search_link for s in result.suggested_brand_names)


def test_fallback_respects_count_and_exclude(monkeypatch):
    monkeypatch.setattr(trademark_service, "is_configured", lambda: False)
    first = _run(trademark_service.generate_trademark_intelligence("Empagliflozin", count=4))
    assert len(first.suggested_brand_names) == 4

    first_names = [s.name for s in first.suggested_brand_names]
    second = _run(trademark_service.generate_trademark_intelligence(
        "Empagliflozin", count=4, exclude=first_names,
    ))
    second_names = {s.name for s in second.suggested_brand_names}
    assert not second_names.intersection(first_names)


def test_ai_generated_names_are_used_when_configured(monkeypatch):
    async def fake_generate(**kwargs):
        return {
            "names": [
                {"name": "Cardiveno", "rationale": "Reflects cardiometabolic focus.",
                 "linguistic_tone": "Authoritative & Scientific", "stem_origin": "Cardi- + -veno"},
                {"name": "Metaboli", "rationale": "Evokes metabolic balance.",
                 "linguistic_tone": "Modern & Dynamic", "stem_origin": "Metabo- + -li"},
            ]
        }

    monkeypatch.setattr(trademark_service, "is_configured", lambda: True)
    monkeypatch.setattr(trademark_service, "generate_json", fake_generate)

    result = _run(trademark_service.generate_trademark_intelligence("Empagliflozin", count=2))
    assert result.ai_generated is True
    names = {s.name for s in result.suggested_brand_names}
    assert names == {"Cardiveno", "Metaboli"}


def test_ai_failure_falls_back_to_template(monkeypatch):
    async def failing(**kwargs):
        raise trademark_service.ClaudeUnavailable("rate limited")

    monkeypatch.setattr(trademark_service, "is_configured", lambda: True)
    monkeypatch.setattr(trademark_service, "generate_json", failing)

    result = _run(trademark_service.generate_trademark_intelligence("Empagliflozin"))
    assert result.ai_generated is False
    assert len(result.suggested_brand_names) >= 3


def test_requirement_is_threaded_into_the_ai_prompt(monkeypatch):
    captured = {}

    async def fake_generate(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return {"names": [{"name": "Weeklor", "rationale": "r", "linguistic_tone": "Modern & Dynamic", "stem_origin": "s"}]}

    monkeypatch.setattr(trademark_service, "is_configured", lambda: True)
    monkeypatch.setattr(trademark_service, "generate_json", fake_generate)

    _run(trademark_service.generate_trademark_intelligence(
        "Semaglutide", requirement="Should evoke once-weekly convenience", count=1,
    ))
    assert "Should evoke once-weekly convenience" in captured["prompt"]


def test_names_colliding_with_a_real_existing_brand_are_flagged_moderate(monkeypatch):
    monkeypatch.setattr(trademark_service, "is_configured", lambda: True)

    async def fake_generate(**kwargs):
        # Same soundex family as "Jardiance" (J-6-3-5), used as a real reference brand.
        return {"names": [{"name": "Jardianz", "rationale": "r", "linguistic_tone": "Modern & Dynamic", "stem_origin": "s"}]}

    monkeypatch.setattr(trademark_service, "generate_json", fake_generate)
    monkeypatch.setattr(trademark_service, "_existing_brands", lambda molecule, therapy_area: (
        ["Jardiance"], [], "reference_class",
    ))

    result = _run(trademark_service.generate_trademark_intelligence("Empagliflozin", count=1))
    assert result.suggested_brand_names[0].collision_risk.startswith("Moderate")


def test_endpoint_accepts_requirement_and_count_params():
    response = client.get(
        "/api/trademark/analyze?molecule=Empagliflozin&count=5&requirement=Should+sound+premium"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggested_brand_names"]) == 5
    assert data["requirement_applied"] == "Should sound premium"
