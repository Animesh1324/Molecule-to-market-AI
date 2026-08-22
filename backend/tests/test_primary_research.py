"""Tests for RCPA and HCP-questionnaire primary research: CRUD, honest
aggregation, and that it actually reaches the brand plan's insights field and
AI-drafting grounding — not just stored and forgotten.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.database import init_db
from app.main import app
from app.services import primary_research_service as research
from app.services import ai_orchestrator
from app.services import ai_drafting

init_db()
client = TestClient(app)


def _project_id() -> str:
    return f"proj-test-{uuid.uuid4().hex[:8]}"


def test_summary_reports_no_data_for_an_empty_project():
    summary = research.summarize_primary_research(_project_id())
    assert summary["has_data"] is False
    assert summary["rcpa_total"] == 0
    assert summary["hcp_total"] == 0


def test_rcpa_entry_requires_a_signal_note():
    with pytest.raises(ValueError):
        research.add_rcpa_entry(
            project_id=_project_id(), pharmacy_name="Metro Pharmacy",
            signal_note="", recorded_by="MR-1",
        )


def test_rcpa_aggregate_is_computed_from_real_rows():
    pid = _project_id()
    research.add_rcpa_entry(pid, "Metro Pharmacy", "Daily GLP-1 Rx observed.", "MR-1",
                             molecule_awareness=True, active_prescribing=True, potential_rating="High")
    research.add_rcpa_entry(pid, "Corner Chemist", "Aware but no active Rx.", "MR-1",
                             molecule_awareness=True, active_prescribing=False)
    research.add_rcpa_entry(pid, "Suburb Pharmacy", "No awareness observed.", "MR-1",
                             molecule_awareness=False, active_prescribing=False)

    summary = research.summarize_primary_research(pid)
    assert summary["has_data"] is True
    assert summary["rcpa_total"] == 3
    assert summary["rcpa_aware_count"] == 2
    assert summary["rcpa_aware_percent"] == pytest.approx(66.7, abs=0.1)
    assert summary["rcpa_active_count"] == 1
    assert summary["rcpa_high_potential_count"] == 1


def test_hcp_questionnaire_validates_rating_bounds():
    with pytest.raises(ValueError):
        research.add_hcp_questionnaire(
            project_id=_project_id(), specialty="Endocrinology", recorded_by="MR-1",
            cost_barrier_rating=15,
        )


def test_hcp_aggregate_is_computed_from_real_rows():
    pid = _project_id()
    research.add_hcp_questionnaire(pid, "Endocrinology", "MR-1", cost_barrier_rating=8, switch_intent=True)
    research.add_hcp_questionnaire(pid, "Cardiology", "MR-1", cost_barrier_rating=6, switch_intent=False)

    summary = research.summarize_primary_research(pid)
    assert summary["hcp_total"] == 2
    assert summary["hcp_avg_cost_barrier_rating"] == 7.0
    assert summary["hcp_switch_intent_count"] == 1
    assert summary["hcp_switch_intent_percent"] == 50.0


def test_delete_removes_the_entry():
    pid = _project_id()
    entry = research.add_rcpa_entry(pid, "Metro Pharmacy", "Observed.", "MR-1")
    assert research.delete_rcpa_entry(entry["id"]) is True
    assert research.list_rcpa_entries(pid) == []
    assert research.delete_rcpa_entry(entry["id"]) is False


def test_brand_plan_template_states_real_primary_research_figures():
    primary_research = {
        "has_data": True, "rcpa_total": 40, "hcp_total": 10,
        "rcpa_aware_count": 28, "rcpa_aware_percent": 70.0,
        "rcpa_active_count": 2, "rcpa_active_percent": 5.0,
        "rcpa_high_potential_count": 3,
        "hcp_avg_cost_barrier_rating": 7.0, "hcp_cost_barrier_respondents": 10,
    }
    plan = ai_orchestrator.generate_strategic_brand_plan(
        project_id="t", molecule_name="Semaglutide", brand_name="TestBrand",
        primary_research=primary_research,
    )
    assert "28/40" in plan.doctor_and_market_insights
    assert "70.0%" in plan.doctor_and_market_insights
    assert "Average cost-barrier rating: 7.0/10" in plan.doctor_and_market_insights


def test_brand_plan_template_states_the_gap_with_no_primary_research():
    plan = ai_orchestrator.generate_strategic_brand_plan(
        project_id="t", molecule_name="Semaglutide", brand_name="TestBrand",
    )
    assert "placeholder" in plan.doctor_and_market_insights.lower()


def test_ai_drafting_grounding_includes_primary_research():
    primary_research = {
        "has_data": True, "rcpa_total": 40, "hcp_total": 10,
        "rcpa_aware_count": 28, "rcpa_aware_percent": 70.0,
        "rcpa_active_count": 2, "rcpa_active_percent": 5.0,
    }
    plan = ai_orchestrator.generate_strategic_brand_plan(
        project_id="t", molecule_name="Semaglutide", brand_name="TestBrand",
    )
    prompt = ai_drafting._format_grounding(plan, None, None, None, None, primary_research)
    assert "Team-collected primary research on file" in prompt
    assert "28/40" in prompt


def test_endpoints_smoke():
    pid = _project_id()
    rcpa_resp = client.post("/api/primary-research/rcpa", json={
        "project_id": pid, "pharmacy_name": "Metro Pharmacy",
        "signal_note": "Daily GLP-1 Rx observed.", "recorded_by": "MR-1",
        "molecule_awareness": True, "active_prescribing": True,
    })
    assert rcpa_resp.status_code == 200
    entry_id = rcpa_resp.json()["id"]

    hcp_resp = client.post("/api/primary-research/questionnaire", json={
        "project_id": pid, "specialty": "Endocrinology", "recorded_by": "MR-1",
        "cost_barrier_rating": 8,
    })
    assert hcp_resp.status_code == 200

    summary_resp = client.get(f"/api/primary-research/summary?project_id={pid}")
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert body["has_data"] is True
    assert body["rcpa_total"] == 1
    assert body["hcp_total"] == 1

    delete_resp = client.delete(f"/api/primary-research/rcpa/{entry_id}")
    assert delete_resp.status_code == 200

    missing_resp = client.delete(f"/api/primary-research/rcpa/{entry_id}")
    assert missing_resp.status_code == 404
