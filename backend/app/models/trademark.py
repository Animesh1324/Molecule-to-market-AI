from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TrademarkNameSuggestion(BaseModel):
    name: str
    rationale: str
    linguistic_tone: str # 'Authoritative & Scientific', 'Patient-Friendly & Vital', 'Modern & Dynamic'
    stem_origin: str
    phonetic_soundex: str
    double_metaphone: str
    collision_risk: str # 'Low', 'Moderate', 'High'
    uspto_search_link: str
    ip_india_search_link: str
    wipo_search_link: str

class CompetitorNamingPattern(BaseModel):
    brand_name: str
    company: str
    prefix_suffix_analysis: str
    syllable_count: int
    cadence: str

class TrademarkIntelligence(BaseModel):
    molecule_name: str
    existing_brand_names: List[str] = []
    similar_sounding_names: List[str] = []
    competitor_naming_patterns: List[CompetitorNamingPattern] = []
    suggested_brand_names: List[TrademarkNameSuggestion] = []
    trademark_risk_advisory: str
    # Provenance for the naming grid, so the UI can tell an AI-drafted batch
    # (creative, requirement-aware) apart from the deterministic fallback.
    ai_generated: bool = False
    requirement_applied: Optional[str] = None
    existing_brands_source: str = "none"  # 'market_data' | 'reference_class' | 'none'
