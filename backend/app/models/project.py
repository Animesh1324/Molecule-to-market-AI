from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProjectCreate(BaseModel):
    title: str = Field(..., description="Project title or brand initiative")
    target_molecule_name: str = Field(..., description="Generic/Molecule name e.g. Empagliflozin, Semaglutide")
    brand_working_name: Optional[str] = Field(None, description="Proposed or existing brand name")
    therapy_area: str = Field("Cardiometabolic", description="Therapeutic area e.g. Oncology, Cardiology, Immunology")
    primary_indication: str = Field(..., description="Target clinical indication")
    target_geography: str = Field("Global", description="Target market: US, India, EU, Global")

class Project(BaseModel):
    id: str
    title: str
    target_molecule_name: str
    brand_working_name: Optional[str] = None
    therapy_area: str
    primary_indication: str
    target_geography: str
    status: str = "active" # draft, active, approved, archived
    created_at: str
    updated_at: str
