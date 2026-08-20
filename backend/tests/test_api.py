from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "healthy"
import pytest
from fastapi.testclient import TestClient
from app.db.database import init_db
from app.main import app

# Ensure DB tables exist before any test (TestClient lifespan may not fire in all Starlette versions)
init_db()

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Operational"
    assert data["modules_active"] == 10

def test_projects_list():
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 2
    assert any(p["target_molecule_name"] == "Empagliflozin" for p in projects)

def test_molecule_intelligence():
    response = client.get("/api/molecules/search?name=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert data["generic_name"] == "Empagliflozin"
    assert "SGLT2" in data["pharmacological_class"]
    assert len(data["approved_indications"]) > 0

def test_evidence_papers():
    response = client.get("/api/evidence/papers?molecule=Empagliflozin")
    assert response.status_code == 200
    papers = response.json()
    assert len(papers) >= 1
    assert any("EMPA-REG" in p["title"] or "Empagliflozin" in p["title"] for p in papers)

def test_clinical_trials():
    response = client.get("/api/trials/landscape?molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert data["total_trials_found"] >= 1
    assert len(data["landmark_trials"]) >= 1

def test_regulatory_labels():
    response = client.get("/api/regulatory/labels?molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert data["us_fda"]["innovator_brand_name"] == "JARDIANCE"
    assert len(data["key_label_claims_verified"]) > 0

def test_trademark_analysis():
    response = client.get("/api/trademark/analyze?molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggested_brand_names"]) >= 3
    assert all("uspto_search_link" in s for s in data["suggested_brand_names"])

def test_competitor_landscape():
    response = client.get("/api/competitors/landscape?molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert len(data["competitors"]) >= 2
    assert len(data["swot_analysis"]["strengths"]) >= 1

def test_forecasting_model():
    response = client.get("/api/forecasting/model?prevalence_rate=0.10&treated_rate=0.60")
    assert response.status_code == 200
    data = response.json()
    assert data["prevalent_patient_pool"] > 0
    assert data["realistic_scenario"]["year_5"] > data["realistic_scenario"]["year_1"]

def test_brand_plan_generation():
    response = client.get("/api/brand-plan/generate?project_id=test-1&molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sections"]) == 12
    assert len(data["monthly_action_plan"]) >= 5

def test_creative_assets_generation():
    response = client.get("/api/assets/generate?molecule=Empagliflozin")
    assert response.status_code == 200
    data = response.json()
    assert len(data["visual_aid_slides"]) == 6
    assert len(data["mr_objection_handling_guide"]) >= 3

def test_export_docx():
    response = client.get("/api/reports/export/docx?molecule=Empagliflozin&brand_name=Cardioflo")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(response.content) > 1000

def test_export_pptx():
    response = client.get("/api/reports/export/pptx?molecule=Empagliflozin&brand_name=Cardioflo")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert len(response.content) > 1000

def test_export_xlsx():
    response = client.get("/api/reports/export/xlsx?brand_name=Cardioflo")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(response.content) > 1000
