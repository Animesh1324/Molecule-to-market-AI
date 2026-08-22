"""Draft a single-page allopathic detail-aid brief and a matching image-generation prompt.

Follows the standard pharma visual-aid anatomy: main indication, brand/pack
shot, punchline, a short clinical message, one dominant visual, composition,
scientific support, and a call-to-prescribe closer — built for the "5-second
rule" (a doctor grasps what/why-better/who within 5 seconds) and a 70/30
visual-to-text ratio.

Only the short narrative fields (punchline, call-to-prescribe, message points)
are Claude-drafted, from the same grounded, verified facts as the rest of the
brand plan, and every drafted field is screened by `compliance` before use —
this brief carries the same "internal draft, not MLR-cleared" status as every
other commercial asset in the app. The image-generation prompt itself is built
deterministically from the screened content, never model-generated, so a
prompt-injection risk in the model's own output can't leak into it.
"""
import logging
from typing import Any, Dict, List, Optional

from ..models.assets import VisualAidBrief
from . import compliance
from .claude_client import ClaudeUnavailable, generate_json, is_configured

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are drafting the short copy for a single-page pharmaceutical \
field-detailing visual aid. Your output is an internal working draft for MLR \
(Medical/Legal/Regulatory) review — not approved promotional copy.

Absolute rules:
1. Never state a clinical result — no percentages, p-values, hazard/odds/risk ratios, \
confidence intervals, or response rates.
2. Never make a comparative or superlative claim ("superior to", "best-in-class", \
"clinically proven", "gold standard").
3. Never assert safety or tolerability ("well tolerated", "favourable safety profile").
4. Never state a dose, strength, or route — those come from the approved label, not you.
5. Use only the facts in the GROUNDING CONTEXT. If it is thin, write a message that \
names the gap for the brand team to source, not a claim you invented.
6. The punchline must be short (under 8 words), benefit-oriented, and NOT a specific \
claim — a positioning line, not a statistic.
7. The call-to-prescribe is a directive action line, not a claim.

Style: the tone of a strategy brief, not an advertisement — decision-useful for a \
brand team writing the real thing, not usable as final promotional copy."""


def _grounding_text(
    molecule: Optional[Dict[str, Any]],
    regulatory: Optional[Dict[str, Any]],
    evidence: Optional[List[Dict[str, Any]]],
    indication: str,
    brand_name: str,
) -> str:
    lines = ["GROUNDING CONTEXT", "", f"Brand: {brand_name}", f"Indication: {indication}"]

    if molecule:
        lines.append("")
        lines.append("## Verified molecule profile")
        for key in ("pharmacological_class", "mechanism_of_action"):
            value = molecule.get(key)
            if value and str(value) != "Not verified":
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    us_fda = (regulatory or {}).get("us_fda") or {}
    if us_fda.get("status") and us_fda["status"] != "Investigational":
        lines.append("")
        lines.append("## Verified regulatory status")
        lines.append(f"- US FDA: {us_fda['status']}")
        indications = us_fda.get("approved_indications") or []
        if indications:
            lines.append(f"- Approved indications: {'; '.join(str(i) for i in indications[:3])}")

    if evidence:
        lines.append("")
        lines.append("## Evidence on file (citations only)")
        for paper in evidence[:4]:
            lines.append(f"- {paper.get('title', 'Untitled')} (PMID {paper.get('pmid') or 'n/a'})")

    return "\n".join(lines)


def _schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "punchline": {"type": "string"},
            "clinical_message_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-4 short strategy-level message points, not finished claims.",
            },
            "hero_visual_concept": {"type": "string"},
            "call_to_prescribe": {"type": "string"},
        },
        "required": ["punchline", "clinical_message_points", "hero_visual_concept", "call_to_prescribe"],
        "additionalProperties": False,
    }


def _composition_text(molecule_name: str, regulatory: Optional[Dict[str, Any]]) -> str:
    us_fda = (regulatory or {}).get("us_fda") or {}
    dosage = us_fda.get("dosage_and_administration_summary")
    lines = [f"Generic name: {molecule_name}"]
    lines.append(
        f"Dosage & administration: {dosage}" if dosage
        else "Dosage & administration: [SOURCE NEEDED — confirm strength and dosage form from the approved local label]"
    )
    return " | ".join(lines)


def _scientific_support(evidence: Optional[List[Dict[str, Any]]], regulatory: Optional[Dict[str, Any]]) -> List[str]:
    support: List[str] = []
    for paper in (evidence or [])[:4]:
        pmid = paper.get("pmid")
        title = paper.get("title", "Untitled")
        support.append(f"{title}{f' (PMID {pmid})' if pmid else ''}")
    us_fda = (regulatory or {}).get("us_fda") or {}
    for app_no in (us_fda.get("application_numbers") or [])[:1]:
        support.append(f"US FDA application {app_no} (approved label)")
    if not support:
        support.append("[SOURCE NEEDED — no evidence or regulatory citation on file yet]")
    return support


def _image_prompt(brief_fields: Dict[str, Any], molecule_name: str, brand_name: str, indication: str) -> str:
    bullets = "\n".join(f"  - {p}" for p in brief_fields["clinical_message_points"])
    citations = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(brief_fields["scientific_support"]))
    return f"""Create a single-page pharmaceutical field-detailing visual aid (detail aid) image.

LAYOUT RULE: 70% visual imagery, 30% text. A doctor must grasp what the product is, \
why it matters, and who it is for within 5 seconds — keep it minimalist, never dense \
tables or paragraphs.

BRAND: {brand_name} ({molecule_name})
MAIN INDICATION (large, top of page): {indication}
PUNCHLINE (short, memorable headline): "{brief_fields['punchline']}"
HERO VISUAL (dominant element, ~70% of the page): {brief_fields['hero_visual_concept']} — \
clean modern clinical color palette (blues/whites/teals), professional pharma-brand \
aesthetic, no photographs of real medicine packaging — use a generic silhouette pack \
mockup instead.
CLINICAL MESSAGE (3-4 short callouts near the visual, small text):
{bullets}
COMPOSITION (small print, mandatory for an allopathic product): {brief_fields['composition']}
SCIENTIFIC SUPPORT (numbered footnote strip at the bottom):
{citations}
CALL TO PRESCRIBE (bottom band, clear directive): "{brief_fields['call_to_prescribe']}"

STYLE: single page, print-ready, minimalist pharma branding. Do not render any specific \
efficacy percentage, p-value, hazard ratio, or comparative superiority claim beyond what \
is written above — this is an internal MLR-review draft, not approved promotional copy."""


async def draft_visual_aid_brief(
    molecule_name: str,
    brand_name: str,
    indication: str,
    molecule: Optional[Dict[str, Any]] = None,
    regulatory: Optional[Dict[str, Any]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
) -> VisualAidBrief:
    composition = _composition_text(molecule_name, regulatory)
    scientific_support = _scientific_support(evidence, regulatory)

    fields = {
        "punchline": "[SOURCE NEEDED — draft a benefit-led punchline once positioning is finalized]",
        "clinical_message_points": [
            "[SOURCE NEEDED — add a message once evidence/regulatory grounding is available]",
        ],
        "hero_visual_concept": "[SOURCE NEEDED — concept pending brand positioning]",
        "call_to_prescribe": f"Discuss {brand_name} with your MLR-cleared team before field use.",
    }
    ai_drafted = False
    review_flags: List[str] = []

    if is_configured():
        prompt = (
            f"{_grounding_text(molecule, regulatory, evidence, indication, brand_name)}\n\n"
            "Draft the punchline, clinical message points, hero visual concept, and "
            "call-to-prescribe for this visual aid."
        )
        try:
            drafted = await generate_json(system=SYSTEM_PROMPT, prompt=prompt, schema=_schema())
            for key in ("punchline", "hero_visual_concept", "call_to_prescribe"):
                value = drafted.get(key)
                if isinstance(value, str) and value.strip():
                    findings = compliance.scan_text(key, value)
                    if findings:
                        review_flags.append(f"{key}: withheld — {', '.join(sorted({f.category for f in findings}))}")
                        continue
                    fields[key] = value
            points = drafted.get("clinical_message_points")
            if isinstance(points, list):
                clean_points = [p for p in points if isinstance(p, str) and not compliance.scan_text("clinical_message_points", p)]
                if clean_points:
                    fields["clinical_message_points"] = clean_points[:4]
            ai_drafted = True
        except ClaudeUnavailable as exc:
            logger.warning("AI visual-aid drafting unavailable, using template: %s", exc)
            review_flags.append(f"AI drafting unavailable: {exc}")

    fields["composition"] = composition
    fields["scientific_support"] = scientific_support

    return VisualAidBrief(
        molecule_name=molecule_name,
        brand_name=brand_name,
        main_indication=indication,
        brand_and_pack_shot=f"{brand_name} — pack mockup pending final formulation and label approval",
        punchline=fields["punchline"],
        clinical_message_points=fields["clinical_message_points"],
        hero_visual_concept=fields["hero_visual_concept"],
        composition=composition,
        scientific_support=scientific_support,
        call_to_prescribe=fields["call_to_prescribe"],
        image_generation_prompt=_image_prompt(fields, molecule_name, brand_name, indication),
        ai_drafted=ai_drafted,
        ai_review_flags=review_flags,
    )
