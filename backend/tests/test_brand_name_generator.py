"""Tests for the AI-requirement naming path in brand_name_generator.

The deterministic path (generate_candidates) is already covered end-to-end via
tests/test_api.py against the real Orange Book index. These tests focus on the
new AI-brief mode and its fallback/screening behavior, using a stubbed model
call so they run without a network dependency.
"""
import asyncio

import pytest

from app.services import brand_name_generator as gen


def _run(coro):
    return asyncio.run(coro)


def test_ai_candidates_fall_back_to_algorithmic_when_not_configured(monkeypatch):
    monkeypatch.setattr(gen, "ai_naming_configured", lambda: False)
    result = _run(gen.generate_ai_candidates("Empagliflozin", "Cardiometabolic", "Heart Failure", "premium sound", 5))
    assert len(result) <= 5
    assert all(c.get("ai_generated") is False for c in result)


def test_ai_candidates_are_screened_against_marketed_names(monkeypatch):
    monkeypatch.setattr(gen, "ai_naming_configured", lambda: True)
    monkeypatch.setattr(gen, "_marketed_names", lambda: {"JARDIANCE", "FARXIGA"})

    async def fake_ai_raw(molecule, therapy_area, indication, requirement, count):
        return [
            {"name": "Jardiance", "rationale": "exact collision, must be rejected"},
            {"name": "Jardianz", "rationale": "one edit from a marketed brand"},
            {"name": "Novaflex", "rationale": "clear name"},
        ]

    monkeypatch.setattr(gen, "_ai_raw_candidates", fake_ai_raw)

    result = _run(gen.generate_ai_candidates("Empagliflozin", "Cardiometabolic", "Heart Failure", "premium sound", 5))
    names = {c["name"] for c in result}
    assert "Jardiance" not in names  # exact collision must never surface
    assert all(c["ai_generated"] for c in result)
    assert all(c["exact_collision_with_marketed_brand"] is False for c in result)


def test_ai_candidates_carry_search_links(monkeypatch):
    monkeypatch.setattr(gen, "ai_naming_configured", lambda: True)
    monkeypatch.setattr(gen, "_marketed_names", lambda: set())

    async def fake_ai_raw(molecule, therapy_area, indication, requirement, count):
        return [{"name": "Weeklor", "rationale": "evokes once-weekly dosing"}]

    monkeypatch.setattr(gen, "_ai_raw_candidates", fake_ai_raw)

    result = _run(gen.generate_ai_candidates("Semaglutide", "Metabolic", "Obesity", "once-weekly", 5))
    assert len(result) == 1
    for key in ("ip_india_search_url", "uspto_search_url", "wipo_search_url"):
        assert result[0][key].startswith("http")


def test_ai_call_failure_falls_back_to_algorithmic(monkeypatch):
    monkeypatch.setattr(gen, "ai_naming_configured", lambda: True)

    async def failing(*args, **kwargs):
        return []  # simulates ClaudeUnavailable being caught inside _ai_raw_candidates

    monkeypatch.setattr(gen, "_ai_raw_candidates", failing)

    result = _run(gen.generate_ai_candidates("Empagliflozin", "Cardiometabolic", "Heart Failure", "x", 5))
    assert len(result) <= 5
