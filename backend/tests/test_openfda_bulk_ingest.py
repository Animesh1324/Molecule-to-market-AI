"""Tests for openFDA bulk ingestion.

Network-free throughout: partition discovery and download are substituted, so
the suite exercises the streaming decoder and the record mapping without
touching api.fda.gov or writing to a database.
"""
import json
import os

import pytest

from app.data_sources.base import DrugRecord
from app.services import openfda_bulk_ingest as bulk


# --------------------------------------------------------------------------
# Streaming decoder
# --------------------------------------------------------------------------

def _write(tmp_path, payload) -> str:
    path = os.path.join(tmp_path, "part.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def test_iter_json_array_yields_every_record(tmp_path):
    payload = {"meta": {"x": 1}, "results": [{"i": n} for n in range(250)]}
    got = list(bulk.iter_json_array(_write(tmp_path, payload)))
    assert [r["i"] for r in got] == list(range(250))


def test_iter_json_array_spans_buffer_boundaries(tmp_path):
    """A record far larger than the 64 KB read block must still decode."""
    payload = {"meta": {}, "results": [{"blob": "x" * 300_000}, {"blob": "y"}]}
    got = list(bulk.iter_json_array(_write(tmp_path, payload)))
    assert len(got) == 2
    assert len(got[0]["blob"]) == 300_000
    assert got[1]["blob"] == "y"


def test_iter_json_array_empty_results(tmp_path):
    assert list(bulk.iter_json_array(_write(tmp_path, {"meta": {}, "results": []}))) == []


def test_iter_json_array_missing_key_yields_nothing(tmp_path):
    assert list(bulk.iter_json_array(_write(tmp_path, {"meta": {}}))) == []


# --------------------------------------------------------------------------
# NDC mapping
# --------------------------------------------------------------------------

NDC_ROW = {
    "product_ndc": "0093-7663",
    "generic_name": "Atorvastatin Calcium",
    "brand_name": "Atorvastatin Calcium",
    "labeler_name": "Teva Pharmaceuticals USA, Inc.",
    "dosage_form": "TABLET, FILM COATED",
    "route": ["ORAL"],
    "product_type": "HUMAN PRESCRIPTION DRUG",
    "marketing_category": "ANDA",
    "application_number": "ANDA090548",
    "marketing_start_date": "20111130",
    "active_ingredients": [{"name": "ATORVASTATIN CALCIUM", "strength": "10 mg/1"}],
    "openfda": {
        "pharm_class": [
            "HMG-CoA Reductase Inhibitor [EPC]",
            "Hydroxymethylglutaryl-CoA Reductase Inhibitors [MoA]",
        ],
        "rxcui": ["617311"],
    },
}


def test_ndc_maps_identity_and_provenance():
    record = bulk.ndc_to_record(NDC_ROW, "2026-08-21")
    assert isinstance(record, DrugRecord)
    assert record.generic_name == "Atorvastatin Calcium"
    assert record.active_ingredients == ["ATORVASTATIN CALCIUM"]
    assert record.strengths == ["10 mg/1"]
    assert record.routes == ["ORAL"]
    assert record.manufacturer == "Teva Pharmaceuticals USA, Inc."
    assert record.status == "active"
    assert record.attribution.source_name == "openFDA"
    assert record.attribution.source_identifier == "0093-7663"
    assert record.attribution.data_version == "2026-08-21"
    # Manufacturer claims to the FDA, not adjudicated fact.
    assert record.attribution.confidence == "reported"


def test_ndc_splits_epc_from_other_classes():
    record = bulk.ndc_to_record(NDC_ROW, None)
    assert record.drug_class == "HMG-CoA Reductase Inhibitor [EPC]"
    assert record.therapeutic_class == "Hydroxymethylglutaryl-CoA Reductase Inhibitors [MoA]"


def test_ndc_without_generic_name_is_dropped():
    assert bulk.ndc_to_record({"brand_name": "Nameless"}, None) is None


def test_ndc_end_dated_listing_is_discontinued_not_dropped():
    row = dict(NDC_ROW, marketing_end_date="20200101")
    record = bulk.ndc_to_record(row, None)
    assert record is not None
    assert record.status == "discontinued"


def test_ndc_reads_top_level_pharm_class():
    """drug/ndc puts pharm_class at the top level, not under openfda.

    Reading only openfda nulled the class for every NDC row in the corpus.
    """
    row = dict(NDC_ROW)
    row.pop("openfda")
    row["pharm_class"] = ["Allergens [CS]", "Increased Histamine Release [PE]"]
    record = bulk.ndc_to_record(row, None)
    assert record.therapeutic_class == "Allergens [CS]"


def test_ndc_reads_top_level_dea_schedule():
    row = dict(NDC_ROW, dea_schedule="CIV")
    assert bulk.ndc_to_record(row, None).extra["dea_schedule"] == "CIV"


def test_field_prefers_top_level_then_falls_back_to_openfda():
    assert bulk._field({"rxcui": ["1"], "openfda": {"rxcui": ["2"]}}, "rxcui") == ["1"]
    assert bulk._field({"openfda": {"rxcui": ["2"]}}, "rxcui") == ["2"]
    assert bulk._field({"openfda": {}}, "rxcui") is None


def test_ndc_carries_identifiers_in_extra():
    record = bulk.ndc_to_record(NDC_ROW, None)
    assert record.extra["product_ndc"] == "0093-7663"
    assert record.extra["marketing_category"] == "ANDA"
    assert record.extra["rxcui"] == ["617311"]


# --------------------------------------------------------------------------
# Label mapping
# --------------------------------------------------------------------------

LABEL_ROW = {
    "id": "abc-123",
    "effective_time": "20250104",
    "indications_and_usage": ["To reduce the risk of MI in adults."],
    "dosage_and_administration": ["10 to 80 mg once daily."],
    "contraindications": ["Acute liver failure."],
    "warnings_and_cautions": ["Myopathy and rhabdomyolysis."],
    "adverse_reactions": ["Nasopharyngitis, arthralgia."],
    "drug_interactions": ["Cyclosporine increases exposure."],
    "mechanism_of_action": ["Selective inhibitor of HMG-CoA reductase."],
    "openfda": {
        "generic_name": ["ATORVASTATIN CALCIUM"],
        "brand_name": ["LIPITOR"],
        "manufacturer_name": ["Parke-Davis"],
        "substance_name": ["ATORVASTATIN CALCIUM TRIHYDRATE"],
        "route": ["ORAL"],
        "pharm_class": ["HMG-CoA Reductase Inhibitor [EPC]"],
    },
}


def test_label_maps_clinical_narrative():
    record = bulk.label_to_record(LABEL_ROW, "2026-08-21")
    assert record.generic_name == "ATORVASTATIN CALCIUM"
    assert record.brand_name == "LIPITOR"
    assert record.indications.startswith("To reduce the risk of MI")
    assert record.dosage == "10 to 80 mg once daily."
    assert record.contraindications == "Acute liver failure."
    assert "Myopathy" in record.warnings
    assert "Nasopharyngitis" in record.adverse_effects
    assert "Cyclosporine" in record.drug_interactions
    assert "HMG-CoA reductase" in record.mechanism
    assert record.attribution.source_identifier == "abc-123"


def test_label_absent_sections_stay_none():
    """Missing must remain distinguishable from empty - see base.DrugRecord."""
    record = bulk.label_to_record(LABEL_ROW, None)
    assert record.pregnancy_information is None
    assert record.lactation_information is None


def test_label_falls_back_to_substance_when_generic_absent():
    row = json.loads(json.dumps(LABEL_ROW))
    del row["openfda"]["generic_name"]
    record = bulk.label_to_record(row, None)
    assert record.generic_name == "ATORVASTATIN CALCIUM TRIHYDRATE"


def test_label_without_any_name_is_dropped():
    assert bulk.label_to_record({"id": "x", "openfda": {}}, None) is None


# --------------------------------------------------------------------------
# Ingestion loop
# --------------------------------------------------------------------------

@pytest.fixture
def fake_partition(tmp_path, monkeypatch):
    """Serve one local partition instead of downloading from openFDA."""
    def _install(dataset, rows):
        path = os.path.join(tmp_path, f"{dataset}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"meta": {}, "results": rows}, handle)
        part = bulk.Partition(dataset=dataset, url=f"http://local/{dataset}.zip", export_date="2026-08-21")
        monkeypatch.setattr(bulk, "list_partitions", lambda ds, **kw: [part])
        monkeypatch.setattr(bulk, "download_partition", lambda p, cache_dir, **kw: path)
        return path
    return _install


def test_ingest_dataset_writes_every_valid_record(fake_partition, tmp_path):
    fake_partition("ndc", [NDC_ROW, dict(NDC_ROW, product_ndc="1"), {"brand_name": "no generic"}])
    written = []
    result = bulk.ingest_dataset(
        "ndc", cache_dir=str(tmp_path), keep_files=True,
        upsert=lambda r: written.append(r) or "id",
    )
    # The nameless row is dropped by the mapper, so it never reaches upsert.
    assert result.read == 2
    assert result.written == 2
    assert len(written) == 2


def test_ingest_counts_unidentifiable_records(fake_partition, tmp_path):
    """Labels with no openfda block have no resolvable name - count, don't hide."""
    fake_partition("label", [LABEL_ROW, {"id": "no-openfda"}, {"id": "empty", "openfda": {}}])
    result = bulk.ingest_dataset(
        "label", cache_dir=str(tmp_path), keep_files=True, upsert=lambda r: "id",
    )
    assert result.read == 1
    assert result.written == 1
    assert result.unidentifiable == 2


def test_ingest_dataset_honours_limit(fake_partition, tmp_path):
    fake_partition("ndc", [dict(NDC_ROW, product_ndc=str(n)) for n in range(50)])
    result = bulk.ingest_dataset(
        "ndc", cache_dir=str(tmp_path), limit=10, keep_files=True, upsert=lambda r: "id",
    )
    assert result.read == 10


def test_ingest_dataset_survives_a_failing_upsert(fake_partition, tmp_path):
    fake_partition("ndc", [dict(NDC_ROW, product_ndc=str(n)) for n in range(5)])

    calls = {"n": 0}

    def flaky(record):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("transient database error")
        return "id"

    result = bulk.ingest_dataset(
        "ndc", cache_dir=str(tmp_path), keep_files=True, upsert=flaky,
    )
    # One bad row must not abort the remaining load.
    assert result.read == 5
    assert result.written == 4
    assert result.failed == 1


def test_ingest_dataset_deletes_partition_unless_kept(fake_partition, tmp_path):
    path = fake_partition("ndc", [NDC_ROW])
    bulk.ingest_dataset("ndc", cache_dir=str(tmp_path), upsert=lambda r: "id")
    assert not os.path.exists(path)


def test_unknown_dataset_is_rejected(tmp_path):
    with pytest.raises(bulk.BulkUnavailable):
        list(bulk.iter_records("event", str(tmp_path), None))


def test_unreachable_index_raises_bulk_unavailable(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("network down")
    monkeypatch.setattr(bulk.urllib.request, "urlopen", boom)
    with pytest.raises(bulk.BulkUnavailable):
        bulk.list_partitions("ndc")


# --------------------------------------------------------------------------
# SPL name derivation (recovering labels with no openfda block)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("element,brand,generic", [
    # Generic repeated immediately, no proprietary name.
    ("Ofloxacin Ofloxacin OFLOXACIN OFLOXACIN Sodium Chloride", None, "Ofloxacin"),
    # Case differs between the two writings.
    ("GABAPENTIN gabapentin GABAPENTIN GABAPENTIN MANNITOL", None, "GABAPENTIN"),
    # Proprietary name then a repeated two-token generic.
    ("Plavix clopidogrel bisulfate clopidogrel bisulfate clopidogrel castor oil",
     "Plavix", "clopidogrel bisulfate"),
    ("Hand Sanitizer Alcohol ALCOHOL ALCOHOL water", "Hand Sanitizer", "Alcohol"),
])
def test_derive_names_from_spl_resolves_known_layouts(element, brand, generic):
    assert bulk.derive_names_from_spl(element) == (brand, generic)


@pytest.mark.parametrize("element", [
    "",
    None,
    "Singleton",
    # Multi-ingredient combination: no run repeats, so no name is established.
    "Polymyxin B Sulfate and Trimethoprim Polymyxin B Sulfate and Trimethoprim Sulfate POLYMYXIN",
    # Generic written only once.
    "OxyContin oxycodone hydrochloride BUTYLATED HYDROXYTOLUENE HYPROMELLOSES",
])
def test_derive_names_declines_rather_than_guessing(element):
    """A wrong generic name is worse than an absent one - see the docstring."""
    assert bulk.derive_names_from_spl(element) == (None, None)


def test_label_without_openfda_is_recovered_and_marked_derived():
    row = {
        "id": "spl-1",
        "spl_product_data_elements": ["Lorazepam Lorazepam LORAZEPAM LACTOSE"],
        "adverse_reactions": ["Sedation, dizziness."],
        "contraindications": ["Acute narrow-angle glaucoma."],
        "openfda": {},
    }
    record = bulk.label_to_record(row, "2026-08-21")
    assert record is not None
    assert record.generic_name == "Lorazepam"
    assert "Sedation" in record.adverse_effects
    # Identity was parsed, not asserted by the FDA - provenance must say so.
    assert record.attribution.confidence == "derived"


def test_annotated_label_stays_reported_not_derived():
    assert bulk.label_to_record(LABEL_ROW, None).attribution.confidence == "reported"


def test_unparseable_label_is_still_dropped():
    row = {"id": "x", "openfda": {}, "spl_product_data_elements": ["OxyContin oxycodone hydrochloride BUTYLATED"]}
    assert bulk.label_to_record(row, None) is None
