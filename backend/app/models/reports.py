from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReportExportRequest(BaseModel):
    project_id: str
    report_type: str # 'molecule_monograph', 'complete_brand_plan', 'executive_pitch_deck', 'visual_aid_brief', 'competitor_report', 'market_forecast_sheet'
    format: str # 'pdf', 'docx', 'pptx', 'xlsx', 'html'

class MLRAuditEntry(BaseModel):
    id: str
    timestamp: str
    action_type: str # 'CLAIM_VERIFIED', 'LABEL_SYNCED', 'FAIR_BALANCE_CHECKED', 'REPORT_EXPORTED'
    item_reference: str
    verified_source: str
    status: str # 'VERIFIED', 'FLAGGED', 'APPROVED'
    auditor: str
