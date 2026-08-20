import re
from typing import List, Dict, Any
from urllib.parse import quote_plus
from ..models.trademark import TrademarkIntelligence, TrademarkNameSuggestion, CompetitorNamingPattern

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

def generate_trademark_intelligence(molecule_name: str, therapy_area: str = "Cardiometabolic") -> TrademarkIntelligence:
    """Generate trademark analysis, phonetic collision score, and proposed brand names."""
    clean_name = molecule_name.strip().title()
    
    # Analyze existing brand names and competitor patterns based on molecule
    existing_brands = []
    similar_names = []
    patterns = []
    suggestions = []
    
    if "empa" in clean_name.lower() or "dapa" in clean_name.lower() or "gliflozin" in clean_name.lower():
        existing_brands = ["Jardiance", "Farxiga", "Forxiga", "Invokana", "Steglatro", "Gibtulio"]
        similar_names = ["Jardianz", "Farxigo", "Invocana", "Empavel", "Dapacare"]
        patterns = [
            CompetitorNamingPattern(
                brand_name="Jardiance",
                company="Boehringer Ingelheim / Lilly",
                prefix_suffix_analysis="Jar- (Guardian root) + -diance (Radiance/Reliance)",
                syllable_count=3,
                cadence="Strong opening with optimistic suffix"
            ),
            CompetitorNamingPattern(
                brand_name="Farxiga",
                company="AstraZeneca",
                prefix_suffix_analysis="Far- (Distance/Reach) + -xi- (High tech pharmaceutical) + -ga",
                syllable_count=3,
                cadence="Dynamic, modern tech-driven pharmaceutical cadence"
            )
        ]
        
        # Proposed creative brand names
        raw_proposals = [
            ("Cardioflo", "Combines cardio-protection with fluid/filtration (SGLT2 flow mechanism)", "Authoritative & Scientific", "Cardio- + -flo"),
            ("Empavita", "Rooted in Empa- scientific heritage with -vita (vitality and life protection)", "Patient-Friendly & Vital", "Empa- + -vita"),
            ("Renovance", "Emphasizes renal protection and disease advancement prevention", "Authoritative & Scientific", "Reno- + -vance"),
            ("Glyxiva", "Sophisticated pharmaceutical tone blending glycemic control and vitality", "Modern & Dynamic", "Gly- + -xiva"),
            ("Vastavive", "Communicates broad multi-organ protection (cardio, renal, metabolic)", "Modern & Dynamic", "Vasta- + -vive")
        ]
    elif "sema" in clean_name.lower() or "tirez" in clean_name.lower() or "glutide" in clean_name.lower():
        existing_brands = ["Ozempic", "Wegovy", "Rybelsus", "Mounjaro", "Zepbound", "Victoza"]
        similar_names = ["Ozempix", "Wegovia", "Rybelsis", "Mounjari", "Semavita"]
        patterns = [
            CompetitorNamingPattern(
                brand_name="Ozempic",
                company="Novo Nordisk",
                prefix_suffix_analysis="O- (Distinct open vowel) + -zempic (Modern medical)",
                syllable_count=3,
                cadence="Memorable, crisp, distinct global trademark"
            ),
            CompetitorNamingPattern(
                brand_name="Wegovy",
                company="Novo Nordisk",
                prefix_suffix_analysis="We- (Empowerment / Collective) + -go- (Motion/Energy) + -vy (Vitality)",
                syllable_count=3,
                cadence="Empowering consumer lifestyle appeal"
            )
        ]
        raw_proposals = [
            ("Semavive", "Highlights semaglutide molecular lineage with vibrant metabolic restoration", "Patient-Friendly & Vital", "Sema- + -vive"),
            ("Metabozen", "Focuses on metabolic balance, weight equilibrium, and glycemic peace", "Modern & Dynamic", "Metabo- + -zen"),
            ("Incretiva", "Anchored in incretin receptor science with an active vitality suffix", "Authoritative & Scientific", "Incretin + -iva"),
            ("Leptinova", "Invokes satiety, metabolic reset, and novel standard of care", "Modern & Dynamic", "Lepti- + -nova"),
            ("AventiQ", "Premium, sleek healthcare identity suggesting forward momentum", "Authoritative & Scientific", "Aventi- + -Q")
        ]
    else:
        existing_brands = [f"{clean_name} Brand A", f"{clean_name} Brand B"]
        similar_names = [f"{clean_name[:4]}care", f"{clean_name[:4]}vance"]
        patterns = [
            CompetitorNamingPattern(
                brand_name="InnovatorBrand",
                company="Leading Pharma",
                prefix_suffix_analysis="Scientific stem + Latinate suffix",
                syllable_count=3,
                cadence="Authoritative scientific cadence"
            )
        ]
        raw_proposals = [
            (f"{clean_name[:4]}vance", "Signifies clinical advancement and superior efficacy", "Authoritative & Scientific", f"{clean_name[:4]} + -vance"),
            (f"{clean_name[:4]}care", "Emphasizes patient well-being and therapeutic safety", "Patient-Friendly & Vital", f"{clean_name[:4]} + -care"),
            (f"{clean_name[:4]}nova", "Highlights novel formulation and modern therapy standard", "Modern & Dynamic", f"{clean_name[:4]} + -nova"),
            (f"{clean_name[:4]}flow", "Reflects physiological harmony and continuous efficacy", "Modern & Dynamic", f"{clean_name[:4]} + -flow"),
            (f"{clean_name[:4]}guard", "Communicates disease protection and organ preservation", "Authoritative & Scientific", f"{clean_name[:4]} + -guard")
        ]
    
    for name, rationale, tone, stem in raw_proposals:
        soundex_code = calculate_soundex(name)
        
        # Risk assessment: check if soundex matches existing brand soundex
        existing_soundexes = [calculate_soundex(b) for b in existing_brands]
        collision_risk = "Low"
        if soundex_code in existing_soundexes:
            collision_risk = "Moderate (Phonetic Soundex Collision with existing brand)"
        
        encoded_query = quote_plus(f"{name} pharmaceutical class 5")
        
        suggestions.append(TrademarkNameSuggestion(
            name=name,
            rationale=rationale,
            linguistic_tone=tone,
            stem_origin=stem,
            phonetic_soundex=soundex_code,
            double_metaphone=name[:4].upper(),
            collision_risk=collision_risk,
            uspto_search_link=f"https://tmsearch.uspto.gov/search/search-results?query={encoded_query}",
            ip_india_search_link=f"https://ipindiaonline.gov.in/tmrpublicsearch/frmmain.aspx",
            wipo_search_link=f"https://branddb.wipo.int/en/similar-names?query={name}"
        ))
    
    return TrademarkIntelligence(
        molecule_name=clean_name,
        existing_brand_names=existing_brands,
        similar_sounding_names=similar_names,
        competitor_naming_patterns=patterns,
        suggested_brand_names=suggestions,
        trademark_risk_advisory="All proposed brand names must undergo formal Class 5 trademark clearance, linguistic vetting across global dialects, and FDA POCA (Phonetic and Orthographic Computer Analysis) evaluation to prevent look-alike sound-alike (LASA) medication errors prior to commercial adoption."
    )
