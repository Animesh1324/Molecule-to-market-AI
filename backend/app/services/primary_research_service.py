"""CRUD and honest aggregation for RCPA visits and HCP questionnaires.

Every summary statistic here is computed from rows the team itself entered —
nothing is estimated, interpolated, or filled in when data is thin. An empty
project returns an explicit "no entries yet" state rather than a plausible-
looking zero, so the gap is visible rather than silently blended into a chart.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..db.database import SessionLocal
from ..db.primary_research_models import HCPQuestionnaireORM, RCPAEntryORM


def _rcpa_dict(row: RCPAEntryORM) -> Dict[str, Any]:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "pharmacy_name": row.pharmacy_name,
        "location": row.location,
        "molecule_awareness": row.molecule_awareness,
        "active_prescribing": row.active_prescribing,
        "rx_frequency_note": row.rx_frequency_note,
        "potential_rating": row.potential_rating,
        "signal_note": row.signal_note,
        "action_note": row.action_note,
        "recorded_by": row.recorded_by,
        "recorded_at": row.recorded_at,
    }


def _hcp_dict(row: HCPQuestionnaireORM) -> Dict[str, Any]:
    return {
        "id": row.id,
        "project_id": row.project_id,
        "specialty": row.specialty,
        "respondent_code": row.respondent_code,
        "cost_barrier_rating": row.cost_barrier_rating,
        "molecule_preference_rating": row.molecule_preference_rating,
        "efficacy_rating": row.efficacy_rating,
        "switch_intent": row.switch_intent,
        "key_quote": row.key_quote,
        "recorded_by": row.recorded_by,
        "recorded_at": row.recorded_at,
    }


def add_rcpa_entry(
    project_id: str,
    pharmacy_name: str,
    signal_note: str,
    recorded_by: str,
    location: Optional[str] = None,
    molecule_awareness: bool = False,
    active_prescribing: bool = False,
    rx_frequency_note: Optional[str] = None,
    potential_rating: Optional[str] = None,
    action_note: Optional[str] = None,
) -> Dict[str, Any]:
    """Record one RCPA pharmacy visit. `signal_note` is mandatory — a row with
    no observation recorded is not a finding, just a checkbox.
    """
    if not pharmacy_name or not pharmacy_name.strip():
        raise ValueError("A pharmacy name is required.")
    if not signal_note or not signal_note.strip():
        raise ValueError("Record what was actually observed at this visit.")

    record = RCPAEntryORM(
        id=uuid.uuid4().hex,
        project_id=project_id,
        pharmacy_name=pharmacy_name.strip(),
        location=(location or "").strip() or None,
        molecule_awareness=molecule_awareness,
        active_prescribing=active_prescribing,
        rx_frequency_note=(rx_frequency_note or "").strip() or None,
        potential_rating=(potential_rating or "").strip() or None,
        signal_note=signal_note.strip(),
        action_note=(action_note or "").strip() or None,
        recorded_by=recorded_by.strip() or "Unattributed",
        recorded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    session = SessionLocal()
    try:
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return _rcpa_dict(record)


def list_rcpa_entries(project_id: str) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = (session.query(RCPAEntryORM)
                .filter(RCPAEntryORM.project_id == project_id)
                .order_by(RCPAEntryORM.recorded_at.desc()).all())
        return [_rcpa_dict(r) for r in rows]
    finally:
        session.close()


def delete_rcpa_entry(entry_id: str) -> bool:
    session = SessionLocal()
    try:
        row = session.get(RCPAEntryORM, entry_id)
        if not row:
            return False
        session.delete(row)
        session.commit()
        return True
    finally:
        session.close()


def add_hcp_questionnaire(
    project_id: str,
    specialty: str,
    recorded_by: str,
    respondent_code: Optional[str] = None,
    cost_barrier_rating: Optional[int] = None,
    molecule_preference_rating: Optional[int] = None,
    efficacy_rating: Optional[int] = None,
    switch_intent: Optional[bool] = None,
    key_quote: Optional[str] = None,
) -> Dict[str, Any]:
    if not specialty or not specialty.strip():
        raise ValueError("The respondent's specialty is required.")
    for name, value, bound in (
        ("cost_barrier_rating", cost_barrier_rating, 10),
        ("molecule_preference_rating", molecule_preference_rating, 5),
        ("efficacy_rating", efficacy_rating, 5),
    ):
        if value is not None and not (0 <= value <= bound):
            raise ValueError(f"{name} must be between 0 and {bound}.")

    record = HCPQuestionnaireORM(
        id=uuid.uuid4().hex,
        project_id=project_id,
        specialty=specialty.strip(),
        respondent_code=(respondent_code or "").strip() or None,
        cost_barrier_rating=cost_barrier_rating,
        molecule_preference_rating=molecule_preference_rating,
        efficacy_rating=efficacy_rating,
        switch_intent=switch_intent,
        key_quote=(key_quote or "").strip() or None,
        recorded_by=recorded_by.strip() or "Unattributed",
        recorded_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    session = SessionLocal()
    try:
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return _hcp_dict(record)


def list_hcp_questionnaires(project_id: str) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = (session.query(HCPQuestionnaireORM)
                .filter(HCPQuestionnaireORM.project_id == project_id)
                .order_by(HCPQuestionnaireORM.recorded_at.desc()).all())
        return [_hcp_dict(r) for r in rows]
    finally:
        session.close()


def delete_hcp_questionnaire(entry_id: str) -> bool:
    session = SessionLocal()
    try:
        row = session.get(HCPQuestionnaireORM, entry_id)
        if not row:
            return False
        session.delete(row)
        session.commit()
        return True
    finally:
        session.close()


def summarize_primary_research(project_id: str) -> Dict[str, Any]:
    """Real aggregates computed only from what the team has entered so far.

    Returns `has_data: False` with no computed figures when a project has no
    entries yet — an aggregate over zero rows is not a finding, it's a gap.
    """
    rcpa = list_rcpa_entries(project_id)
    hcp = list_hcp_questionnaires(project_id)

    summary: Dict[str, Any] = {
        "has_data": bool(rcpa or hcp),
        "rcpa_total": len(rcpa),
        "hcp_total": len(hcp),
    }

    if rcpa:
        aware = sum(1 for r in rcpa if r["molecule_awareness"])
        active = sum(1 for r in rcpa if r["active_prescribing"])
        high_potential = sum(1 for r in rcpa if (r["potential_rating"] or "").lower() == "high")
        summary.update({
            "rcpa_aware_count": aware,
            "rcpa_aware_percent": round(aware / len(rcpa) * 100, 1),
            "rcpa_active_count": active,
            "rcpa_active_percent": round(active / len(rcpa) * 100, 1),
            "rcpa_high_potential_count": high_potential,
        })

    if hcp:
        cost_ratings = [r["cost_barrier_rating"] for r in hcp if r["cost_barrier_rating"] is not None]
        preference_ratings = [r["molecule_preference_rating"] for r in hcp if r["molecule_preference_rating"] is not None]
        efficacy_ratings = [r["efficacy_rating"] for r in hcp if r["efficacy_rating"] is not None]
        switch_responses = [r["switch_intent"] for r in hcp if r["switch_intent"] is not None]

        if cost_ratings:
            summary["hcp_avg_cost_barrier_rating"] = round(sum(cost_ratings) / len(cost_ratings), 1)
            summary["hcp_cost_barrier_respondents"] = len(cost_ratings)
        if preference_ratings:
            summary["hcp_avg_preference_rating"] = round(sum(preference_ratings) / len(preference_ratings), 1)
        if efficacy_ratings:
            summary["hcp_avg_efficacy_rating"] = round(sum(efficacy_ratings) / len(efficacy_ratings), 1)
        if switch_responses:
            switch_yes = sum(1 for s in switch_responses if s)
            summary["hcp_switch_intent_count"] = switch_yes
            summary["hcp_switch_intent_percent"] = round(switch_yes / len(switch_responses) * 100, 1)
            summary["hcp_switch_intent_respondents"] = len(switch_responses)

        specialties: Dict[str, int] = {}
        for r in hcp:
            specialties[r["specialty"]] = specialties.get(r["specialty"], 0) + 1
        summary["hcp_specialty_breakdown"] = specialties

    return summary
