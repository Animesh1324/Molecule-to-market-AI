"""Tests for the real AI Co-Pilot backend, replacing the old frontend-only
keyword-matched generator that fabricated p-values, sample sizes, and
superiority claims for whatever molecule was loaded.
"""
import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.services import ai_copilot

client = TestClient(app)


def _run(coro):
    return asyncio.run(coro)


def test_answers_honestly_when_not_configured(monkeypatch):
    monkeypatch.setattr(ai_copilot, "is_configured", lambda: False)
    result = _run(ai_copilot.answer_copilot_question(
        molecule="Empagliflozin", brand_name="Cardioflo", therapy_area="Cardiometabolic",
        indication="Heart Failure", question="Draft a doctor detailer pitch", history=[],
    ))
    assert result["ai_answered"] is False
    assert "ANTHROPIC_API_KEY" in result["reply"]


def test_returns_ai_reply_when_clean(monkeypatch):
    async def fake_generate_json(**kwargs):
        return {"reply": "Lead with the validated mechanism and ask the team to confirm the label claim before use."}

    monkeypatch.setattr(ai_copilot, "is_configured", lambda: True)
    monkeypatch.setattr(ai_copilot, "generate_json", fake_generate_json)

    result = _run(ai_copilot.answer_copilot_question(
        molecule="Empagliflozin", brand_name="Cardioflo", therapy_area="Cardiometabolic",
        indication="Heart Failure", question="How should we frame the pitch?", history=[],
    ))
    assert result["ai_answered"] is True
    assert "validated mechanism" in result["reply"]


def test_quarantines_a_clinical_claim_instead_of_showing_it(monkeypatch):
    async def fake_generate_json(**kwargs):
        return {"reply": "In pivotal trials (N>7,000), Cardioflo achieved a 38% relative risk reduction (p<0.001)."}

    monkeypatch.setattr(ai_copilot, "is_configured", lambda: True)
    monkeypatch.setattr(ai_copilot, "generate_json", fake_generate_json)

    result = _run(ai_copilot.answer_copilot_question(
        molecule="Empagliflozin", brand_name="Cardioflo", therapy_area="Cardiometabolic",
        indication="Heart Failure", question="Draft a doctor pitch", history=[],
    ))
    assert result["ai_answered"] is False
    assert "38%" not in result["reply"]
    assert "withheld" in result["reply"]


def test_quarantines_a_superiority_claim(monkeypatch):
    async def fake_generate_json(**kwargs):
        return {"reply": "Only Cardioflo offers unmatched, best-in-class organ protection."}

    monkeypatch.setattr(ai_copilot, "is_configured", lambda: True)
    monkeypatch.setattr(ai_copilot, "generate_json", fake_generate_json)

    result = _run(ai_copilot.answer_copilot_question(
        molecule="Empagliflozin", brand_name="Cardioflo", therapy_area="Cardiometabolic",
        indication="Heart Failure", question="Draft a doctor pitch", history=[],
    ))
    assert result["ai_answered"] is False
    assert "unmatched" not in result["reply"]


def test_ai_unavailable_falls_back_honestly(monkeypatch):
    async def failing(**kwargs):
        raise ai_copilot.ClaudeUnavailable("rate limited")

    monkeypatch.setattr(ai_copilot, "is_configured", lambda: True)
    monkeypatch.setattr(ai_copilot, "generate_json", failing)

    result = _run(ai_copilot.answer_copilot_question(
        molecule="Empagliflozin", brand_name="Cardioflo", therapy_area="Cardiometabolic",
        indication="Heart Failure", question="Anything", history=[],
    ))
    assert result["ai_answered"] is False
    assert "unavailable" in result["reply"]


def test_grounding_includes_history_and_competitor_facts():
    prompt = ai_copilot._format_grounding(
        "Empagliflozin", "Cardioflo", "Cardiometabolic", "Heart Failure",
        {"pharmacological_class": "SGLT2 inhibitor"},
        [{"title": "EMPA-REG OUTCOME", "pmid": "26378978"}],
        None,
        {"competitors": [{"brand_name": "Farxiga", "company": "AstraZeneca", "market_share_percentage": 22.5}]},
        [{"sender": "user", "text": "What about competitors?"}],
        "Who competes with us?",
    )
    assert "SGLT2 inhibitor" in prompt
    assert "EMPA-REG OUTCOME" in prompt
    assert "Farxiga" in prompt
    assert "What about competitors?" in prompt
    assert "Who competes with us?" in prompt


def test_endpoint_smoke():
    response = client.post("/api/copilot/ask", json={
        "molecule": "Empagliflozin",
        "brand_name": "Cardioflo",
        "therapy_area": "Cardiometabolic",
        "indication": "Heart Failure",
        "question": "How should we position this brand?",
        "history": [],
    })
    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert isinstance(body["ai_answered"], bool)
