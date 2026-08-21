from pydantic import BaseModel
from typing import List


class CDSCOChecklistItem(BaseModel):
    step: str
    source_register: str
    url: str
    what_to_check: str
    why_it_matters: str
    blocks_launch: bool = False


class CDSCOIntelligence(BaseModel):
    query: str
    display_name: str
    components: List[str] = []
    is_combination: bool = False
    checklist: List[CDSCOChecklistItem] = []
    blocking_steps: List[str] = []
    automation_note: str = ""
    india_specific_warning: str = ""
