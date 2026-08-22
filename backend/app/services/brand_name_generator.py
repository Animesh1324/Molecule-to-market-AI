"""Generate candidate brand names and screen them against real marketed brands.

The naming rules a brand team works to: short enough to say and recall on a
call (roughly 5-9 characters), rooted in the molecule stem or the therapeutic
function so it carries meaning, and not colliding with anything already on the
market — regulators reject names that look or sound like an existing brand
because that is how dispensing errors happen.

Collision screening runs against the FDA Orange Book's ~49k real trade names
plus a phonetic key, so a candidate is only offered if nothing marketed shares
its spelling or its sound. Final clearance is still a formal trademark search:
every candidate ships with the search links to run it.
"""
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import quote_plus

from . import orange_book
from .claude_client import ClaudeUnavailable, generate_json, is_configured as ai_naming_configured
from .molecule_resolver import resolve as resolve_molecule

logger = logging.getLogger(__name__)

# Meaning-carrying roots, grouped by what the brand should signal.
FUNCTIONAL_ROOTS: Dict[str, List[str]] = {
    "cardio": ["Cardi", "Cor", "Vasco", "Pulse", "Rythm"],
    "renal": ["Reno", "Nefro", "Filtra"],
    "metabolic": ["Gluco", "Metra", "Lipo", "Slenda"],
    "protection": ["Shield", "Guarda", "Armo", "Fenda", "Salva"],
    "vitality": ["Viva", "Vita", "Zeno", "Nova", "Elan"],
    "control": ["Stabil", "Equa", "Steda", "Regu", "Norma"],
    "clarity": ["Clara", "Lumo", "Sereno", "Aura"],
    "strength": ["Forta", "Valo", "Robu", "Maxa"],
    "respiratory": ["Pulmo", "Aera", "Bronca", "Respi"],
    "neuro": ["Neura", "Cogni", "Menta", "Seren"],
    "oncology": ["Onco", "Remis", "Tumo", "Vanqa"],
    "infection": ["Steri", "Bacta", "Immu", "Puri"],
    "pain": ["Alga", "Lenu", "Solace", "Calma"],
    "gastro": ["Gastro", "Digi", "Enter"],
}

# Which root families fit a given therapy area.
THERAPY_ROOTS: List[tuple] = [
    (("cardio", "metabolic", "protection", "control", "vitality"),
     ("cardio", "metabolic", "diabet", "heart", "renal", "nephro", "lipid", "obesity")),
    (("oncology", "vitality", "strength", "protection"),
     ("oncolog", "cancer", "tumor", "tumour", "carcinoma", "nsclc", "leukemia")),
    (("respiratory", "clarity", "vitality"),
     ("respirat", "pulmon", "asthma", "copd", "allerg")),
    (("neuro", "clarity", "control"),
     ("neuro", "cns", "psychiatr", "epilep", "migraine", "alzheim", "parkinson")),
    (("infection", "protection", "strength"),
     ("infect", "antibiot", "antivir", "antimicrob", "hiv", "hepatitis")),
    (("pain", "clarity", "vitality"),
     ("pain", "analges", "arthrit", "rheumat", "inflamm")),
    (("gastro", "control", "clarity"),
     ("gastro", "colitis", "crohn", "hepat", "digest")),
]

SUFFIXES = ["a", "va", "ia", "za", "ra", "el", "on", "ex", "is", "or", "yn", "us"]

# Regulators reject names implying a promise or an outcome.
BANNED_FRAGMENTS = {"cure", "safe", "best", "pure", "heal", "miracle", "perfect", "super"}

MIN_LEN, MAX_LEN = 5, 9


def _roots_for(therapy_area: str, indication: str) -> List[str]:
    text = f"{therapy_area} {indication}".lower()
    families: List[str] = []
    for family_names, keywords in THERAPY_ROOTS:
        if any(k in text for k in keywords):
            families.extend(family_names)
    if not families:
        families = ["protection", "vitality", "control", "clarity"]
    roots: List[str] = []
    for family in dict.fromkeys(families):
        roots.extend(FUNCTIONAL_ROOTS.get(family, []))
    return roots


def _molecule_stems(components: List[str]) -> List[str]:
    """Short openings taken from each molecule name."""
    stems: List[str] = []
    for component in components:
        clean = re.sub(r"[^A-Za-z]", "", component)
        if len(clean) >= 4:
            stems.append(clean[:4].title())
        if len(clean) >= 5:
            stems.append(clean[:5].title())
        # Class stems carry recognition: -gliflozin, -glutide, -mab, -prazole.
        for stem in ("gliflozin", "glutide", "gliptin", "prazole", "statin",
                     "sartan", "olol", "pril", "mab", "nib", "cycline", "cillin"):
            if clean.lower().endswith(stem):
                stems.append(clean[: -len(stem)][:4].title())
    return [s for s in dict.fromkeys(stems) if len(s) >= 3]


def _marketed_names() -> Set[str]:
    """Every trade name in the Orange Book, upper-cased, for collision checks."""
    index = orange_book.get_index()
    if not index.get("available"):
        return set()
    names: Set[str] = set()
    table = index["products_by_ingredient"]  # type: ignore[index]
    for rows in table.values():              # type: ignore[union-attr]
        for row in rows:
            name = (row.get("Trade_Name") or "").strip().upper()
            if name:
                names.add(name)
                # Store the first word too: "SYNJARDY XR" collides with "SYNJARDY".
                names.add(name.split()[0])
    return names


def _soundex(name: str) -> str:
    """Standard American Soundex, for near-sound collisions."""
    name = re.sub(r"[^A-Za-z]", "", name).upper()
    if not name:
        return ""
    codes = {**{c: "1" for c in "BFPV"}, **{c: "2" for c in "CGJKQSXZ"},
             **{c: "3" for c in "DT"}, "L": "4",
             **{c: "5" for c in "MN"}, "R": "6"}
    first, rest = name[0], name[1:]
    out: List[str] = []
    previous = codes.get(first, "")
    for char in rest:
        code = codes.get(char, "")
        if code and code != previous:
            out.append(code)
        if char not in "HW":
            previous = code
    return (first + "".join(out) + "000")[:4]


def _edit_distance(a: str, b: str, cap: int = 3) -> int:
    """Levenshtein distance, abandoned early once it exceeds `cap`."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ca != cb),
            ))
        if min(current) > cap:
            return cap + 1
        previous = current
    return previous[-1]


def _too_close(candidate: str, marketed_by_initial: Dict[str, List[str]]) -> bool:
    """Whether a candidate is confusably close to any marketed brand.

    Threshold scales with length: a 5-letter name one edit away from a marketed
    brand is a real dispensing risk, while a 9-letter name needs to be nearer
    still before it reads as the same word.
    """
    threshold = 1 if len(candidate) <= 6 else 2
    for initial in {candidate[:1]}:
        for name in marketed_by_initial.get(initial, ()):
            if abs(len(name) - len(candidate)) > threshold:
                continue
            if _edit_distance(candidate, name, cap=threshold) <= threshold:
                return True
    return False

def _screen_name(
    name: str,
    rationale: str,
    construction: str,
    marketed: Set[str],
    marketed_by_initial: Dict[str, List[str]],
) -> Optional[Dict[str, object]]:
    """Run one candidate string through the same real-collision checks `consider` applies.

    Standalone so AI-proposed names get exactly the same Orange Book screening
    as the algorithmic ones — an AI-suggested name is never trusted on its own
    judgment about collision risk.
    """
    clean = name.strip().title()
    upper = clean.upper()
    if not (MIN_LEN <= len(clean) <= MAX_LEN):
        return None
    if any(bad in clean.lower() for bad in BANNED_FRAGMENTS):
        return None
    if not re.fullmatch(r"[A-Za-z]+", clean):
        return None
    exact = upper in marketed
    phonetic = _too_close(upper, marketed_by_initial)
    return {
        "name": clean,
        "rationale": rationale,
        "construction": construction,
        "length": len(clean),
        "syllable_estimate": max(1, len(re.findall(r"[aeiouy]+", clean.lower()))),
        "soundex": _soundex(clean),
        "exact_collision_with_marketed_brand": exact,
        "phonetic_collision_with_marketed_brand": phonetic,
        "screening_status": (
            "Rejected — exact match to a marketed brand" if exact
            else "Caution — sounds like a marketed brand" if phonetic
            else "Clear of FDA Orange Book brands"
        ),
    }


def _attach_search_links(candidate: Dict[str, object]) -> None:
    name = str(candidate["name"])
    candidate["ip_india_search_url"] = "https://tmrsearch.ipindia.gov.in/tmrpublicsearch/"
    candidate["ip_india_search_term"] = name
    candidate["uspto_search_url"] = f"https://tmsearch.uspto.gov/search/search-results?q={quote_plus(name)}"
    candidate["wipo_search_url"] = f"https://branddb.wipo.int/en/quicksearch/brand/?q={quote_plus(name)}"
    candidate["verification_required"] = (
        "Screened only against FDA Orange Book brand names. Run the trademark "
        "searches above — IP India for Indian rights — before committing."
    )


_AI_NAMING_SYSTEM_PROMPT = """You are a pharmaceutical brand-naming specialist proposing \
candidate trade names for a new molecule, working to a brand team's stated naming brief.

Rules:
1. Every name must be an invented, coinable word — never a real dictionary word, \
never an existing drug name.
2. Never embed an unsubstantiated clinical claim in the name itself — no "cure", \
"safe", "best", "pure", "heal", "miracle", "perfect", or "super".
3. Satisfy the brand team's stated requirement — it is a brief, not a suggestion to \
weigh against your own preference.
4. Aim for 5-9 letters, one or two syllables, easy to say on a phone call.
5. Ground the rationale in the molecule's real pharmacological class or the stated \
therapy area — do not invent a clinical claim to justify a name."""


async def _ai_raw_candidates(
    molecule: str, therapy_area: str, indication: str, requirement: str, count: int,
) -> List[Dict[str, str]]:
    schema = {
        "type": "object",
        "properties": {
            "names": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["name", "rationale"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["names"],
        "additionalProperties": False,
    }
    prompt = (
        f"Molecule: {molecule}\nTherapy area: {therapy_area or 'unspecified'}\n"
        f"Indication: {indication or 'unspecified'}\nNaming requirement: {requirement}\n"
        f"Propose {count} candidate names satisfying the requirement."
    )
    try:
        result = await generate_json(system=_AI_NAMING_SYSTEM_PROMPT, prompt=prompt, schema=schema)
    except ClaudeUnavailable as exc:
        logger.warning("AI brand naming unavailable, using algorithmic candidates only: %s", exc)
        return []
    names = result.get("names")
    return names if isinstance(names, list) else []


async def generate_ai_candidates(
    molecule: str,
    therapy_area: str = "",
    indication: str = "",
    requirement: str = "",
    wanted: int = 10,
) -> List[Dict[str, object]]:
    """AI-proposed candidates honoring a free-text naming brief, screened the same as algorithmic ones.

    Falls back to the deterministic generator (ignoring the unmet requirement,
    since nothing can honor it without a model) when AI drafting has no key
    configured or the call fails — the caller always gets a usable list.
    """
    if not ai_naming_configured():
        return generate_candidates(molecule, therapy_area, indication, wanted)

    marketed = _marketed_names()
    marketed_by_initial: Dict[str, List[str]] = {}
    for name in marketed:
        marketed_by_initial.setdefault(name[:1], []).append(name)

    raw = await _ai_raw_candidates(molecule, therapy_area, indication, requirement, wanted * 2)
    if not raw:
        return generate_candidates(molecule, therapy_area, indication, wanted)

    seen: Set[str] = set()
    screened: List[Dict[str, object]] = []
    for entry in raw:
        name = str(entry.get("name") or "").strip()
        if not name or name.upper() in seen:
            continue
        candidate = _screen_name(
            name, str(entry.get("rationale") or ""), "AI-generated to the stated requirement",
            marketed, marketed_by_initial,
        )
        if candidate is None or candidate["exact_collision_with_marketed_brand"]:
            continue
        seen.add(name.upper())
        candidate["ai_generated"] = True
        screened.append(candidate)

    screened.sort(key=lambda c: (bool(c["phonetic_collision_with_marketed_brand"]), int(c["length"])))
    for candidate in screened[:wanted]:
        _attach_search_links(candidate)
    return screened[:wanted]


def generate_candidates(
    molecule: str,
    therapy_area: str = "",
    indication: str = "",
    wanted: int = 10,
) -> List[Dict[str, object]]:
    """Return `wanted` novel, collision-screened brand-name candidates."""
    resolved = resolve_molecule(molecule)
    stems = _molecule_stems(resolved.components) or ["Nova"]
    roots = _roots_for(therapy_area, indication)

    marketed = _marketed_names()
    # Bucket by first letter and length so each check compares against a
    # few hundred plausible names rather than all 49k.
    marketed_by_initial: Dict[str, List[str]] = {}
    for name in marketed:
        marketed_by_initial.setdefault(name[:1], []).append(name)

    seen: Set[str] = set()
    candidates: List[Dict[str, object]] = []

    def consider(name: str, rationale: str, construction: str) -> None:
        if len(candidates) >= wanted * 3:
            return
        clean = name.strip().title()
        upper = clean.upper()
        if upper in seen:
            return
        if not (MIN_LEN <= len(clean) <= MAX_LEN):
            return
        if any(bad in clean.lower() for bad in BANNED_FRAGMENTS):
            return
        if not re.fullmatch(r"[A-Za-z]+", clean):
            return
        # Reject anything already marketed, or confusably close to it. Soundex
        # alone is useless against 49k names — nearly every 4-char code is
        # taken — so closeness is measured by edit distance, which is much
        # nearer to how a regulator assesses look-alike/sound-alike risk.
        exact = upper in marketed
        phonetic = _too_close(upper, marketed_by_initial)
        seen.add(upper)
        candidates.append({
            "name": clean,
            "rationale": rationale,
            "construction": construction,
            "length": len(clean),
            "syllable_estimate": max(1, len(re.findall(r"[aeiouy]+", clean.lower()))),
            "soundex": _soundex(clean),
            "exact_collision_with_marketed_brand": exact,
            "phonetic_collision_with_marketed_brand": phonetic,
            "screening_status": (
                "Rejected — exact match to a marketed brand" if exact
                else "Caution — sounds like a marketed brand" if phonetic
                else "Clear of FDA Orange Book brands"
            ),
        })

    def blend(left: str, right: str) -> str:
        """Overlap the seam so the join reads as one word, not two glued."""
        left, right = left.strip(), right.strip()
        for overlap in (2, 1):
            if left[-overlap:].lower() == right[:overlap].lower():
                return (left + right[overlap:]).title()
        # Two consonants meeting is what makes a blend unpronounceable.
        if left[-1].lower() not in "aeiouy" and right[0].lower() not in "aeiouy":
            return (left + right[1:]).title()
        return (left + right).title()

    for stem in stems:
        short_stem = stem[:4]
        for root in roots:
            short_root = root[:4]
            consider(
                blend(short_stem, short_root.lower()),
                f"Molecule stem '{short_stem}' blended with '{root}', which signals the therapeutic benefit.",
                f"{short_stem} + {short_root.lower()}",
            )
            consider(
                blend(short_root, short_stem.lower()),
                f"'{root}' leads on benefit, resolving into the molecule stem '{short_stem}'.",
                f"{short_root} + {short_stem.lower()}",
            )
    for stem in stems:
        for suffix in SUFFIXES:
            consider(
                blend(stem[:5], suffix),
                f"Molecule stem '{stem[:5]}' with a soft '-{suffix}' ending for recall.",
                f"{stem[:5]} + -{suffix}",
            )
    for root in roots:
        for suffix in SUFFIXES:
            consider(
                blend(root, suffix),
                f"Function-led name from '{root}' with a '-{suffix}' ending.",
                f"{root} + -{suffix}",
            )

    # Clear names first, then cautions; never surface an exact collision.
    ranked = sorted(
        (c for c in candidates if not c["exact_collision_with_marketed_brand"]),
        key=lambda c: (bool(c["phonetic_collision_with_marketed_brand"]), int(c["length"])),
    )

    for candidate in ranked:
        candidate["ai_generated"] = False
        _attach_search_links(candidate)

    return ranked[:wanted]
