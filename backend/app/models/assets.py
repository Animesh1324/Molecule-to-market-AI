from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class VisualAidSlide(BaseModel):
    slide_number: int
    slide_title: str
    headline_for_doctor: str
    visual_concept_description: str
    clinical_data_chart_description: str
    key_bullet_points: List[str] = []
    medical_representative_talk_track: str
    evidence_citation: str # Mandatory source backing
    safety_fair_balance_footer: str

class LBLBrief(BaseModel):
    title: str
    target_audience: str # 'Cardiologists & Endocrinologists'
    page_1_content_headline: str
    page_1_clinical_evidence_summary: str
    page_2_dosing_and_safety_summary: str
    call_to_action: str
    prescribing_info_footnote: str

class MRObjectionHandling(BaseModel):
    doctor_objection: str
    underlying_concern: str
    recommended_mr_response: str
    supporting_clinical_trial: str
    recommended_visual_aid_page: int

class PatientEducationLeaflet(BaseModel):
    title: str
    plain_language_condition_summary: str
    how_this_medicine_works: str
    how_to_take_and_adherence: str
    what_to_expect_and_side_effects: str
    lifestyle_and_diet_tips: List[str] = []

class CreativeCommercialAssets(BaseModel):
    molecule_name: str
    brand_name: str
    campaign_theme: str
    logo_direction: str
    pack_mockup_brief: str
    visual_aid_slides: List[VisualAidSlide] = []
    lbl_brief: LBLBrief
    mr_objection_handling_guide: List[MRObjectionHandling] = []
    patient_education_leaflet: PatientEducationLeaflet
    conference_booth_concept: str
    digital_email_copy: str
    banner_ad_copy: str
