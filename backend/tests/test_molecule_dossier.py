"""Tests for the single-call molecule dossier."""
import pytest

from app.db.database import SessionLocal, init_db
from app.db.drug_models import DrugORM
from app.db.orange_book_models import OrangeBookPatentORM, OrangeBookProductORM
from app.services import molecule_dossier as md

init_db()


@pytest.fixture(autouse=True)
def _clean():
    s = SessionLocal()
    for m in (DrugORM, OrangeBookProductORM, OrangeBookPatentORM):
        s.query(m).delete()
    s.commit(); s.close()
    yield


def _drug(generic, brand=None, drug_class=None, indications=None):
    return DrugORM(id=f"id-{generic}-{brand}", generic_name=generic, brand_name=brand,
                   drug_class=drug_class, indications=indications,
                   search_blob=f"{generic} {brand or ''} {drug_class or ''}".lower())


def test_combination_product_does_not_supply_the_molecules_class():
    """Regression: searching a molecule must not adopt a co-formulation's class.

    "empagliflozin" matched an empagliflozin+metformin product and reported the
    class as Biguanide — metformin's class, not empagliflozin's. A brand plan
    carrying that would fail MLR.
    """
    s = SessionLocal()
    s.add(_drug("Empagliflozin And Metformin Hydrochloride", "Synjardy",
                "Biguanide [EPC]", "Rich label text that would win on completeness."))
    s.add(_drug("Empagliflozin", "Jardiance", "Sodium-Glucose Cotransporter 2 Inhibitor [EPC]"))
    s.commit(); s.close()

    d = md.build_dossier("empagliflozin")
    assert d["identity"]["drug_class"] == "Sodium-Glucose Cotransporter 2 Inhibitor [EPC]"
    assert d["identity"]["single_ingredient_products"] == 1
    assert any("Metformin" in c for c in d["identity"]["combination_products"])


def test_combination_patents_are_excluded_from_the_molecules_count():
    s = SessionLocal()
    s.add(OrangeBookProductORM(id="p1", appl_no="1", ingredient="EMPAGLIFLOZIN", trade_name="JARDIANCE"))
    s.add(OrangeBookProductORM(id="p2", appl_no="2",
                               ingredient="EMPAGLIFLOZIN; METFORMIN HYDROCHLORIDE", trade_name="SYNJARDY"))
    s.add(OrangeBookPatentORM(id="x1", appl_no="1", patent_no="111", patent_expire_date_iso="2030-01-01"))
    s.add(OrangeBookPatentORM(id="x2", appl_no="2", patent_no="999", patent_expire_date_iso="2040-01-01"))
    s.commit(); s.close()

    e = md.build_dossier("empagliflozin")["exclusivity"]
    assert e["patents"] == 1                      # not the combination's patent
    assert e["latest_patent_expiry"] == "2030-01-01"
    assert e["combination_products"] == 1


def test_patents_count_distinct_not_listings():
    """FDA lists one patent per covered indication; those are not extra patents."""
    s = SessionLocal()
    s.add(OrangeBookProductORM(id="p1", appl_no="1", ingredient="TESTOLOL"))
    for n, use in enumerate(["U-1", "U-2", "U-3"]):
        s.add(OrangeBookPatentORM(id=f"x{n}", appl_no="1", patent_no="555",
                                  patent_use_code=use, patent_expire_date_iso="2033-01-01"))
    s.commit(); s.close()

    e = md.build_dossier("testolol")["exclusivity"]
    assert e["patents"] == 1
    assert e["patent_listings"] == 3
    assert e["use_codes"] == 3


def test_absent_orange_book_listing_says_why():
    """Biologics are Purple Book. Absence must not read as 'off patent'."""
    s = SessionLocal(); s.add(_drug("Pembrolizumab", "Keytruda")); s.commit(); s.close()
    e = md.build_dossier("pembrolizumab")["exclusivity"]
    assert e["found"] is False
    assert "Purple Book" in e["note"]
    assert "patents" not in e            # no zero that could be read as a finding


def test_every_paper_carries_a_resolvable_link():
    assert md.paper_url("12345", None, None) == "https://pubmed.ncbi.nlm.nih.gov/12345/"
    assert md.paper_url(None, "10.1/x", None) == "https://doi.org/10.1/x"
    assert md.paper_url(None, None, "PMC9") == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9/"
    assert md.paper_url(None, None, None) is None


def test_unknown_molecule_reports_not_found_rather_than_empty_success():
    d = md.build_dossier("notarealmolecule")
    assert d["identity"]["found"] is False
    assert d["sections_populated"] == []


def test_blank_molecule_is_rejected():
    with pytest.raises(ValueError):
        md.build_dossier("   ")


def test_every_section_names_a_source():
    s = SessionLocal(); s.add(_drug("Testolol", "Testabrand", "Beta Blocker [EPC]")); s.commit(); s.close()
    d = md.build_dossier("testolol")
    assert d["identity"]["source"]["url"]
    assert d["approvals"]["source"]["url"]
    assert d["exclusivity"]["source"]["url"]
    assert d["safety_signals"]["recalls"]["source"]["url"]
    assert d["safety_signals"]["shortages"]["source"]["url"]
