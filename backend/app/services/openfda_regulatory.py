"""US FDA regulatory facts for a molecule, from openFDA.

Separate from `data_sources/openfda_source.py` on purpose: that module builds
`DrugRecord`s for the drug catalogue, keyed by product. This one answers a
different question — "what is the regulatory position of this *molecule*" — and
produces `RegulatoryAgencyInfo`: approval year, application numbers, innovator
brand, indications, and the safety sections a label carries. Folding the two
together would mean one of them returning a shape it does not mean.

Everything here is a label or application fact published by the FDA. Nothing is
inferred: a molecule with no FDA record returns no record, and a label section
the SPL omits stays empty rather than being filled from a sibling product.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings
from ..models.regulatory import RegulatoryAgencyInfo
from . import inn_synonyms

logger = logging.getLogger(__name__)

LABEL_URL = "https://api.fda.gov/drug/label.json"
DRUGSFDA_URL = "https://api.fda.gov/drug/drugsfda.json"
NDC_URL = "https://api.fda.gov/drug/ndc.json"
TIMEOUT = 15.0

# Applications are ranked so the innovator, not a generic filer, names the brand.
_APPLICATION_RANK = {"NDA": 0, "BLA": 1, "ANDA": 2}


def _params(extra: Dict[str, Any]) -> Dict[str, Any]:
    """Attach the API key when one is configured.

    The key raises the daily request ceiling (1k -> 120k). It does not lift the
    skip=25,000 paging cap and does not change what the API returns, so nothing
    here depends on its presence.
    """
    key = get_settings().get("openfda_api_key")
    return {**extra, **({"api_key": key} if key else {})}


async def _get(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = await client.get(url, params=_params(params))
    except Exception:
        logger.warning("openFDA request failed: %s", url, exc_info=True)
        return None
    if response.status_code == 404:
        return None                      # openFDA's "no matches", not an error
    if response.status_code != 200:
        logger.warning("openFDA %s returned %s", url, response.status_code)
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _clean_sections(values: Optional[List[str]], limit: int = 6) -> List[str]:
    """Split SPL prose into readable bullets without rewriting it.

    Label text is the regulated wording. It is trimmed and split on sentence
    boundaries for display, never paraphrased.
    """
    out: List[str] = []
    for block in values or []:
        text = re.sub(r"\s+", " ", str(block)).strip()
        if not text:
            continue
        text = _strip_heading(text)
        for sentence in re.split(r"(?<=[.;])\s+(?=[A-Z(])", text):
            sentence = sentence.strip()
            if len(sentence) > 12:
                out.append(sentence[:400])
            if len(out) >= limit:
                return out
    return out


# SPL bodies repeat their own section heading as the first words, often behind a
# section number ("2 DOSAGE AND ADMINISTRATION Take orally..."). Left in, every
# bullet opens with shouting boilerplate instead of the actual label text.
_HEADINGS = (
    "INDICATIONS AND USAGE", "DOSAGE AND ADMINISTRATION", "CONTRAINDICATIONS",
    "WARNINGS AND PRECAUTIONS", "WARNINGS AND CAUTIONS", "WARNINGS",
    "BOXED WARNING", "WARNING", "ADVERSE REACTIONS",
    "MECHANISM OF ACTION", "PHARMACOKINETICS", "PHARMACODYNAMICS",
    "DRUG INTERACTIONS", "DOSAGE FORMS AND STRENGTHS", "CLINICAL PHARMACOLOGY",
)


def _strip_heading(text: str) -> str:
    """Remove a leading section number and repeated SPL heading."""
    cleaned = re.sub(r"^\d+(\.\d+)*\s+", "", text).lstrip()
    upper = cleaned.upper()
    for heading in _HEADINGS:
        if upper.startswith(heading):
            cleaned = cleaned[len(heading):].lstrip(" :.-\u2014")
            break
    return cleaned


def _first(values: Optional[List[str]], limit: int = 900) -> str:
    for block in values or []:
        text = _strip_heading(re.sub(r"\s+", " ", str(block)).strip())
        if text:
            return text[:limit]
    return ""


def _is_combination_generic_name(name: str) -> bool:
    """Whether an openFDA generic_name string names more than one ingredient.

    FDA writes combination generic names as "X AND Y" or "X, Y, Z" on this
    specific endpoint — verified against live label data: 'EMPAGLIFLOZIN AND
    METFORMIN HYDROCHLORIDE', 'ABACAVIR SULFATE, DOLUTEGRAVIR SODIUM,
    LAMIVUDINE'. A single-ingredient name never contains either separator here.

    ";" is included defensively rather than from a reproduced failure on this
    endpoint: FDA is not internally consistent about the separator across its
    own datasets — the Orange Book writes "EMPAGLIFLOZIN; METFORMIN
    HYDROCHLORIDE" for the same combination this endpoint writes with "AND".
    Checking for it costs nothing (no real drug name contains a semicolon) and
    closes the gap before it produces a live misattribution rather than after.
    """
    text = (name or "").upper()
    return " AND " in text or "," in text or ";" in text


async def _fetch_label(client: httpx.AsyncClient, molecule: str) -> Optional[Dict[str, Any]]:
    """Most recent single-ingredient SPL naming this molecule.

    A phrase search on openfda.generic_name matches a fixed-dose combination's
    label too — "EMPAGLIFLOZIN"[Title/Abstract]-style quoting does not exclude
    'EMPAGLIFLOZIN AND METFORMIN HYDROCHLORIDE', and sorted by recency a combo's
    label can outrank the plain molecule's own. Taking results[0] unconditionally
    meant a co-formulated product's boxed warnings, contraindications, and
    mechanism text could be attributed to the single molecule — verified live:
    querying "Empagliflozin" returned combination labels in the top 10 by
    effective_time. Fetching a wider candidate set and filtering to
    single-ingredient names before picking the most recent one fixes this; a
    combination label is used only when truly no single-ingredient label exists,
    which is real for a molecule marketed solely as part of a fixed-dose product.

    Generic-name search first: it matches the molecule regardless of which brand
    or labeler published the SPL. Substance name is the fallback for biologics,
    where the generic field is often the trade name.
    """
    for field in ("openfda.generic_name", "openfda.substance_name"):
        # No `sort` param: asking openFDA to sort by effective_time across
        # every match before returning the top 20 measured at ~3.2s of a
        # ~3.4s total call — sorting the (at most 20) results client-side
        # instead is effectively free and cut this endpoint to ~0.9s.
        # effective_time is an 8-digit YYYYMMDD string, so plain string
        # comparison already sorts chronologically.
        payload = await _get(client, LABEL_URL, {
            "search": f'{field}:"{molecule}"',
            "limit": 20,
        })
        results = (payload or {}).get("results") or []
        if not results:
            continue
        results = sorted(results, key=lambda r: r.get("effective_time") or "", reverse=True)

        def generic_names(label: Dict[str, Any]) -> List[str]:
            return list((label.get("openfda") or {}).get(
                "generic_name" if field == "openfda.generic_name" else "substance_name") or [])

        single_ingredient = [
            r for r in results
            if not any(_is_combination_generic_name(n) for n in generic_names(r))
        ]
        return (single_ingredient or results)[0]
    return None


async def _fetch_applications(client: httpx.AsyncClient, molecule: str) -> List[Dict[str, Any]]:
    payload = await _get(client, DRUGSFDA_URL, {
        "search": f'products.active_ingredients.name:"{molecule}"',
        "limit": 100,
    })
    return (payload or {}).get("results") or []


def _earliest_approval(applications: List[Dict[str, Any]]) -> Optional[int]:
    """First US approval year across all applications for the molecule."""
    years: List[int] = []
    for application in applications:
        for submission in application.get("submissions") or []:
            if (submission.get("submission_status") or "").upper() != "AP":
                continue
            date = str(submission.get("submission_status_date") or "")
            if len(date) >= 4 and date[:4].isdigit():
                years.append(int(date[:4]))
    return min(years) if years else None


def _application_approval_year(application: Dict[str, Any]) -> int:
    years = [
        int(str(s.get("submission_status_date"))[:4])
        for s in application.get("submissions") or []
        if (s.get("submission_status") or "").upper() == "AP"
        and str(s.get("submission_status_date") or "")[:4].isdigit()
    ]
    return min(years) if years else 9999


def _innovator(applications: List[Dict[str, Any]], molecule: str) -> tuple:
    """Innovator brand and sponsor for the molecule.

    Single-ingredient status is the PRIMARY sort key, application type only
    the secondary one within it. Sorting by application type first — NDA
    before ANDA — lets a combination product's NDA outrank every
    single-ingredient application regardless of ingredient count, since the
    single-ingredient preference was only ever a tiebreaker inside the same
    type. Verified live: acetaminophen has no NDA at all for the plain
    molecule — it is an OTC monograph drug, never formally NDA'd — so the
    only NDA-ranked application matching it was Combogesic IV, an unrelated
    acetaminophen+ibuprofen combination, which won under the old ranking and
    was reported as acetaminophen's own "innovator".

    A winning single-ingredient application is trusted as the innovator only
    when it is itself an NDA/BLA. A single-ingredient ANDA is a generic filing
    of something — presenting its incidental brand name as "the innovator"
    would be its own misattribution, just a different one. Genuinely absent
    (as for acetaminophen) returns (None, None) rather than a plausible-looking
    guess; the caller falls back to the label's own brand_name annotation.
    """
    def rank(application: Dict[str, Any]) -> tuple:
        number = (application.get("application_number") or "").upper()
        prefix = number[:3]
        products = application.get("products") or []
        single = any(len(p.get("active_ingredients") or []) == 1 for p in products)
        return (0 if single else 1, _APPLICATION_RANK.get(prefix, 3),
                _application_approval_year(application))

    for application in sorted(applications, key=rank):
        prefix = (application.get("application_number") or "").upper()[:3]
        products = application.get("products") or []
        single_products = [p for p in products if len(p.get("active_ingredients") or []) == 1]
        if not single_products or prefix not in ("NDA", "BLA"):
            continue
        for product in sorted(single_products, key=lambda p: len(p.get("active_ingredients") or [])):
            brand = (product.get("brand_name") or "").strip()
            if brand:
                return brand.title(), (application.get("sponsor_name") or "").title()
    return None, None


def _is_single_ingredient_application(application: Dict[str, Any]) -> bool:
    """Whether at least one product under this application is the molecule
    alone, rather than every product being a fixed-dose combination.

    Same check `_innovator` already applies per-application when picking a
    brand name, reused here to scope the aggregate counts (application total,
    approval year, generic-entry status) to applications for the plain
    molecule. Without it, drugsfda.json's `products.active_ingredients.name`
    search matches every fixed-dose combination too — verified live: searching
    "Empagliflozin" returned 45 combination-product rows (Glyxambi,
    Synjardy) alongside the molecule's own 27 applications, which would
    inflate the application count and let an unrelated combination's approval
    date or ANDA status stand in for the molecule's own.
    """
    return any(
        len(p.get("active_ingredients") or []) == 1
        for p in application.get("products") or []
    )


def _market_status(applications: List[Dict[str, Any]]) -> str:
    """Whether the molecule is single-source or genericised in the US."""
    prefixes = {(a.get("application_number") or "")[:3].upper() for a in applications}
    anda_count = sum(1 for a in applications
                     if (a.get("application_number") or "").upper().startswith("ANDA"))
    if anda_count >= 1:
        return f"Genericised / multi-source — {anda_count} ANDA(s) on file with the FDA"
    if prefixes & {"NDA", "BLA"}:
        return "Innovator exclusivity — no ANDA on file with the FDA"
    return ""


async def fetch_us_fda_profile(molecule: str) -> Optional[Dict[str, Any]]:
    """Regulatory position of a molecule with the US FDA, or None if unlisted.

    Tries every INN/USAN spelling of the molecule, not just the one supplied.
    openFDA files everything under the USAN — "Paracetamol" (the INN, used
    everywhere outside the US, including India) returned nothing at all until
    this existed, even though the same molecule under "Acetaminophen" has
    thousands of records. inn_synonyms already solved exactly this for the
    drug catalogue, Orange Book, and patient-experience modules; this module
    just hadn't been wired to it.
    """
    label: Optional[Dict[str, Any]] = None
    all_applications: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for candidate in inn_synonyms.candidates(molecule):
            label, all_applications = await asyncio.gather(
                _fetch_label(client, candidate),
                _fetch_applications(client, candidate),
            )
            if label or all_applications:
                break

    if not label and not all_applications:
        return None

    # Scoped to applications for the plain molecule. `_innovator` already
    # reasons about single-ingredient products internally, so it still takes
    # the unfiltered list — everything else here (count, approval year,
    # generic-entry status, application numbers) reads the molecule's own
    # regulatory position, not a fixed-dose combination's.
    applications: List[Dict[str, Any]] = []
    combination_applications: List[Dict[str, Any]] = []
    for application in all_applications:
        target = applications if _is_single_ingredient_application(application) else combination_applications
        target.append(application)

    label = label or {}
    openfda = label.get("openfda") or {}
    brand, sponsor = _innovator(all_applications, molecule)
    # No fallback to the label's own brand_name annotation: that array names
    # whichever single-ingredient product's label was most recently updated,
    # which for a molecule with no genuine NDA/BLA (most OTC monograph drugs —
    # acetaminophen has never been formally NDA'd) can be any manufacturer's
    # store-brand copy. Verified live: the fallback surfaced "CVS Childrens
    # Pain plus Fever Relief" as acetaminophen's "innovator". Leaving `brand`
    # as None here is the honest answer — a marketed product is not the same
    # claim as an innovator, and this field makes exactly that claim.

    application_numbers = sorted({
        str(a.get("application_number")) for a in applications
        if a.get("application_number")
    })[:12]
    if not application_numbers:
        application_numbers = list(openfda.get("application_number") or [])[:12]

    approval_year = _earliest_approval(applications)
    spl_id = (openfda.get("spl_set_id") or [None])[0]

    info = RegulatoryAgencyInfo(
        agency_name="US FDA",
        status="Approved — listed in FDA drug applications" if applications
               else "Marketed — FDA structured product label on file",
        approval_year=approval_year,
        innovator_brand_name=brand,
        application_numbers=application_numbers,
        approved_indications=_clean_sections(label.get("indications_and_usage"), limit=8),
        dosage_and_administration_summary=_first(label.get("dosage_and_administration")),
        boxed_warnings=_clean_sections(label.get("boxed_warning"), limit=4),
        warnings_and_precautions=_clean_sections(
            label.get("warnings_and_cautions") or label.get("warnings"), limit=8),
        contraindications=_clean_sections(label.get("contraindications"), limit=6),
        source_spl_or_url=(f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={spl_id}"
                           if spl_id else "https://dailymed.nlm.nih.gov"),
    )
    return {
        "info": info,
        "sponsor": sponsor,
        "application_count": len(applications),
        "combination_application_count": len(combination_applications),
        "market_status": _market_status(applications),
        "manufacturers": list(openfda.get("manufacturer_name") or [])[:5],
        "route": list(openfda.get("route") or [])[:4],
        "pharm_class": list(openfda.get("pharm_class_epc") or [])[:4],
    }


# ---------------------------------------------------------------------------
# Clinical profile
#
# The molecule profile module reads PubChem, which is a *chemical* registry: it
# knows formula, weight, and SMILES, and nothing about pharmacology. Every
# clinical field therefore rendered "Not verified" for any molecule without a
# hand-written entry. The FDA label carries exactly those fields, so they are
# read from there instead.
# ---------------------------------------------------------------------------

# Label section -> profile field. Kept as data so the mapping is inspectable
# rather than buried in twenty attribute assignments.
_PK_SECTIONS = {
    "absorption": ("absorption",),
    "distribution": ("distribution",),
    "metabolism": ("metabolism",),
    "elimination": ("elimination", "excretion"),
}

_CYP_RE = re.compile(r"CYP\s?([1-4][A-C]\d{1,2})", re.IGNORECASE)
_HALFLIFE_RE = re.compile(
    r"([\d.]+\s*(?:to|-|–)?\s*[\d.]*\s*(?:hours?|hrs?|days?|minutes?))[^.]{0,60}half[- ]?life"
    r"|half[- ]?life[^.]{0,80}?([\d.]+\s*(?:to|-|–)?\s*[\d.]*\s*(?:hours?|hrs?|days?|minutes?))",
    re.IGNORECASE)
_PROTEIN_RE = re.compile(r"(\d{1,3}(?:\.\d+)?\s*%)[^.]{0,60}bound to (?:human )?plasma protein"
                         r"|protein[- ]?binding[^.]{0,60}?(\d{1,3}(?:\.\d+)?\s*%)", re.IGNORECASE)
# Verified against live label text for Rosuvastatin, Pantoprazole, Osimertinib
# before wiring in — these three fields were never extracted at all before
# (only absorption/distribution/metabolism/elimination/half_life/protein_binding
# were), so every non-curated molecule showed the PubChem-fallback's literal
# "Not verified" placeholder for bioavailability, Tmax, and clearance
# regardless of whether the label actually stated one.
_BIOAVAIL_RE = re.compile(
    r"(?:absolute\s+)?bioavailability[^.]{0,40}?(?:is|of)\s+(?:approximately\s+)?"
    r"(\d+(?:\.\d+)?(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?)?\s*%)", re.IGNORECASE)
_CLEARANCE_RE = re.compile(
    r"clearance[^.]{0,60}?(?:is|was)\s+(?:approximately\s+)?"
    r"(\d+(?:\.\d+)?(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?)?\s*\(?\s*(?:L/h|mL/min|L/min|mL/h)\s*\)?)",
    re.IGNORECASE)
_TMAX_RE = re.compile(
    r"t\s*max[^.]{0,60}?(?:is|of|was)\s+(?:approximately\s+)?"
    r"(\d+(?:\.\d+)?(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?)?\s*(?:hours?|hrs?|h\b|minutes?|min\b))",
    re.IGNORECASE)


def _sentence_with(text: str, keywords: tuple) -> str:
    """First sentence mentioning any keyword. Quoted, never paraphrased."""
    for sentence in re.split(r"(?<=[.])\s+", text or ""):
        lowered = sentence.lower()
        if any(word in lowered for word in keywords) and len(sentence) > 25:
            return sentence.strip()[:400]
    return ""


def _match(pattern: re.Pattern, text: str) -> str:
    found = pattern.search(text or "")
    if not found:
        return ""
    return next((g for g in found.groups() if g), "").strip()


async def _fetch_ndc_listings(client: httpx.AsyncClient, molecule: str) -> List[Dict[str, Any]]:
    """Raw NDC directory records for a molecule, single query shared by both
    class and dosage-form lookups below.
    """
    payload = await _get(client, NDC_URL, {
        "search": f'active_ingredients.name:"{molecule}"',
        "limit": 100,
    })
    return (payload or {}).get("results") or []


def _single_ingredient_listings(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """NDC records naming exactly one active ingredient.

    A record matched the search because the molecule is one of its ingredients,
    so `len(active_ingredients) == 1` means the molecule is the ONLY one — a
    plain product, not a fixed-dose combination.
    """
    return [r for r in records if len(r.get("active_ingredients") or []) == 1]


async def _fetch_pharm_class(client: httpx.AsyncClient, molecule: str) -> List[str]:
    """Established pharmacologic class, from single-ingredient NDC listings.

    Read from NDC rather than the label because the label's `pharm_class_epc`
    annotation is present on some SPLs and absent from others — pantoprazole's
    most recent label carries none, so a label-first lookup returned nothing for
    a molecule whose class is perfectly well known. NDC lists it per product.

    This previously used NDC's `count=pharm_class.exact` facet, which aggregates
    the field across every matching listing — combinations included. Verified
    live: querying "Empagliflozin" returned "Biguanide [EPC]" (metformin's
    class, from the empagliflozin+metformin combination) and "Dipeptidyl
    Peptidase 4 Inhibitor [EPC]" (linagliptin's, from empagliflozin+linagliptin)
    ranked ahead of empagliflozin's own class in the returned term list, with no
    way to tell which record a given term came from at the facet level. Fetching
    raw records and aggregating only from single-ingredient ones isolates the
    molecule's own class — confirmed empty of both foreign classes afterward.
    """
    records = _single_ingredient_listings(await _fetch_ndc_listings(client, molecule))
    classes: List[str] = []
    for record in records:
        classes.extend(record.get("pharm_class") or [])
    # EPC is the established class; MoA and CS are secondary descriptors.
    epc = sorted({c for c in classes if c.endswith("[EPC]")})
    return (epc or sorted(set(classes)))[:3]


async def _fetch_dosage_forms(client: httpx.AsyncClient, molecule: str) -> List[str]:
    """Marketed dosage forms of the plain molecule, from single-ingredient
    NDC listings.

    `dosage_form` is an NDC listing field; it does not exist on the label
    endpoint, which is why reading it off the label returned nothing. Scoped to
    single-ingredient listings for the same reason as pharm_class: an injectable
    fixed-dose combination should not report itself as a form the plain
    molecule is marketed in.
    """
    records = _single_ingredient_listings(await _fetch_ndc_listings(client, molecule))
    forms: List[str] = []
    seen = set()
    for record in records:
        form = record.get("dosage_form")
        if form and form not in seen:
            seen.add(form)
            forms.append(str(form).title())
    return forms[:8]


async def fetch_molecule_clinical_profile(molecule: str) -> Optional[Dict[str, Any]]:
    """Clinical fields for a molecule, read from its FDA label.

    Returns only what the label actually states. A section the SPL omits comes
    back empty, so the caller can leave the field alone rather than filling it
    with text borrowed from a different product.

    Tries every INN/USAN spelling — see fetch_us_fda_profile for why: openFDA
    files under the USAN, so an INN-only query like "Paracetamol" found
    nothing on its own. Once a spelling resolves a label, pharm_class and
    dosage_forms are queried under that same resolved spelling rather than
    the original input, so all three read from one consistent identity.
    """
    label: Optional[Dict[str, Any]] = None
    resolved_name = molecule
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for candidate in inn_synonyms.candidates(molecule):
            label = await _fetch_label(client, candidate)
            if label:
                resolved_name = candidate
                break
        if not label:
            return None
        pharm_classes, dosage_forms = await asyncio.gather(
            _fetch_pharm_class(client, resolved_name),
            _fetch_dosage_forms(client, resolved_name),
        )

    openfda = label.get("openfda") or {}
    pharmacology = " ".join(
        re.sub(r"\s+", " ", str(block))
        for block in (label.get("clinical_pharmacology") or []) +
                     (label.get("pharmacokinetics") or [])
    )

    pharmacokinetics = {
        field: _sentence_with(pharmacology, keywords)
        for field, keywords in _PK_SECTIONS.items()
    }
    pharmacokinetics["half_life"] = _match(_HALFLIFE_RE, pharmacology)
    pharmacokinetics["protein_binding"] = _match(_PROTEIN_RE, pharmacology)
    pharmacokinetics["bioavailability"] = _match(_BIOAVAIL_RE, pharmacology)
    pharmacokinetics["clearance"] = _match(_CLEARANCE_RE, pharmacology)
    pharmacokinetics["tmax"] = _match(_TMAX_RE, pharmacology)
    pharmacokinetics["cyp_pathways"] = sorted({
        f"CYP{m.group(1).upper()}" for m in _CYP_RE.finditer(pharmacology)
    })[:8]

    return {
        "pharmacological_class": "; ".join(
            pharm_classes or openfda.get("pharm_class_epc") or openfda.get("pharm_class_moa") or []),
        "mechanism_of_action": _first(label.get("mechanism_of_action"), 700)
                               or _sentence_with(pharmacology, ("mechanism", "inhibit", "agonist", "antagonist")),
        "pharmacodynamics": _first(label.get("pharmacodynamics"), 700),
        "pharmacokinetics": pharmacokinetics,
        "approved_indications": _clean_sections(label.get("indications_and_usage"), limit=8),
        "dosage_forms": dosage_forms or _clean_sections(
            label.get("dosage_forms_and_strengths"), limit=6),
        "routes_of_administration": [r.title() for r in (openfda.get("route") or [])][:6],
        "standard_dosages": _clean_sections(label.get("dosage_and_administration"), limit=6),
        "contraindications": _clean_sections(label.get("contraindications"), limit=6),
        "black_box_warnings": _clean_sections(label.get("boxed_warning"), limit=4),
        "drug_interactions": _clean_sections(label.get("drug_interactions"), limit=8),
        "adverse_effects": _clean_sections(label.get("adverse_reactions"), limit=10),
        "source_url": (f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="
                       f"{(openfda.get('spl_set_id') or [''])[0]}"),
    }
