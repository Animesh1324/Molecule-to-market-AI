"""Assemble the patent and competitive-entry picture for a molecule or combination.

Answers the questions a brand manager otherwise gathers by hand from the FDA
site: who holds the innovator application, what patents cover it and when they
expire, what exclusivity is running, and which generic filers have been
approved with which trade names.
"""
import logging
from typing import Dict, List, Optional, Tuple

from ..models.lifecycle import (
    ExclusivityRecord,
    MarketedProduct,
    MoleculeLifecycle,
    PatentRecord,
)
from . import orange_book
from .inn_synonyms import candidates as name_candidates
from .molecule_resolver import ResolvedMolecule, resolve

logger = logging.getLogger(__name__)

# Commercial data a public source cannot supply. Named explicitly so the UI can
# show the gap rather than implying the number is simply missing.
UNAVAILABLE_PUBLICLY = [
    "Unit and value sales by brand (licensed: IQVIA, AIOCD-AWACS)",
    "Price to stockist and price to retailer (trade margin data is not published)",
    "India patent status and expiry (IP India has no public API)",
    "CDSCO approval registry (no machine-readable endpoint)",
]


def _matches_all_components(row: dict, components: List[str]) -> bool:
    """Whether an Orange Book row's ingredient list covers every component.

    Each component is checked under all of its spellings, so an FDC typed as
    "Paracetamol + Caffeine" matches a row listed as "ACETAMINOPHEN; CAFFEINE".
    """
    ingredients = (row.get("Ingredient") or "").lower()
    for component in components:
        if not any(alias in ingredients for alias in name_candidates(component)):
            return False
    return True


def _product_from_row(row: dict) -> MarketedProduct:
    appl_type = (row.get("Appl_Type") or "").strip().upper()
    return MarketedProduct(
        trade_name=(row.get("Trade_Name") or "").strip() or "Unnamed",
        applicant=(row.get("Applicant") or "").strip(),
        applicant_full_name=(row.get("Applicant_Full_Name") or "").strip() or None,
        strength=(row.get("Strength") or "").strip() or None,
        dosage_form_route=(row.get("DF;Route") or "").strip() or None,
        application_type="NDA" if appl_type == "N" else "ANDA" if appl_type == "A" else appl_type,
        application_number=(row.get("Appl_No") or "").strip(),
        approval_date=(row.get("Approval_Date") or "").strip() or None,
        is_reference_listed_drug=(row.get("RLD") or "").strip().lower() == "yes",
        therapeutic_equivalence_code=(row.get("TE_Code") or "").strip() or None,
    )


def _dedupe(products: List[MarketedProduct]) -> List[MarketedProduct]:
    """One row per trade name + applicant + application; strengths collapse."""
    seen: Dict[Tuple[str, str, str], MarketedProduct] = {}
    for product in products:
        key = (product.trade_name.lower(), product.applicant.lower(), product.application_number)
        if key not in seen:
            seen[key] = product
    return list(seen.values())


def _sort_key(product: MarketedProduct):
    parsed = orange_book.parse_date(product.approval_date)
    return (parsed is None, parsed or 0, product.trade_name)


def build_lifecycle(molecule: str) -> MoleculeLifecycle:
    """Return the lifecycle picture, handling single molecules and combinations."""
    resolved: ResolvedMolecule = resolve(molecule)
    if not resolved.components:
        return MoleculeLifecycle(
            query=molecule,
            display_name=molecule,
            coverage_note="No molecule name supplied.",
            unavailable=list(UNAVAILABLE_PUBLICLY),
        )

    index = orange_book.get_index()
    if not index.get("available"):
        return MoleculeLifecycle(
            query=molecule,
            display_name=resolved.display_name,
            components=resolved.components,
            is_combination=resolved.is_combination,
            coverage_note=(
                "FDA Orange Book could not be reached, so patent and competitor "
                "data is unavailable for this request. Retry shortly."
            ),
            data_sources=[],
            unavailable=list(UNAVAILABLE_PUBLICLY),
        )

    # Gather candidate rows from every component, then keep only the products
    # whose ingredient list covers the whole combination.
    candidates: List[dict] = []
    for component in resolved.components:
        candidates.extend(orange_book.products_for(component))

    matching = [r for r in candidates if _matches_all_components(r, resolved.components)]

    products = _dedupe([_product_from_row(r) for r in matching])
    products.sort(key=_sort_key)

    innovators = [p for p in products if p.application_type == "NDA"]
    generics = [p for p in products if p.application_type == "ANDA"]

    # The innovator is the earliest-approved reference listed drug, falling back
    # to the earliest NDA when no row carries the RLD flag.
    rld = [p for p in innovators if p.is_reference_listed_drug]
    innovator = (rld or innovators or [None])[0]

    patents: List[PatentRecord] = []
    exclusivity: List[ExclusivityRecord] = []
    seen_patents = set()
    seen_exclusivity = set()

    for product in innovators:
        for row in orange_book.patents_for(product.application_number):
            number = (row.get("Patent_No") or "").strip()
            expiry = (row.get("Patent_Expire_Date_Text") or "").strip()
            if not number or (number, expiry) in seen_patents:
                continue
            seen_patents.add((number, expiry))
            patents.append(
                PatentRecord(
                    patent_number=number,
                    expiry_date=expiry,
                    submission_date=(row.get("Submission_Date") or "").strip() or None,
                    drug_substance=(row.get("Drug_Substance_Flag") or "").strip().upper() == "Y",
                    drug_product=(row.get("Drug_Product_Flag") or "").strip().upper() == "Y",
                    use_code=(row.get("Patent_Use_Code") or "").strip() or None,
                )
            )
        for row in orange_book.exclusivity_for(product.application_number):
            code = (row.get("Exclusivity_Code") or "").strip()
            date = (row.get("Exclusivity_Date") or "").strip()
            if not code or (code, date) in seen_exclusivity:
                continue
            seen_exclusivity.add((code, date))
            exclusivity.append(
                ExclusivityRecord(
                    code=code,
                    expiry_date=date,
                    description=orange_book.EXCLUSIVITY_CODES.get(code.rstrip("*").upper()),
                )
            )

    patents.sort(key=lambda p: (orange_book.parse_date(p.expiry_date) is None,
                                orange_book.parse_date(p.expiry_date) or 0), reverse=True)
    dated = [p for p in patents if orange_book.parse_date(p.expiry_date)]
    latest_expiry = dated[0].expiry_date if dated else None

    first_generic = next(
        (g.approval_date for g in generics if orange_book.parse_date(g.approval_date)), None
    )

    if products:
        note = (
            f"{len(products)} FDA-listed product(s) for {resolved.display_name}: "
            f"{len(innovators)} innovator application(s), {len(generics)} generic filer(s)."
        )
        if resolved.is_combination:
            note += " Matched on products containing every component of the combination."
    else:
        note = (
            f"No FDA-listed product matches {resolved.display_name}. "
            "This is expected for molecules approved only outside the US, or for "
            "combinations marketed without a US application."
        )

    return MoleculeLifecycle(
        query=molecule,
        display_name=resolved.display_name,
        components=resolved.components,
        is_combination=resolved.is_combination,
        innovator_company=innovator.applicant_full_name or innovator.applicant if innovator else None,
        innovator_brand=innovator.trade_name if innovator else None,
        innovator_application=(
            f"{innovator.application_type}{innovator.application_number}" if innovator else None
        ),
        first_approval_date=innovator.approval_date if innovator else None,
        patents=patents,
        latest_patent_expiry=latest_expiry,
        exclusivity=exclusivity,
        generic_entrants=generics,
        generic_entrant_count=len(generics),
        first_generic_approval_date=first_generic,
        all_products=products,
        data_sources=["FDA Orange Book (Approved Drug Products with Therapeutic Equivalence Evaluations)"],
        coverage_note=note,
        unavailable=list(UNAVAILABLE_PUBLICLY),
    )
