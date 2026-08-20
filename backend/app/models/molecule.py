from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Pharmacokinetics(BaseModel):
    absorption: str = ""
    bioavailability: str = ""
    tmax: str = ""
    distribution: str = ""
    protein_binding: str = ""
    metabolism: str = ""
    cyp_pathways: List[str] = []
    elimination: str = ""
    half_life: str = ""
    clearance: str = ""

class SpecialPopulations(BaseModel):
    pregnancy: str = ""
    lactation: str = ""
    pediatric: str = ""
    geriatric: str = ""
    renal_impairment: str = ""
    hepatic_impairment: str = ""

class AdverseEffects(BaseModel):
    common: List[str] = []
    rare: List[str] = []
    serious: List[str] = []

class MoleculeProfile(BaseModel):
    generic_name: str
    chemical_name: Optional[str] = None
    chemical_class: str
    pharmacological_class: str
    cas_number: Optional[str] = None
    pubchem_cid: Optional[int] = None
    smiles: Optional[str] = None
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    mechanism_of_action: str
    pharmacodynamics: str
    pharmacokinetics: Pharmacokinetics
    approved_indications: List[str] = []
    investigational_indications: List[str] = []
    dosage_forms: List[str] = []
    routes_of_administration: List[str] = []
    standard_dosages: List[str] = []
    contraindications: List[str] = []
    black_box_warnings: List[str] = []
    drug_interactions: List[str] = []
    adverse_effects: AdverseEffects
    special_populations: SpecialPopulations
    differentiating_science: str
    key_targets: List[str] = []
