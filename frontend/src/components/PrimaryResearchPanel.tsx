'use client';

/**
 * RCPA (Retail Chemist Prescription Audit) and structured HCP questionnaire
 * entry — the primary field research a brand team collects itself. Neither
 * type can come from any API; these are direct observations and survey
 * responses the team records here so they flow into the brand plan's
 * doctor/market insights and the AI-drafting grounding as real, team-
 * collected field data — never blended into licensed market data or
 * presented as an independently verified secondary source.
 */

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, ClipboardList, Plus, Stethoscope, Store, Trash2 } from 'lucide-react';
import {
  addHCPQuestionnaire,
  addRCPAEntry,
  deleteHCPQuestionnaire,
  deleteRCPAEntry,
  fetchHCPQuestionnaires,
  fetchPrimaryResearchSummary,
  fetchRCPAEntries,
} from '../lib/api';
import { HCPQuestionnaire, PrimaryResearchSummary, RCPAEntry } from '../lib/types';

interface Props {
  projectId: string;
  currentUser?: string;
}

const card = 'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

export default function PrimaryResearchPanel({ projectId, currentUser }: Props) {
  const [tab, setTab] = useState<'rcpa' | 'hcp'>('rcpa');
  const [summary, setSummary] = useState<PrimaryResearchSummary | null>(null);
  const [rcpaEntries, setRcpaEntries] = useState<RCPAEntry[]>([]);
  const [hcpEntries, setHcpEntries] = useState<HCPQuestionnaire[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showRcpaForm, setShowRcpaForm] = useState(false);
  const [showHcpForm, setShowHcpForm] = useState(false);

  // RCPA form state
  const [pharmacyName, setPharmacyName] = useState('');
  const [location, setLocation] = useState('');
  const [awareness, setAwareness] = useState(false);
  const [activeRx, setActiveRx] = useState(false);
  const [rxFrequency, setRxFrequency] = useState('');
  const [potential, setPotential] = useState('Medium');
  const [signalNote, setSignalNote] = useState('');
  const [actionNote, setActionNote] = useState('');

  // HCP form state
  const [specialty, setSpecialty] = useState('');
  const [respondentCode, setRespondentCode] = useState('');
  const [costBarrier, setCostBarrier] = useState('');
  const [preference, setPreference] = useState('');
  const [efficacy, setEfficacy] = useState('');
  const [switchIntent, setSwitchIntent] = useState<'yes' | 'no' | ''>('');
  const [keyQuote, setKeyQuote] = useState('');
  const [recordedBy, setRecordedBy] = useState(currentUser || '');

  const refresh = useCallback(async () => {
    try {
      const [s, r, h] = await Promise.all([
        fetchPrimaryResearchSummary(projectId),
        fetchRCPAEntries(projectId),
        fetchHCPQuestionnaires(projectId),
      ]);
      setSummary(s);
      setRcpaEntries(r);
      setHcpEntries(h);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load primary research.');
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const submitRcpa = async () => {
    setBusy(true);
    setError(null);
    try {
      await addRCPAEntry({
        project_id: projectId, pharmacy_name: pharmacyName, signal_note: signalNote, recorded_by: recordedBy,
        location: location || undefined, molecule_awareness: awareness, active_prescribing: activeRx,
        rx_frequency_note: rxFrequency || undefined, potential_rating: potential, action_note: actionNote || undefined,
      });
      setPharmacyName(''); setLocation(''); setAwareness(false); setActiveRx(false);
      setRxFrequency(''); setPotential('Medium'); setSignalNote(''); setActionNote('');
      setShowRcpaForm(false);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save this RCPA entry.');
    } finally {
      setBusy(false);
    }
  };

  const submitHcp = async () => {
    setBusy(true);
    setError(null);
    try {
      await addHCPQuestionnaire({
        project_id: projectId, specialty, recorded_by: recordedBy,
        respondent_code: respondentCode || undefined,
        cost_barrier_rating: costBarrier ? Number(costBarrier) : undefined,
        molecule_preference_rating: preference ? Number(preference) : undefined,
        efficacy_rating: efficacy ? Number(efficacy) : undefined,
        switch_intent: switchIntent ? switchIntent === 'yes' : undefined,
        key_quote: keyQuote || undefined,
      });
      setSpecialty(''); setRespondentCode(''); setCostBarrier(''); setPreference('');
      setEfficacy(''); setSwitchIntent(''); setKeyQuote('');
      setShowHcpForm(false);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save this questionnaire response.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Summary */}
      <div className={card}>
        <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider mb-3">
          Field Research Summary
        </h3>
        {!summary?.has_data ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            No RCPA visits or HCP questionnaire responses on file yet for this project. Add entries below —
            these figures feed directly into the brand plan's doctor &amp; market insights and, when AI drafting
            is configured, the model's grounding context.
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            {summary.rcpa_total > 0 && (
              <>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Pharmacies visited</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.rcpa_total}</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Aware</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.rcpa_aware_count}/{summary.rcpa_total} ({summary.rcpa_aware_percent}%)</span>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">Active Rx</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.rcpa_active_count}/{summary.rcpa_total} ({summary.rcpa_active_percent}%)</span>
                </div>
              </>
            )}
            {summary.hcp_total > 0 && (
              <>
                <div>
                  <span className="text-slate-500 dark:text-slate-400 block">HCP respondents</span>
                  <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.hcp_total}</span>
                </div>
                {summary.hcp_avg_cost_barrier_rating !== undefined && (
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block">Avg. cost-barrier rating</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.hcp_avg_cost_barrier_rating}/10</span>
                  </div>
                )}
                {summary.hcp_switch_intent_percent !== undefined && (
                  <div>
                    <span className="text-slate-500 dark:text-slate-400 block">Switch intent</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-white">{summary.hcp_switch_intent_percent}%</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
        <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-3">
          Directional field findings the team collected itself — not statistically confirmatory, and never blended into licensed market data.
        </p>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setTab('rcpa')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${tab === 'rcpa' ? 'bg-brand-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}
        >
          <Store className="w-3.5 h-3.5" /> RCPA ({rcpaEntries.length})
        </button>
        <button
          onClick={() => setTab('hcp')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${tab === 'hcp' ? 'bg-brand-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}
        >
          <Stethoscope className="w-3.5 h-3.5" /> HCP Questionnaire ({hcpEntries.length})
        </button>
      </div>

      {tab === 'rcpa' && (
        <div className="space-y-4">
          <button
            onClick={() => setShowRcpaForm((v) => !v)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold"
          >
            <Plus className="w-4 h-4" /> Record a pharmacy visit
          </button>

          {showRcpaForm && (
            <div className={`${card} space-y-3`}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input value={pharmacyName} onChange={(e) => setPharmacyName(e.target.value)} placeholder="Pharmacy name *"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
                <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Location (optional)"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-slate-600 dark:text-slate-300">
                <label className="flex items-center gap-1.5"><input type="checkbox" checked={awareness} onChange={(e) => setAwareness(e.target.checked)} /> Molecule awareness</label>
                <label className="flex items-center gap-1.5"><input type="checkbox" checked={activeRx} onChange={(e) => setActiveRx(e.target.checked)} /> Active prescribing/dispensing</label>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input value={rxFrequency} onChange={(e) => setRxFrequency(e.target.value)} placeholder="Rx frequency note, e.g. '2-3/month'"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
                <select value={potential} onChange={(e) => setPotential(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white">
                  <option value="High">High potential</option>
                  <option value="Medium">Medium potential</option>
                  <option value="Low">Low potential</option>
                </select>
              </div>
              <textarea value={signalNote} onChange={(e) => setSignalNote(e.target.value)} placeholder="What was observed at this visit? *" rows={2}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              <textarea value={actionNote} onChange={(e) => setActionNote(e.target.value)} placeholder="Recommended follow-up (optional)" rows={2}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              <input value={recordedBy} onChange={(e) => setRecordedBy(e.target.value)} placeholder="Recorded by *"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              <button onClick={submitRcpa} disabled={busy || !pharmacyName.trim() || !signalNote.trim() || !recordedBy.trim()}
                className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-semibold">
                Save visit
              </button>
            </div>
          )}

          <div className="space-y-3">
            {rcpaEntries.map((entry) => (
              <div key={entry.id} className={`${card} flex items-start justify-between gap-3`}>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white">{entry.pharmacy_name}</span>
                    {entry.location && <span className="text-slate-400">· {entry.location}</span>}
                    {entry.potential_rating && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px]">{entry.potential_rating} potential</span>
                    )}
                  </div>
                  <div className="flex gap-3 text-slate-500 dark:text-slate-400">
                    <span>{entry.molecule_awareness ? '✓ aware' : '✗ not aware'}</span>
                    <span>{entry.active_prescribing ? '✓ active Rx' : '✗ not active'}</span>
                    {entry.rx_frequency_note && <span>{entry.rx_frequency_note}</span>}
                  </div>
                  <p className="text-slate-600 dark:text-slate-300">{entry.signal_note}</p>
                  {entry.action_note && <p className="text-teal-700 dark:text-teal-400">→ {entry.action_note}</p>}
                  <p className="text-slate-400 dark:text-slate-500">{entry.recorded_by} · {entry.recorded_at}</p>
                </div>
                <button onClick={() => deleteRCPAEntry(entry.id).then(refresh)} className="text-slate-400 hover:text-red-500 shrink-0">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'hcp' && (
        <div className="space-y-4">
          <button
            onClick={() => setShowHcpForm((v) => !v)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold"
          >
            <Plus className="w-4 h-4" /> Record a questionnaire response
          </button>

          {showHcpForm && (
            <div className={`${card} space-y-3`}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="Specialty *"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
                <input value={respondentCode} onChange={(e) => setRespondentCode(e.target.value)} placeholder="Respondent code (anonymized, optional)"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input type="number" min={0} max={10} value={costBarrier} onChange={(e) => setCostBarrier(e.target.value)} placeholder="Cost-barrier (0-10)"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
                <input type="number" min={0} max={5} value={preference} onChange={(e) => setPreference(e.target.value)} placeholder="Preference (0-5)"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
                <input type="number" min={0} max={5} value={efficacy} onChange={(e) => setEfficacy(e.target.value)} placeholder="Perceived efficacy (0-5)"
                  className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              </div>
              <select value={switchIntent} onChange={(e) => setSwitchIntent(e.target.value as 'yes' | 'no' | '')}
                className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white">
                <option value="">Switch intent — not asked</option>
                <option value="yes">Would switch a patient</option>
                <option value="no">Would not switch</option>
              </select>
              <textarea value={keyQuote} onChange={(e) => setKeyQuote(e.target.value)} placeholder="Direct quote or note (optional)" rows={2}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              <input value={recordedBy} onChange={(e) => setRecordedBy(e.target.value)} placeholder="Recorded by *"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white" />
              <button onClick={submitHcp} disabled={busy || !specialty.trim() || !recordedBy.trim()}
                className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-semibold">
                Save response
              </button>
            </div>
          )}

          <div className="space-y-3">
            {hcpEntries.map((entry) => (
              <div key={entry.id} className={`${card} flex items-start justify-between gap-3`}>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white">{entry.specialty}</span>
                    {entry.respondent_code && <span className="text-slate-400">· {entry.respondent_code}</span>}
                  </div>
                  <div className="flex gap-3 text-slate-500 dark:text-slate-400">
                    {entry.cost_barrier_rating !== null && <span>Cost barrier: {entry.cost_barrier_rating}/10</span>}
                    {entry.molecule_preference_rating !== null && <span>Preference: {entry.molecule_preference_rating}/5</span>}
                    {entry.efficacy_rating !== null && <span>Efficacy: {entry.efficacy_rating}/5</span>}
                    {entry.switch_intent !== null && <span>{entry.switch_intent ? 'Would switch' : 'Would not switch'}</span>}
                  </div>
                  {entry.key_quote && <p className="text-slate-600 dark:text-slate-300 italic">"{entry.key_quote}"</p>}
                  <p className="text-slate-400 dark:text-slate-500">{entry.recorded_by} · {entry.recorded_at}</p>
                </div>
                <button onClick={() => deleteHCPQuestionnaire(entry.id).then(refresh)} className="text-slate-400 hover:text-red-500 shrink-0">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
