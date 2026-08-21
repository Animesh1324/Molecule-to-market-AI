"""India (CDSCO) regulatory checklist with direct links to the source registers.

CDSCO publishes its registers as PDFs and search forms behind a session, with
no machine-readable endpoint, so this cannot be fetched the way FDA data can.
What it can do is remove the part that actually wastes a brand manager's time:
knowing which of the dozen CDSCO registers matters for a given question, what
each one settles, and landing on the right page with the molecule in hand.

Every item states what to look for and what it means for the plan, so the
manual check takes minutes and its result is recorded against the project.
"""
from typing import Dict, List
from urllib.parse import quote_plus

from ..models.cdsco import CDSCOChecklistItem, CDSCOIntelligence
from .molecule_resolver import resolve as resolve_molecule

CDSCO_HOME = "https://cdsco.gov.in"


def _items(display_name: str, indication: str) -> List[CDSCOChecklistItem]:
    q = quote_plus(display_name)
    return [
        CDSCOChecklistItem(
            step="Approval status in India",
            source_register="CDSCO — Approved New Drugs list",
            url=f"{CDSCO_HOME}/opencms/opencms/en/Drugs/Approval-of-New-Drugs/",
            what_to_check=(
                f"Search the year-wise approved new drug PDFs for '{display_name}'. "
                "Record the approval date, the approved indication wording, and the "
                "strengths and dosage forms granted."
            ),
            why_it_matters=(
                "The Indian approved indication frequently differs from the FDA's. "
                "Every promotional claim must sit inside the Indian wording, not the US one."
            ),
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Fixed-dose combination legitimacy",
            source_register="CDSCO — Approved / Prohibited FDC lists",
            url=f"{CDSCO_HOME}/opencms/opencms/en/Drugs/FDC/",
            what_to_check=(
                f"Confirm '{display_name}' appears on the approved FDC list and not on "
                "any banned/irrational FDC notification."
            ),
            why_it_matters=(
                "India has prohibited hundreds of FDCs. Building a plan on a combination "
                "that is later notified as irrational writes off the entire investment."
            ),
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Import / manufacture licence route",
            source_register="CDSCO — Form CT-20 / CT-21, Form 45, Form 46",
            url=f"{CDSCO_HOME}/opencms/opencms/en/Drugs/Import-and-Registration/",
            what_to_check=(
                "Establish whether your entity holds, or must apply for, the relevant "
                "import registration or manufacturing licence for this molecule."
            ),
            why_it_matters="Determines the realistic launch date and the regulatory workload before it.",
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Schedule classification",
            source_register="Drugs and Cosmetics Rules — Schedules H, H1, X",
            url=f"{CDSCO_HOME}/opencms/opencms/en/Acts-and-Rules/",
            what_to_check=(
                f"Determine whether '{display_name}' is Schedule H, H1, or X, and record "
                "the mandated label warning."
            ),
            why_it_matters=(
                "Schedule H1 obliges a specific warning box and a sales register. It shapes "
                "pack artwork, chemist detailing, and what the field force may leave behind."
            ),
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Price control status",
            source_register="NPPA — DPCO ceiling prices / NLEM",
            url="https://www.nppaindia.nic.in/en/ceiling-price/",
            what_to_check=(
                f"Check whether '{display_name}' or its class appears in the National List "
                "of Essential Medicines or carries a DPCO ceiling price."
            ),
            why_it_matters=(
                "A scheduled formulation has its price capped and annual increases limited. "
                "This decides whether your pricing and trade-margin model is even legal."
            ),
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Indian clinical trial footprint",
            source_register="CTRI — Clinical Trials Registry India",
            url=f"https://ctri.nic.in/Clinicaltrials/advsearch.php?searchterm={q}",
            what_to_check=(
                f"Search CTRI for '{display_name}'"
                + (f" in {indication}" if indication else "")
                + ". Note Indian investigators, sites, and sponsors."
            ),
            why_it_matters=(
                "Indian trial data and local investigators carry disproportionate weight "
                "with Indian prescribers and are the natural starting point for the "
                "advisory board and KOL map."
            ),
            blocks_launch=False,
        ),
        CDSCOChecklistItem(
            step="Existing Indian brands on the molecule",
            source_register="CDSCO product search / state FDA registers",
            url=f"{CDSCO_HOME}/opencms/opencms/en/Drugs/",
            what_to_check=(
                f"List every brand already marketing '{display_name}' in India, with the "
                "marketing company and strengths."
            ),
            why_it_matters=(
                "Establishes how crowded the molecule is, and which brand names are "
                "already taken before trademark screening begins."
            ),
            blocks_launch=False,
        ),
        CDSCOChecklistItem(
            step="Pharmacovigilance obligation",
            source_register="PvPI — Pharmacovigilance Programme of India",
            url="https://ipc.gov.in/PvPI/pv_home.html",
            what_to_check="Confirm the PSUR schedule and the adverse-event reporting route for the product.",
            why_it_matters="A licence condition. Non-compliance puts the marketing authorisation at risk.",
            blocks_launch=False,
        ),
        CDSCOChecklistItem(
            step="Promotional code compliance",
            source_register="UCPMP — Uniform Code for Pharmaceutical Marketing Practices",
            url="https://pharmaceuticals.gov.in/uniform-code-pharmaceutical-marketing-practices",
            what_to_check=(
                "Check the current UCPMP edition for what the plan plans to do: gifts, "
                "hospitality, travel, sampling, and expert engagement."
            ),
            why_it_matters=(
                "UCPMP is now enforced with declarations. Field tactics and KOL engagement "
                "must be designed inside it, not corrected afterwards."
            ),
            blocks_launch=True,
        ),
        CDSCOChecklistItem(
            step="Trademark clearance",
            source_register="IP India — Public trademark search",
            url="https://tmrsearch.ipindia.gov.in/tmrpublicsearch/",
            what_to_check=(
                "Run each shortlisted brand name in class 5 (pharmaceuticals). Record the "
                "application numbers of anything similar."
            ),
            why_it_matters=(
                "Names are cleared or lost here. The search requires a CAPTCHA, so it must "
                "be run by a person — the shortlist is prepared for you in the trademark module."
            ),
            blocks_launch=True,
        ),
    ]


def build_cdsco_intelligence(molecule: str, indication: str = "") -> CDSCOIntelligence:
    resolved = resolve_molecule(molecule)
    display = resolved.display_name or molecule
    items = _items(display, indication)
    return CDSCOIntelligence(
        query=molecule,
        display_name=display,
        components=resolved.components,
        is_combination=resolved.is_combination,
        checklist=items,
        blocking_steps=[i.step for i in items if i.blocks_launch],
        automation_note=(
            "CDSCO and IP India publish their registers as PDFs and CAPTCHA-protected "
            "search forms, with no public API, so these cannot be fetched automatically. "
            "Each step below links straight to the right register with the molecule "
            "prefilled where the site allows it."
        ),
        india_specific_warning=(
            f"Do not assume the FDA position applies to India. For {display}, the Indian "
            "approved indication, schedule, FDC status, and price control are all set "
            "independently and frequently differ."
        ),
    )
