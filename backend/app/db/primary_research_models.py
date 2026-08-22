"""Primary market research a brand team collects itself: RCPA (Retail Chemist
Prescription Audit) pharmacy visits and structured HCP (doctor) questionnaires.

Neither can come from any public API — an RCPA finding is what a field rep
observed at a specific pharmacy on a specific visit, and a questionnaire
response is what a specific doctor said in a signed survey. Both are stored
as one team's field-collected attestation, tagged with who recorded it and
when, and are never blended into the licensed market-data or regulatory
layers — they inform the brand plan's own narrative fields directly, always
labeled as team-collected primary research rather than a verified secondary
source.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String, Text

from .database import Base


class RCPAEntryORM(Base):
    """One pharmacy visit in a Retail Chemist Prescription Audit."""

    __tablename__ = "rcpa_entries"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, nullable=False, index=True)

    pharmacy_name = Column(String, nullable=False)
    location = Column(String, nullable=True)

    molecule_awareness = Column(Boolean, nullable=False, default=False)
    active_prescribing = Column(Boolean, nullable=False, default=False)
    rx_frequency_note = Column(String, nullable=True)   # e.g. "2-3/month", free text as observed
    potential_rating = Column(String, nullable=True)    # 'High' | 'Medium' | 'Low' — the field rep's own call

    signal_note = Column(Text, nullable=False)          # what was actually observed at this visit
    action_note = Column(Text, nullable=True)           # recommended follow-up, if any

    recorded_by = Column(String, nullable=False)
    recorded_at = Column(String, nullable=False)


class HCPQuestionnaireORM(Base):
    """One structured doctor questionnaire response."""

    __tablename__ = "hcp_questionnaires"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, nullable=False, index=True)

    specialty = Column(String, nullable=False)
    respondent_code = Column(String, nullable=True)   # anonymized/coded label, not necessarily a real name

    cost_barrier_rating = Column(Integer, nullable=True)      # 0-10: how much cost blocks adherence/prescribing
    molecule_preference_rating = Column(Integer, nullable=True)  # 0-5: preference for this molecule in their practice
    efficacy_rating = Column(Integer, nullable=True)             # 0-5: perceived efficacy in their practice
    switch_intent = Column(Boolean, nullable=True)                # would they switch a patient to this brand

    key_quote = Column(Text, nullable=True)   # a direct note/quote from the respondent, if captured

    recorded_by = Column(String, nullable=False)
    recorded_at = Column(String, nullable=False)
