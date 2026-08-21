"""Normalisation and splitting of molecule names, including fixed-dose combinations.

PubChem, and most structure databases, resolve single compounds only: a lookup
for "Empagliflozin + Metformin" returns 404 because no such compound exists.
Brand planning is full of fixed-dose combinations, so every downstream module
needs the component list as well as the combination label the user typed.
"""
import re
from typing import List, NamedTuple

# Separators a brand manager might type between components of an FDC.
_SEPARATORS = re.compile(
    r"\s*(?:\+|/|,|&|\bplus\b|\band\b|\bwith\b|\bcombination\s+of\b)\s*",
    re.IGNORECASE,
)

# Dosage/form noise that clings to pasted names and breaks exact-match lookups.
_NOISE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|%)\b"
    r"|\b(?:tablet|tablets|capsule|capsules|injection|film[- ]coated|"
    r"extended[- ]release|sustained[- ]release|er|xr|sr|ir|oral|solution|suspension|"
    r"hydrochloride|hcl|sodium|potassium|calcium|sulfate|sulphate|phosphate|"
    r"maleate|tartrate|besylate|mesylate|fumarate|succinate|dihydrate|monohydrate)\b",
    re.IGNORECASE,
)


class ResolvedMolecule(NamedTuple):
    """The user's input, normalised, with its components broken out."""

    raw: str
    display_name: str
    components: List[str]

    @property
    def is_combination(self) -> bool:
        return len(self.components) > 1

    @property
    def primary(self) -> str:
        """The component to use where only one name is accepted."""
        return self.components[0] if self.components else self.display_name


def _clean(fragment: str, *, strip_salts: bool) -> str:
    text = fragment.strip()
    if strip_salts:
        text = _NOISE.sub(" ", text)
    text = re.sub(r"[^\w\s\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def resolve(name: str) -> ResolvedMolecule:
    """Split a possibly-combination molecule name into its components.

    Salt and dosage-form words are stripped from the *components* used for
    lookups, but the display name keeps what the user typed so the UI and the
    exported documents still say "Empagliflozin + Metformin".
    """
    raw = (name or "").strip()
    if not raw:
        return ResolvedMolecule(raw=raw, display_name="", components=[])

    parts = [p for p in _SEPARATORS.split(raw) if p and p.strip()]

    components: List[str] = []
    for part in parts:
        cleaned = _clean(part, strip_salts=True)
        # Keep the salt form if stripping emptied the fragment entirely.
        if not cleaned:
            cleaned = _clean(part, strip_salts=False)
        if cleaned and cleaned.lower() not in {c.lower() for c in components}:
            components.append(cleaned.title())

    if not components:
        fallback = _clean(raw, strip_salts=False)
        components = [fallback.title()] if fallback else []

    display = " + ".join(components) if len(components) > 1 else (components[0] if components else raw)
    return ResolvedMolecule(raw=raw, display_name=display, components=components)


def search_terms(resolved: ResolvedMolecule) -> List[str]:
    """Query fragments for literature and trial searches.

    A combination is searched as an AND of its components, which is how the
    trials and papers for an FDC are actually indexed — searching the joined
    string returns nothing.
    """
    return list(resolved.components) or [resolved.display_name]
