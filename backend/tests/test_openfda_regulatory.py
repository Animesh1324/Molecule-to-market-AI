"""Regression tests for the combination-product contamination bug in
openfda_regulatory.py.

openFDA's search matches a molecule as a *substring/phrase* across generic
names, NDC listings, and drug applications — and none of those endpoints
exclude fixed-dose combinations that include the molecule. Verified live
against api.fda.gov before writing the fix: querying "Empagliflozin" surfaced
combination labels ('EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE') ranked ahead
of the plain molecule's own label by recency, an NDC pharm_class aggregation
polluted with "Biguanide [EPC]" (metformin's class) and "Dipeptidyl Peptidase
4 Inhibitor [EPC]" (linagliptin's), and 45 combination-product rows mixed into
drugsfda.json's 27 true applications for the molecule.

Each test below reconstructs the exact shape that caused a real
misattribution and pins the corrected behaviour, with httpx mocked so these
run offline and never depend on live API state.

No pytest-asyncio in this environment (matching the rest of the suite —
see test_evidence_corpus.py): async calls are driven with asyncio.run()
inside plain sync test functions rather than `async def test_...`.
"""
import asyncio
from typing import Any, Dict, List
from unittest.mock import patch

import httpx

from app.services import openfda_regulatory as R


class _FakeResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def _label(generic_names: List[str], **fields) -> Dict[str, Any]:
    return {"openfda": {"generic_name": generic_names}, **fields}


def _ndc_record(active_ingredient_names: List[str], pharm_class=None, dosage_form=None) -> Dict[str, Any]:
    return {
        "active_ingredients": [{"name": n} for n in active_ingredient_names],
        "pharm_class": pharm_class or [],
        "dosage_form": dosage_form,
    }


def _application(number: str, ingredient_groups: List[List[str]], brand: str,
                 approved: str = "2010-01-01") -> Dict[str, Any]:
    """One drugsfda application; each entry in ingredient_groups is one product."""
    return {
        "application_number": number,
        "sponsor_name": "Sponsor",
        "products": [
            {"brand_name": brand, "active_ingredients": [{"name": n} for n in group]}
            for group in ingredient_groups
        ],
        "submissions": [{"submission_status": "AP", "submission_status_date": approved}],
    }


def _mock_get(routes: Dict[str, List[List[Dict[str, Any]]]]):
    """Route by which endpoint is called, ignoring exact query params.

    `routes` maps a substring of the URL to the ordered response payloads that
    endpoint should return across successive calls (a queue, popped in order).
    """
    queues = {k: list(v) for k, v in routes.items()}

    async def fake_get(self, url, params=None):
        for key, queue in queues.items():
            if key in url:
                results = queue.pop(0) if queue else []
                return _FakeResponse({"results": results})
        return _FakeResponse({"results": []})

    return fake_get


def _run(coro_fn, *args, **kwargs):
    async def wrapped():
        async with httpx.AsyncClient() as client:
            return await coro_fn(client, *args, **kwargs)
    return asyncio.run(wrapped())


# --------------------------------------------------------------------------
# _fetch_label: combination labels must not outrank a single-ingredient one
# --------------------------------------------------------------------------

def test_is_combination_generic_name():
    assert R._is_combination_generic_name("EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE")
    assert R._is_combination_generic_name("EMPAGLIFLOZIN, LINAGLIPTIN, METFORMIN HYDROCHLORIDE")
    assert not R._is_combination_generic_name("EMPAGLIFLOZIN")
    assert not R._is_combination_generic_name("ROSUVASTATIN CALCIUM")
    # Defensive: FDA's Orange Book uses ";" for the same combinations this
    # endpoint writes with "AND" — not reproduced on this endpoint, but the
    # underlying data source is demonstrably inconsistent about it elsewhere.
    assert R._is_combination_generic_name("EMPAGLIFLOZIN; METFORMIN HYDROCHLORIDE")


def test_fetch_label_skips_combination_labels_ranked_first_by_recency():
    """Reproduces the exact live finding: a combo label sorted ahead of the
    plain molecule's own label by effective_time must not be selected.
    """
    combo = _label(["EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE"],
                    boxed_warning=["Lactic acidosis risk from the metformin component."])
    plain = _label(["EMPAGLIFLOZIN"],
                   contraindications=["Hypersensitivity to empagliflozin."])

    with patch.object(httpx.AsyncClient, "get", new=_mock_get({
        "drug/label.json": [[combo, plain]],
    })):
        result = _run(R._fetch_label, "Empagliflozin")

    assert result is plain
    assert "Lactic acidosis" not in str(result)


def test_fetch_label_falls_back_to_a_combination_when_no_single_ingredient_label_exists():
    """A molecule marketed only as part of a fixed-dose product has no
    single-ingredient label to prefer — the combination is the only source and
    must still be returned rather than nothing.
    """
    combo_only = _label(["DRUG A AND DRUG B"])
    with patch.object(httpx.AsyncClient, "get", new=_mock_get({
        "drug/label.json": [[combo_only]],
    })):
        result = _run(R._fetch_label, "Drug A")
    assert result is combo_only


# --------------------------------------------------------------------------
# _fetch_pharm_class / _fetch_dosage_forms: NDC aggregation must not mix in
# a co-formulated ingredient's class or form.
# --------------------------------------------------------------------------

def test_pharm_class_excludes_the_co_formulated_ingredients_class():
    plain = _ndc_record(["EMPAGLIFLOZIN"], pharm_class=["Sodium-Glucose Cotransporter 2 Inhibitor [EPC]"])
    combo_metformin = _ndc_record(["EMPAGLIFLOZIN", "METFORMIN HYDROCHLORIDE"],
                                  pharm_class=["Biguanide [EPC]"])
    combo_linagliptin = _ndc_record(["EMPAGLIFLOZIN", "LINAGLIPTIN"],
                                    pharm_class=["Dipeptidyl Peptidase 4 Inhibitor [EPC]"])

    with patch.object(httpx.AsyncClient, "get", new=_mock_get({
        "drug/ndc.json": [[plain, combo_metformin, combo_linagliptin]],
    })):
        classes = _run(R._fetch_pharm_class, "Empagliflozin")

    assert classes == ["Sodium-Glucose Cotransporter 2 Inhibitor [EPC]"]
    assert "Biguanide [EPC]" not in classes
    assert "Dipeptidyl Peptidase 4 Inhibitor [EPC]" not in classes


def test_dosage_forms_excludes_combination_only_forms():
    plain_tablet = _ndc_record(["DRUG A"], dosage_form="TABLET")
    combo_injection = _ndc_record(["DRUG A", "DRUG B"], dosage_form="INJECTION")

    with patch.object(httpx.AsyncClient, "get", new=_mock_get({
        "drug/ndc.json": [[plain_tablet, combo_injection]],
    })):
        forms = _run(R._fetch_dosage_forms, "Drug A")

    assert forms == ["Tablet"]
    assert "Injection" not in forms


# --------------------------------------------------------------------------
# fetch_us_fda_profile: application-level counts, approval year, and generic
# status must reflect the molecule alone, not every combination it appears in.
# --------------------------------------------------------------------------

def test_is_single_ingredient_application():
    single = _application("NDA204629", [["EMPAGLIFLOZIN"]], "Jardiance")
    combo = _application("NDA206073", [["EMPAGLIFLOZIN", "LINAGLIPTIN"]], "Glyxambi")
    assert R._is_single_ingredient_application(single)
    assert not R._is_single_ingredient_application(combo)


def _run_profile(molecule: str, routes: Dict[str, List[List[Dict[str, Any]]]]) -> Dict[str, Any]:
    with patch.object(httpx.AsyncClient, "get", new=_mock_get(routes)):
        return asyncio.run(R.fetch_us_fda_profile(molecule))


def test_application_count_excludes_combination_applications():
    plain_label = _label(["EMPAGLIFLOZIN"])
    single_app = _application("NDA204629", [["EMPAGLIFLOZIN"]], "Jardiance", "2014-08-01")
    combo_app_1 = _application("NDA206073", [["EMPAGLIFLOZIN", "LINAGLIPTIN"]], "Glyxambi", "2015-01-30")
    combo_app_2 = _application("ANDA212198", [["EMPAGLIFLOZIN", "METFORMIN HYDROCHLORIDE"]],
                               "Empagliflozin and Metformin", "2021-06-01")

    result = _run_profile("Empagliflozin", {
        "drug/label.json": [[plain_label]],
        "drug/drugsfda.json": [[single_app, combo_app_1, combo_app_2]],
    })

    assert result["application_count"] == 1
    assert result["combination_application_count"] == 2
    assert result["info"].approval_year == 2014
    assert "ANDA212198" not in result["info"].application_numbers


def test_approval_year_is_not_pulled_from_an_unrelated_combination():
    """A combination approved before the plain molecule must not make the
    plain molecule appear to have been approved earlier than it was.
    """
    plain_label = _label(["ROSUVASTATIN CALCIUM"])
    single_app = _application("NDA021366", [["ROSUVASTATIN CALCIUM"]], "Crestor", "2003-08-12")
    earlier_combo = _application("NDA209965", [["ROSUVASTATIN CALCIUM", "EZETIMIBE"]],
                                 "Roszet", "1999-01-01")

    result = _run_profile("Rosuvastatin", {
        "drug/label.json": [[plain_label]],
        "drug/drugsfda.json": [[single_app, earlier_combo]],
    })

    assert result["info"].approval_year == 2003
    assert result["info"].innovator_brand_name == "Crestor"


def test_market_status_anda_count_excludes_combination_andas():
    plain_label = _label(["DRUG A"])
    nda = _application("NDA100001", [["DRUG A"]], "Innovator", "2005-01-01")
    combo_anda = _application("ANDA200001", [["DRUG A", "DRUG B"]], "Generic Combo", "2020-01-01")

    result = _run_profile("Drug A", {
        "drug/label.json": [[plain_label]],
        "drug/drugsfda.json": [[nda, combo_anda]],
    })

    assert "no ANDA" in result["market_status"]
