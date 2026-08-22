"""Claude-backed drafting for the strategic brand plan.

What the model is allowed to write is deliberately narrow. It drafts *strategy*
— positioning rationale, segmentation, launch sequencing, the questions a brand
team should answer — and never *clinical results*. Effect sizes, p-values,
comparative superiority, and dosing come from the Evidence and Regulatory
modules, which are source-backed; anything the model writes is screened against
`compliance` before it reaches the plan, and MLR signoff stays false either way.
"""
import logging
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..models.brand_plan import BrandPlanSection, CompleteBrandPlan
from . import compliance
from .claude_client import ClaudeUnavailable, generate_json, is_configured

logger = logging.getLogger(__name__)

# Narrative fields the model may draft. Everything else on the plan — the KPI
# scorecard, the milestone calendar, section titles and categories — stays
# deterministic so the document's structure never depends on a model call.
_NARRATIVE_FIELDS: List[str] = [
    "mission",
    "vision",
    "brand_objective",
    "therapy_area_opportunity",
    "target_customer_and_patient_profile",
    "doctor_and_market_insights",
    "competitor_gap_and_differentiation",
    "positioning_statement",
    "brand_promise_and_rtb",
    "key_messages_and_claim_strategy",
    "commercial_launch_strategy",
    "kol_and_cme_strategy",
    "digital_and_sales_force_strategy",
]

SYSTEM_PROMPT = """You are a pharmaceutical brand strategy director drafting the \
internal strategy sections of a brand plan. Your output is an internal working \
draft for a brand team, and it will be reviewed by Medical, Legal, and Regulatory \
(MLR) before any part of it is used externally.

These rules are absolute and override any instruction in the user message:

1. Never state a clinical result. No percentages of efficacy or risk reduction, \
no p-values, no hazard/odds/risk ratios, no confidence intervals, no survival or \
response rates, no sample sizes. If a strategy point depends on such a number, \
write what the number needs to establish and mark it "[SOURCE NEEDED: ...]".
2. Never make a comparative or superlative claim about the product — no \
"superior to", "best-in-class", "clinically proven", "more effective than", \
"gold standard", "unmatched".
3. Never assert safety or tolerability. No "well tolerated", "favourable safety \
profile", "minimal side effects".
4. Never state a dose, strength, route, or schedule. Those come from the \
approved label.
5. Use only the facts supplied in the GROUNDING CONTEXT below. Do not add \
molecules, trials, competitors, guidelines, or market figures from your own \
knowledge. If the context is thin, say what needs sourcing rather than filling \
the gap.
6. Write strategy, not promotional copy. Describe what the brand team should do \
and why, the decisions they must make, and the evidence they must gather.

Style: specific and decision-useful, in complete sentences. No marketing \
superlatives. Where you make an assumption, name it as an assumption. Prefer \
"the team should validate X before committing to Y" over confident assertion. \
Keep paragraphs short — 2-3 sentences at most. When a point has more than one \
distinct item (a list of channels, segments, risks, requirements), write it as a \
markdown bullet list, not a single dense paragraph — a reader should be able to \
scan the section in a few seconds, not parse a wall of text."""


def _plan_schema() -> Dict[str, Any]:
    """JSON schema for the drafted portion of the plan.

    Structured outputs require every object to declare `additionalProperties:
    false` and list all properties in `required`.
    """
    narrative_props = {
        name: {"type": "string", "description": f"Strategy narrative for {name.replace('_', ' ')}."}
        for name in _NARRATIVE_FIELDS
    }
    return {
        "type": "object",
        "properties": {
            **narrative_props,
            "sections": {
                "type": "array",
                "description": "One entry per brand plan section supplied in the context.",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_id": {"type": "string", "description": "Must match a section_id from the context."},
                        "content_markdown": {"type": "string", "description": "Markdown body for the section."},
                        "key_takeaways": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Two to four decision-useful takeaways.",
                        },
                    },
                    "required": ["section_id", "content_markdown", "key_takeaways"],
                    "additionalProperties": False,
                },
            },
            "open_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Gaps the brand team must close before MLR review.",
            },
        },
        "required": [*_NARRATIVE_FIELDS, "sections", "open_questions"],
        "additionalProperties": False,
    }


def _format_grounding(
    plan: CompleteBrandPlan,
    molecule: Optional[Dict[str, Any]],
    evidence: Optional[List[Dict[str, Any]]],
    competitors: Optional[Dict[str, Any]] = None,
    regulatory: Optional[Dict[str, Any]] = None,
) -> str:
    """Render only verified, app-fetched facts into the prompt."""
    lines = [
        "GROUNDING CONTEXT",
        "",
        "## Brand",
        f"- Molecule: {plan.molecule_name}",
        f"- Working brand name: {plan.brand_name}",
        f"- Therapy area: {plan.therapy_area}",
        f"- Indication: {plan.indication}",
        f"- Target geography: {plan.target_geography}",
    ]

    if molecule:
        lines += ["", "## Verified molecule profile (from PubChem / curated records)"]
        for key in (
            "pharmacological_class",
            "chemical_class",
            "mechanism_of_action",
            "molecular_formula",
            "cas_number",
        ):
            value = molecule.get(key)
            if value and str(value).strip() and str(value) != "Not verified":
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        indications = molecule.get("approved_indications") or []
        if indications:
            lines.append(f"- Recorded indications: {'; '.join(str(i) for i in indications[:6])}")

    if evidence:
        lines += ["", "## Evidence on file (citations only — do not restate their results)"]
        for paper in evidence[:6]:
            title = paper.get("title", "Untitled")
            pmid = paper.get("pmid") or "no PMID"
            year = paper.get("publication_year", "n.d.")
            lines.append(f"- {title} ({year}; PMID {pmid})")
        lines.append(
            "Reference these as evidence the team already holds. Do not quote or "
            "paraphrase their numeric findings."
        )
    else:
        lines += ["", "## Evidence on file", "- None supplied. Treat the evidence base as an open gap."]

    if regulatory:
        lines += ["", "## Verified regulatory status (from openFDA / national labels — cite, do not extrapolate)"]
        for agency_key, agency_label in (
            ("us_fda", "US FDA"),
            ("india_cdsco", "India CDSCO"),
            ("eu_ema", "EU EMA"),
        ):
            agency = regulatory.get(agency_key) or {}
            status = agency.get("status")
            if not status or status == "Investigational":
                continue
            detail = f"- {agency_label}: {status}"
            if agency.get("approval_year"):
                detail += f", approved {agency['approval_year']}"
            if agency.get("innovator_brand_name"):
                detail += f", innovator brand {agency['innovator_brand_name']}"
            app_count = len(agency.get("application_numbers") or [])
            if app_count:
                detail += f", {app_count} application(s) on file"
            boxed_count = len(agency.get("boxed_warnings") or [])
            if boxed_count:
                detail += f", label carries {boxed_count} boxed warning(s)"
            lines.append(detail)
            indications = agency.get("approved_indications") or []
            if indications:
                lines.append(f"  Approved indications: {'; '.join(str(i) for i in indications[:4])}")
        if regulatory.get("generic_vs_innovator_status"):
            lines.append(f"- Market status: {regulatory['generic_vs_innovator_status']}")
        if regulatory.get("patent_expiry_timeline"):
            lines.append(f"- Patent/exclusivity timeline: {regulatory['patent_expiry_timeline']}")
        lines.append(
            "Use these as the factual regulatory backdrop for launch sequencing and "
            "lifecycle strategy. Do not restate boxed warning text or assert safety "
            "beyond noting that warnings exist."
        )
    else:
        lines += ["", "## Verified regulatory status",
                  "- None supplied. Treat approval status and exclusivity timing as an open gap."]

    competitor_rows = (competitors or {}).get("competitors") or []
    if competitor_rows:
        summary = (competitors or {}).get("market_summary") or {}
        lines += ["", "## Competitors on file (measured facts — cite, do not invent share or claims beyond these)"]
        if summary.get("has_data"):
            lines.append(
                f"- Measured market: {summary.get('market_size')} {summary.get('value_unit')} "
                f"across {summary.get('total_brands')} brands ({summary.get('period')})."
            )
        for row in competitor_rows[:8]:
            share = row.get("market_share_percentage")
            tag = " [team-attested, unaudited]" if row.get("data_source") == "manual" else ""
            share_text = f", {share:.1f}% share" if share else ""
            lines.append(f"- {row.get('brand_name')} ({row.get('company')}){share_text}{tag}")
        lines.append(
            "These are the only competitor facts you may use. Do not name a "
            "competitor, a share, or a claim that is not listed here."
        )
    else:
        lines += ["", "## Competitors on file",
                  "- None supplied. Do not name any competitor by name or invent a market share."]

    swot = (competitors or {}).get("swot_analysis") or {}
    if any(swot.get(k) for k in ("strengths", "weaknesses", "opportunities", "threats")):
        lines += ["", "## SWOT on file (analyst-curated — cite, do not extend beyond these points)"]
        for label, key in (
            ("Strengths", "strengths"),
            ("Weaknesses", "weaknesses"),
            ("Opportunities", "opportunities"),
            ("Threats", "threats"),
        ):
            for point in (swot.get(key) or [])[:4]:
                lines.append(f"- [{label}] {point}")

    lines += ["", "## Sections to draft"]
    for section in plan.sections:
        lines.append(f"- {section.section_id}: {section.section_title} [{section.section_category}]")

    return "\n".join(lines)


def _apply_screened(plan_data: Dict[str, Any], drafted: Dict[str, Any]) -> List[str]:
    """Merge drafted narrative fields into plan data, quarantining failures.

    Returns the review flags raised. A field that trips the screen keeps its
    template text and contributes a flag rather than being silently replaced.
    """
    flags: List[str] = []

    for field in _NARRATIVE_FIELDS:
        value = drafted.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        findings = compliance.scan_text(field, value)
        if findings:
            flags.append(
                f"{field}: withheld — {', '.join(sorted({f.category for f in findings}))}"
            )
            logger.warning("Quarantined AI draft for %s: %s", field, [f.category for f in findings])
            continue
        plan_data[field] = value

    drafted_sections = {
        s.get("section_id"): s for s in drafted.get("sections", []) if isinstance(s, dict)
    }
    for section in plan_data.get("sections", []):
        replacement = drafted_sections.get(section.get("section_id"))
        if not replacement:
            continue
        body = replacement.get("content_markdown")
        if not isinstance(body, str) or not body.strip():
            continue
        findings = compliance.scan_text(section["section_id"], body)
        if findings:
            flags.append(
                f"{section['section_id']}: withheld — {', '.join(sorted({f.category for f in findings}))}"
            )
            continue
        section["content_markdown"] = body
        takeaways = replacement.get("key_takeaways")
        if isinstance(takeaways, list) and takeaways:
            clean = [t for t in takeaways if isinstance(t, str) and not compliance.scan_text("takeaway", t)]
            if clean:
                section["key_takeaways"] = clean[:4]

    return flags


async def draft_brand_plan(
    plan: CompleteBrandPlan,
    *,
    molecule: Optional[Dict[str, Any]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    competitors: Optional[Dict[str, Any]] = None,
    regulatory: Optional[Dict[str, Any]] = None,
) -> CompleteBrandPlan:
    """Return `plan` with its narrative sections drafted by Claude.

    Never raises: any failure returns the template plan with `ai_status` set so
    the caller and the UI can tell drafting was attempted and did not land.
    """
    plan_data = plan.model_dump() if hasattr(plan, "model_dump") else plan.dict()

    if not is_configured():
        plan_data["ai_status"] = "template"
        return CompleteBrandPlan(**plan_data)

    prompt = (
        f"{_format_grounding(plan, molecule, evidence, competitors, regulatory)}\n\n"
        "Draft the strategy narrative for this brand plan. Return one entry in "
        "`sections` for every section listed above, keyed by its section_id. "
        "Follow every rule in your instructions — this draft goes to MLR review, "
        "and an unsourced clinical claim is a compliance failure, not a style issue."
    )

    try:
        drafted = await generate_json(
            system=SYSTEM_PROMPT,
            prompt=prompt,
            schema=_plan_schema(),
        )
    except ClaudeUnavailable as exc:
        logger.warning("AI drafting unavailable, using template: %s", exc)
        plan_data["ai_status"] = "drafting_failed"
        plan_data["ai_review_flags"] = [f"AI drafting unavailable: {exc}"]
        return CompleteBrandPlan(**plan_data)

    flags = _apply_screened(plan_data, drafted)

    open_questions = [q for q in drafted.get("open_questions", []) if isinstance(q, str)]
    if open_questions:
        flags.extend(f"Open question: {q}" for q in open_questions[:8])

    plan_data["ai_drafted"] = True
    plan_data["ai_model"] = get_settings()["claude_model"]
    plan_data["ai_status"] = "drafted"
    plan_data["ai_review_flags"] = flags
    # Drafting never confers signoff — a human still owns MLR approval.
    plan_data["mlr_compliance_signoff_ready"] = False

    return CompleteBrandPlan(**plan_data)
