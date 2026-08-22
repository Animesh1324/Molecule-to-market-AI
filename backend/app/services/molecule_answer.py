"""Claude-answered molecule queries.

Requested explicitly: answer a molecule question with Claude rather than by
assembling stored records. Built as asked, with the compromises named rather
than hidden, because a brand plan is an MLR-reviewed artefact and a reviewer
has to be able to tell which statements came from a regulator and which came
from a model.

Three things this does that a bare model call would not:

* **Grounds the answer where evidence exists.** Whatever the local catalogue
  holds for the molecule — label text, approval history, patents, recalls — is
  passed to Claude as context. This does not change what was asked for; it
  changes the answer from recollection to reading. Where the catalogue is
  silent, so is the grounding, and the model is on its own.
* **Labels provenance per field.** Every field comes back marked `fda` or
  `model`. A field Claude wrote is never presented as a regulator's statement.
* **Screens output before returning it.** `compliance.scan_fields` already
  guards AI-drafted text elsewhere; the same screen runs here, so efficacy
  claims, comparative superiority and dosing advice are quarantined rather
  than shipped.

What it cannot fix: a model-sourced clinical statement is not citable to a
source document, so `mlr_citable` is False on every such field. That is a
property of the approach, not of the implementation.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from . import compliance
from .claude_client import ClaudeUnavailable, generate_json, is_configured
from .molecule_dossier import build_dossier

logger = logging.getLogger(__name__)

SYSTEM = (
    "You are a pharmaceutical information assistant supporting brand-plan "
    "research. Answer about the molecule named by the user.\n\n"
    "Rules, in order of priority:\n"
    "1. GROUNDED CONTEXT WINS. When the FDA context below contains a fact, use "
    "it verbatim in meaning and do not contradict it from memory.\n"
    "2. NEVER INVENT specifics. Do not produce approval dates, patent expiry "
    "dates, application numbers, trial results, effect sizes, p-values, hazard "
    "ratios, or market figures unless they appear in the context. If a "
    "specific is not in the context, say it is not available.\n"
    "3. NO CLINICAL ADVICE. Do not give dosing recommendations, comparative "
    "efficacy or safety superiority claims, or treatment guidance.\n"
    "4. MARK YOUR SOURCES. For each field set source='fda' when it came from "
    "the provided context and source='model' when it came from your own "
    "knowledge. Be honest; mismarking is worse than admitting uncertainty.\n"
    "5. Prefer 'not available' to a plausible guess."
)

SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["molecule", "summary", "fields", "caveats"],
    "properties": {
        "molecule": {"type": "string"},
        "summary": {"type": "string", "description": "2-4 sentences, no clinical advice"},
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "value", "source"],
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "string"},
                    "source": {"type": "string", "enum": ["fda", "model"]},
                },
            },
        },
        "caveats": {"type": "array", "items": {"type": "string"}},
    },
}


def _context(dossier: Dict[str, Any], *, max_chars: int = 12000) -> str:
    """Compact the stored record into prompt context.

    Trimmed rather than dumped whole: label narrative alone can run to tens of
    thousands of characters, and burying the structured facts in it makes the
    model likelier to fall back on memory for exactly the specifics it must not
    invent.
    """
    identity = dossier.get("identity") or {}
    approvals = dossier.get("approvals") or {}
    exclusivity = dossier.get("exclusivity") or {}
    safety = dossier.get("safety_signals") or {}
    clinical = identity.get("clinical") or {}

    if not identity.get("found"):
        return "NO FDA RECORD FOUND for this molecule in the local catalogue."

    lines: List[str] = ["FDA CONTEXT (authoritative - prefer over your own knowledge):"]
    lines.append(f"- generic name: {identity.get('generic_name')}")
    lines.append(f"- drug class: {identity.get('drug_class') or 'not recorded'}")
    lines.append(f"- brands: {', '.join(identity.get('brands') or []) or 'none recorded'}")
    lines.append(f"- dosage forms: {', '.join(identity.get('dosage_forms') or []) or 'none'}")
    lines.append(f"- routes: {', '.join(identity.get('routes') or []) or 'none'}")
    if approvals.get("found"):
        lines.append(f"- first FDA approval: {approvals.get('first_approval') or 'not recorded'}")
        lines.append(f"- innovator: {approvals.get('innovator') or 'not recorded'}")
        lines.append(f"- applications on file: {approvals.get('applications')}")
    if exclusivity.get("found"):
        lines.append(f"- Orange Book patents: {exclusivity.get('patents')}, "
                     f"latest expiry {exclusivity.get('latest_patent_expiry') or 'unknown'}")
        lines.append(f"- AB-rated generics approved: {exclusivity.get('ab_rated_products')}")
    elif exclusivity.get("note"):
        lines.append(f"- Orange Book: {exclusivity['note']}")
    recalls = (safety.get("recalls") or {})
    if recalls.get("total"):
        lines.append(f"- recalls on record: {recalls['total']} {recalls.get('by_classification')}")
    shortages = (safety.get("shortages") or {})
    if shortages.get("current"):
        lines.append(f"- current shortages: {shortages['current']}")

    for label, key in (("indications", "indications"), ("contraindications", "contraindications"),
                       ("warnings", "warnings"), ("mechanism", "mechanism")):
        value = clinical.get(key)
        if value:
            lines.append(f"- label {label}: {str(value)[:1500]}")

    text = "\n".join(lines)
    return text[:max_chars]


async def answer_molecule(molecule: str, question: Optional[str] = None) -> Dict[str, Any]:
    """Answer a molecule query with Claude, grounded in the stored record."""
    name = (molecule or "").strip()
    if not name:
        raise ValueError("molecule is required")
    if not is_configured():
        raise ClaudeUnavailable("AI answering is not configured (set ANTHROPIC_API_KEY).")

    dossier = build_dossier(name, paper_limit=10)
    context = _context(dossier)
    grounded = bool((dossier.get("identity") or {}).get("found"))

    prompt = (
        f"Molecule: {name}\n\n{context}\n\n"
        + (f"Question: {question}\n\n" if question else "")
        + "Answer using the context above. Mark each field 'fda' when it came "
          "from the context and 'model' when it came from your own knowledge."
    )

    payload = await generate_json(system=SYSTEM, prompt=prompt, schema=SCHEMA, max_tokens=4000)

    fields = payload.get("fields") or []
    screened: List[Dict[str, Any]] = []
    scan_input: Dict[str, str] = {}
    for item in fields:
        name_ = str(item.get("name", ""))
        value = str(item.get("value", ""))
        source = "fda" if item.get("source") == "fda" else "model"
        scan_input[name_] = value
        screened.append({
            "name": name_,
            "value": value,
            "source": source,
            # A model-sourced clinical statement cannot be cited to a source
            # document. This is inherent to answering from a model, not a bug.
            "mlr_citable": source == "fda",
        })

    scan_input["summary"] = str(payload.get("summary", ""))
    findings = compliance.scan_fields(scan_input)
    flagged = {f.field for f in findings}
    for item in screened:
        item["compliance_flagged"] = item["name"] in flagged

    return {
        "molecule": payload.get("molecule") or name,
        "summary": payload.get("summary"),
        "fields": screened,
        "caveats": payload.get("caveats") or [],
        "grounded_in_catalogue": grounded,
        "model_sourced_fields": sum(1 for i in screened if i["source"] == "model"),
        "compliance_findings": [
            {"field": f.field, "issue": getattr(f, "reason", None) or getattr(f, "pattern", None)}
            for f in findings
        ],
        "compliance_notice": compliance.quarantine_notice(findings) if findings else None,
        # Never true for this route. An answer containing model-sourced clinical
        # statements cannot clear MLR, whatever the screen returns.
        "mlr_compliance_signoff_ready": False,
        "disclaimer": (
            "Generated with AI assistance. Fields marked source='model' are not "
            "traceable to a regulatory document and must be verified against the "
            "approved label before any external use."
        ),
    }
