import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from ..models.trademark import CompetitorNamingPattern, TrademarkIntelligence, TrademarkNameSuggestion
from .claude_client import ClaudeUnavailable, generate_json, is_configured
from . import market_data_service as market

logger = logging.getLogger(__name__)


def calculate_soundex(name: str) -> str:
    """Standard American Soundex Algorithm."""
    if not name:
        return ""
    name = name.upper()
    soundex_map = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }

    first_letter = name[0]
    tail = name[1:]

    encoded = []
    prev_code = soundex_map.get(first_letter, '')

    for char in tail:
        code = soundex_map.get(char, '')
        if code != prev_code:
            if code != '':
                encoded.append(code)
            prev_code = code

    soundex_val = (first_letter + ''.join(encoded) + '000')[:4]
    return soundex_val


# Reference naming patterns for two well-studied classes, used only when the
# loaded market extract has no rows for the molecule (so there is nothing real
# to fall back on). Kept small and explicitly labeled as reference material —
# never presented as this project's own live market data.
_REFERENCE_CLASSES: Dict[str, Dict[str, List[Any]]] = {
    "gliflozin": {
        "brands": [("Jardiance", "Boehringer Ingelheim / Lilly"), ("Farxiga", "AstraZeneca"),
                   ("Invokana", "Janssen"), ("Steglatro", "Merck")],
    },
    "glutide": {
        "brands": [("Ozempic", "Novo Nordisk"), ("Mounjaro", "Eli Lilly"),
                   ("Victoza", "Novo Nordisk"), ("Trulicity", "Eli Lilly")],
    },
}

# Fallback naming particles used only when AI drafting is not configured.
# Deterministic and clearly a template, not a creative-naming substitute —
# `ai_generated=False` on the response tells the UI to say so.
_FALLBACK_TONES = [
    ("vance", "Authoritative & Scientific", "Signifies clinical advancement"),
    ("care", "Patient-Friendly & Vital", "Emphasizes patient well-being"),
    ("nova", "Modern & Dynamic", "Highlights a novel therapy standard"),
    ("flow", "Modern & Dynamic", "Reflects physiological harmony"),
    ("guard", "Authoritative & Scientific", "Communicates disease protection"),
    ("vita", "Patient-Friendly & Vital", "Evokes vitality and life protection"),
    ("zen", "Patient-Friendly & Vital", "Evokes balance and relief"),
    ("prime", "Authoritative & Scientific", "Signals first-line, front-rank therapy"),
    ("well", "Patient-Friendly & Vital", "Plain-language wellness cue"),
    ("core", "Authoritative & Scientific", "Signals treating the root mechanism"),
]


def _reference_class_for(molecule: str) -> Optional[str]:
    lowered = molecule.lower()
    for key in _REFERENCE_CLASSES:
        if key in lowered:
            return key
    return None


def _syllable_count(word: str) -> int:
    """Rough vowel-group heuristic — good enough for cadence commentary, not phonetics research."""
    groups = re.findall(r"[aeiouyAEIOUY]+", word)
    return max(1, len(groups))


def _existing_brands(molecule: str, therapy_area: str) -> tuple[List[str], List[CompetitorNamingPattern], str]:
    """Real brand names to check new suggestions against, and where they came from.

    Prefers the loaded market extract (any molecule actually on file) over the
    small hardcoded reference classes, so collision checking reflects real
    brands rather than a fixed, molecule-agnostic placeholder list.
    """
    overview = market.brand_competitors(molecule, limit=10)
    brands = overview.get("brands") or []
    if brands:
        names = [b["brand"] for b in brands if b.get("brand")]
        patterns = [
            CompetitorNamingPattern(
                brand_name=b["brand"],
                company=b.get("company") or "Unknown",
                prefix_suffix_analysis=f"{b['brand'][:len(b['brand'])//2] or b['brand']}- / -{b['brand'][len(b['brand'])//2:] or ''}",
                syllable_count=_syllable_count(b["brand"]),
                cadence=f"{b.get('market_share_percent', 0):.1f}% share in the current extract",
            )
            for b in brands[:4]
        ]
        return names, patterns, "market_data"

    ref_key = _reference_class_for(molecule)
    if ref_key:
        ref_brands = _REFERENCE_CLASSES[ref_key]["brands"]
        names = [b[0] for b in ref_brands]
        patterns = [
            CompetitorNamingPattern(
                brand_name=name,
                company=company,
                prefix_suffix_analysis=f"{name[:len(name)//2]}- / -{name[len(name)//2:]}",
                syllable_count=_syllable_count(name),
                cadence="Reference class example — not from the loaded market extract",
            )
            for name, company in ref_brands
        ]
        return names, patterns, "reference_class"

    return [], [], "none"


_NAMING_SYSTEM_PROMPT = """You are a pharmaceutical brand-naming specialist proposing \
candidate names for a Class 5 (pharmaceutical) trademark filing.

Rules, in order of priority:
1. Never propose a name that itself asserts or implies an unsubstantiated clinical \
claim — no "best", "cure", "safe", "superior", or efficacy/dosage terms embedded in \
the name. Regulatory naming review (USFDA POCA / CDSCO) rejects names read as a claim.
2. Avoid names that are phonetically close to any name in the existing-brands list \
supplied — that list is real competitor and reference brands, and closeness there is \
a genuine look-alike/sound-alike (LASA) medication-error risk, not just a marketing \
concern.
3. If a naming requirement is supplied, satisfy it — it is the brand team's brief, \
not a suggestion to weigh against your own preference.
4. Vary linguistic tone across the batch (Authoritative & Scientific, Patient-Friendly \
& Vital, Modern & Dynamic) rather than returning near-duplicates of one style.
5. Each name needs a short rationale grounded in the molecule's actual pharmacological \
class or the stated therapy area — do not invent clinical claims to justify a name.

Return invented, coinable words suitable for trademark filing — not real drug names, \
not generic English words."""


async def _ai_generate_names(
    molecule: str,
    therapy_area: str,
    indication: Optional[str],
    existing_brands: List[str],
    requirement: Optional[str],
    count: int,
    exclude: List[str],
) -> Optional[List[Dict[str, str]]]:
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
                        "linguistic_tone": {
                            "type": "string",
                            "enum": ["Authoritative & Scientific", "Patient-Friendly & Vital", "Modern & Dynamic"],
                        },
                        "stem_origin": {"type": "string"},
                    },
                    "required": ["name", "rationale", "linguistic_tone", "stem_origin"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["names"],
        "additionalProperties": False,
    }

    prompt_lines = [
        f"Molecule: {molecule}",
        f"Therapy area: {therapy_area}",
    ]
    if indication:
        prompt_lines.append(f"Indication: {indication}")
    if existing_brands:
        prompt_lines.append(f"Existing/competitor brand names to stay phonetically distinct from: {', '.join(existing_brands)}")
    if exclude:
        prompt_lines.append(f"Already suggested in a prior batch — do not repeat these: {', '.join(exclude)}")
    if requirement:
        prompt_lines.append(f"Brand team's naming requirement: {requirement}")
    prompt_lines.append(f"Propose exactly {count} candidate names.")

    try:
        result = await generate_json(
            system=_NAMING_SYSTEM_PROMPT,
            prompt="\n".join(prompt_lines),
            schema=schema,
        )
    except ClaudeUnavailable as exc:
        logger.warning("AI brand naming unavailable, using template: %s", exc)
        return None

    names = result.get("names")
    return names if isinstance(names, list) else None


def _fallback_names(molecule: str, count: int, exclude: List[str]) -> List[Dict[str, str]]:
    """Deterministic naming used only when AI drafting has no key configured."""
    clean_name = molecule.strip().title()
    stem = clean_name[:4] if len(clean_name) >= 4 else clean_name
    excluded_lower = {e.lower() for e in exclude}
    suggestions: List[Dict[str, str]] = []
    for suffix, tone, rationale in _FALLBACK_TONES:
        if len(suggestions) >= count:
            break
        name = f"{stem}{suffix}".title()
        if name.lower() in excluded_lower:
            continue
        suggestions.append({
            "name": name,
            "rationale": f"{rationale} (template pattern — enable AI drafting for creative, requirement-aware naming).",
            "linguistic_tone": tone,
            "stem_origin": f"{stem}- + -{suffix}",
        })
    return suggestions


async def generate_trademark_intelligence(
    molecule_name: str,
    therapy_area: str = "Cardiometabolic",
    indication: Optional[str] = None,
    requirement: Optional[str] = None,
    count: int = 8,
    exclude: Optional[List[str]] = None,
) -> TrademarkIntelligence:
    """Generate trademark analysis, phonetic collision score, and proposed brand names.

    Existing-brand and naming-pattern data comes from the loaded market extract
    when the molecule is on file, so collision checking reflects real
    competitors rather than a fixed placeholder list. Name suggestions come
    from Claude when configured (creative, honors any stated requirement) or a
    labeled deterministic template otherwise — never presented as the same
    thing.
    """
    clean_name = molecule_name.strip().title()
    exclude = exclude or []

    existing_brands, patterns, brands_source = _existing_brands(molecule_name, therapy_area)
    existing_soundexes = {calculate_soundex(b) for b in existing_brands}

    ai_generated = False
    raw_names: Optional[List[Dict[str, str]]] = None
    if is_configured():
        raw_names = await _ai_generate_names(
            clean_name, therapy_area, indication, existing_brands, requirement, count, exclude,
        )
        ai_generated = raw_names is not None

    if raw_names is None:
        raw_names = _fallback_names(clean_name, count, exclude)

    suggestions: List[TrademarkNameSuggestion] = []
    for entry in raw_names:
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        soundex_code = calculate_soundex(name)
        collision_risk = "Moderate (Phonetic Soundex Collision with an existing brand)" if soundex_code in existing_soundexes else "Low"
        encoded_query = quote_plus(f"{name} pharmaceutical class 5")
        suggestions.append(TrademarkNameSuggestion(
            name=name,
            rationale=str(entry.get("rationale") or "").strip(),
            linguistic_tone=str(entry.get("linguistic_tone") or "Modern & Dynamic"),
            stem_origin=str(entry.get("stem_origin") or ""),
            phonetic_soundex=soundex_code,
            double_metaphone=name[:4].upper(),
            collision_risk=collision_risk,
            uspto_search_link=f"https://tmsearch.uspto.gov/search/search-results?query={encoded_query}",
            ip_india_search_link="https://ipindiaonline.gov.in/tmrpublicsearch/frmmain.aspx",
            wipo_search_link=f"https://branddb.wipo.int/en/similar-names?query={name}",
        ))

    similar_sounding = [
        name for name in existing_brands
        if any(calculate_soundex(name) == s.phonetic_soundex for s in suggestions)
    ]

    return TrademarkIntelligence(
        molecule_name=clean_name,
        existing_brand_names=existing_brands,
        similar_sounding_names=similar_sounding,
        competitor_naming_patterns=patterns,
        suggested_brand_names=suggestions,
        trademark_risk_advisory=(
            "All proposed brand names must undergo formal Class 5 trademark clearance, "
            "linguistic vetting across global dialects, and FDA POCA (Phonetic and "
            "Orthographic Computer Analysis) evaluation to prevent look-alike sound-alike "
            "(LASA) medication errors prior to commercial adoption."
        ),
        ai_generated=ai_generated,
        requirement_applied=requirement,
        existing_brands_source=brands_source,
    )
