"""Screening for clinical claims that a language model must never invent.

The brand plan is an internal strategy document, but its text flows into the
DOCX/PPTX exports and from there into MLR review. A drafting model that
produces a plausible-sounding "38% reduction in CV death" for the wrong
molecule creates a fabricated efficacy claim under the user's name.

The rule this module enforces: quantitative clinical results and superiority
language come from the evidence and regulatory modules, which are sourced.
Generated strategy text may describe *plans*, never *results*. Anything here
that trips a pattern is quarantined rather than silently shipped.
"""
import re
from typing import Dict, List, NamedTuple


class ClaimFinding(NamedTuple):
    field: str
    category: str
    excerpt: str


# Each pattern targets a shape of claim that must be traceable to a citation.
# They are deliberately broad: a false positive costs a review flag, while a
# false negative puts an unsourced clinical claim into an exported deck.
_CLAIM_PATTERNS: List[tuple] = [
    (
        "quantified_clinical_effect",
        re.compile(
            r"\b\d{1,3}(?:\.\d+)?\s*%\s*(?:relative\s+|absolute\s+)?"
            r"(?:risk\s+)?(?:reduction|reductions|increase|improvement|decrease|lower|higher|"
            r"response|remission|survival|efficacy|reduction\s+in)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "p_value",
        re.compile(r"\bp\s*[<>=]\s*0?\.\d+", re.IGNORECASE),
    ),
    (
        "hazard_or_odds_ratio",
        re.compile(r"\b(?:hazard\s+ratio|odds\s+ratio|risk\s+ratio|HR|OR|RR)\s*[:=]?\s*0?\.\d+", re.IGNORECASE),
    ),
    (
        "confidence_interval",
        re.compile(r"\b\d{1,3}\s*%\s*CI\b|\bconfidence\s+interval\s*[:,]?\s*\d", re.IGNORECASE),
    ),
    (
        "superiority_language",
        re.compile(
            r"\b(?:superior\s+to|proven\s+superior|best[- ]in[- ]class|first[- ]in[- ]class|"
            r"more\s+effective\s+than|outperforms|clinically\s+proven|demonstrated\s+superiority|"
            r"gold\s+standard|unmatched|only\s+(?:drug|therapy|agent)\s+(?:that|to))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "safety_assurance",
        re.compile(
            r"\b(?:well[- ]tolerated|excellent\s+safety|no\s+(?:significant\s+)?side\s+effects|"
            r"safe\s+for\s+all|minimal\s+adverse|favou?rable\s+safety\s+profile)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "dosing_instruction",
        re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|IU)\b\s*(?:once|twice|daily|bd|od|per\s+day|q\.?d)", re.IGNORECASE),
    ),
]


def scan_text(field: str, text: str) -> List[ClaimFinding]:
    """Return every unsourced-claim pattern found in one field of generated text."""
    if not text:
        return []

    findings: List[ClaimFinding] = []
    for category, pattern in _CLAIM_PATTERNS:
        for match in pattern.finditer(text):
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            findings.append(
                ClaimFinding(
                    field=field,
                    category=category,
                    excerpt=text[start:end].strip().replace("\n", " "),
                )
            )
    return findings


def scan_fields(fields: Dict[str, str]) -> List[ClaimFinding]:
    """Scan a mapping of field name to generated text."""
    findings: List[ClaimFinding] = []
    for name, value in fields.items():
        if isinstance(value, str):
            findings.extend(scan_text(name, value))
    return findings


def quarantine_notice(findings: List[ClaimFinding]) -> str:
    """Human-readable replacement text for a field that failed screening."""
    categories = sorted({f.category.replace("_", " ") for f in findings})
    return (
        "AI draft withheld — the generated text contained "
        f"{', '.join(categories)} that is not traceable to a verified source. "
        "Clinical results and comparative claims must come from the Evidence and "
        "Regulatory modules, not from drafting. Rewrite this section manually."
    )
