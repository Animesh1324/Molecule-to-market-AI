'use client';

import React, { useCallback, useEffect, useState } from 'react';
import {
  Search,
  Loader2,
  AlertTriangle,
  ExternalLink,
  GitCompareArrows,
  Sparkles,
  FileText,
} from 'lucide-react';
import {
  compareDrugs,
  fetchPMTAnalysis,
  searchDrugs,
} from '../lib/api';
import { DrugComparison, DrugOut, DrugSearchResult, PMTAnalysis } from '../lib/types';

const card =
  'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

const NARRATIVE_FIELDS: Array<{ key: keyof DrugOut; label: string }> = [
  { key: 'mechanism', label: 'Mechanism of action' },
  { key: 'indications', label: 'Indications' },
  { key: 'dosage', label: 'Dosage' },
  { key: 'contraindications', label: 'Contraindications' },
  { key: 'warnings', label: 'Warnings' },
  { key: 'adverse_effects', label: 'Adverse effects' },
  { key: 'drug_interactions', label: 'Drug interactions' },
  { key: 'pregnancy_information', label: 'Pregnancy' },
  { key: 'lactation_information', label: 'Lactation' },
];

type Tab = 'search' | 'compare' | 'pmt';

export default function DrugIntelligencePanel({ defaultMolecule }: { defaultMolecule: string }) {
  const [tab, setTab] = useState<Tab>('search');

  const [query, setQuery] = useState(defaultMolecule);
  const [result, setResult] = useState<DrugSearchResult | null>(null);
  const [selected, setSelected] = useState<DrugOut | null>(null);

  const [drugA, setDrugA] = useState(defaultMolecule);
  const [drugB, setDrugB] = useState('');
  const [comparison, setComparison] = useState<DrugComparison | null>(null);

  const [pmt, setPmt] = useState<PMTAnalysis | null>(null);
  const [competitors, setCompetitors] = useState('');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (task: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await task();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed.');
    } finally {
      setBusy(false);
    }
  }, []);

  const doSearch = useCallback(
    (term: string) =>
      run(async () => {
        const found = await searchDrugs(term);
        setResult(found);
        setSelected(found.items[0] ?? null);
      }),
    [run]
  );

  // Seed with the project's molecule so the panel is useful on open.
  useEffect(() => {
    if (defaultMolecule) doSearch(defaultMolecule);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultMolecule]);

  return (
    <div className="space-y-6">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-700 dark:text-brand-400">
          Module 15: Drug Intelligence
        </span>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
          Drug database, comparison &amp; PMT analysis
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Normalised records from permitted sources, cached locally. Every fact carries its
          source; generated analysis is kept on its own tab.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {([
          { id: 'search', label: 'Search & profile', icon: Search },
          { id: 'compare', label: 'Compare', icon: GitCompareArrows },
          { id: 'pmt', label: 'PMT analysis', icon: Sparkles },
        ] as Array<{ id: Tab; label: string; icon: typeof Search }>).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              tab === id
                ? 'bg-brand-600 text-white'
                : 'border border-slate-200 dark:border-slate-700 text-slate-500 hover:border-brand-500'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      {error && (
        <p className="flex items-start gap-1.5 text-xs text-red-500">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      )}

      {tab === 'search' && (
        <div className="space-y-5">
          <div className="flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doSearch(query)}
              placeholder="Brand, generic, ingredient, class (GLP-1), strength, or form"
              className="flex-1 px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200"
            />
            <button
              type="button"
              onClick={() => doSearch(query)}
              disabled={busy}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              Search
            </button>
          </div>

          {result && (
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              {result.note}
              {result.matched_on !== 'no match' && ` Matched on ${result.matched_on}.`}
            </p>
          )}

          {result && result.items.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {result.items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelected(item)}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                    selected?.id === item.id
                      ? 'bg-brand-600 text-white'
                      : 'border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-brand-500'
                  }`}
                >
                  {item.brand_name || item.generic_name}
                </button>
              ))}
            </div>
          )}

          {selected && (
            <div className="space-y-4">
              <div className={card}>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {selected.brand_name || selected.generic_name}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {selected.generic_name}
                  {selected.manufacturer ? ` · ${selected.manufacturer}` : ''}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  {[
                    { label: 'Class', value: selected.drug_class },
                    { label: 'Routes', value: selected.routes.join(', ') },
                    { label: 'Forms', value: selected.dosage_forms.slice(0, 3).join(', ') },
                    { label: 'Strengths', value: selected.strengths.slice(0, 3).join(', ') },
                  ].map((f) => (
                    <div key={f.label}>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                        {f.label}
                      </span>
                      <span className="text-xs text-slate-700 dark:text-slate-200">
                        {f.value || 'Not available'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {NARRATIVE_FIELDS.map(({ key, label }) => {
                const value = selected[key] as string | null | undefined;
                if (!value) return null;
                return (
                  <details key={key} className={card}>
                    <summary className="text-xs font-mono uppercase tracking-wider text-slate-500 cursor-pointer">
                      {label}
                    </summary>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mt-3 whitespace-pre-wrap">
                      {value}
                    </p>
                  </details>
                );
              })}

              {/* Provenance is always shown: no fact without its source. */}
              <div className={card}>
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-brand-500" />
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500">
                    Sources
                  </span>
                </div>
                {selected.sources.map((source) => (
                  <div key={source.source_name} className="flex items-center justify-between gap-2 text-xs">
                    <span className="text-slate-700 dark:text-slate-200">
                      {source.source_name}
                      <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500">
                        {source.confidence}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 text-slate-400 font-mono text-[10px]">
                      {source.retrieved_at}
                      {source.source_url && (
                        <a href={source.source_url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="w-3 h-3 hover:text-brand-500" />
                        </a>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'compare' && (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <input
              value={drugA}
              onChange={(e) => setDrugA(e.target.value)}
              placeholder="Drug A"
              className="flex-1 min-w-[140px] px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200"
            />
            <input
              value={drugB}
              onChange={(e) => setDrugB(e.target.value)}
              placeholder="Drug B (e.g. tirzepatide)"
              className="flex-1 min-w-[140px] px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200"
            />
            <button
              type="button"
              disabled={busy || !drugA || !drugB}
              onClick={() => run(async () => setComparison(await compareDrugs(drugA, drugB)))}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitCompareArrows className="w-3.5 h-3.5" />}
              Compare
            </button>
          </div>

          {comparison && (
            <>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                {comparison.comparison_note}
              </p>
              <div className={`${card} overflow-x-auto`}>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                      <th className="p-2 font-mono font-normal">Field</th>
                      <th className="p-2 font-mono font-normal">{drugA}</th>
                      <th className="p-2 font-mono font-normal">{drugB}</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-600 dark:text-slate-300 align-top">
                    {comparison.fields.map((f) => (
                      <tr key={f.field} className="border-b border-slate-100 dark:border-slate-850">
                        <td className="p-2 font-semibold text-slate-700 dark:text-slate-200 whitespace-nowrap">
                          {f.label}
                        </td>
                        <td className="p-2 max-w-xs">{(f.drug_a_value || '').slice(0, 220)}</td>
                        <td className="p-2 max-w-xs">{(f.drug_b_value || '').slice(0, 220)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/30">
                <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                  {comparison.caveat}
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'pmt' && (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            <input
              value={competitors}
              onChange={(e) => setCompetitors(e.target.value)}
              placeholder="Competitors, comma separated (optional)"
              className="flex-1 min-w-[180px] px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200"
            />
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                run(async () => setPmt(await fetchPMTAnalysis(defaultMolecule, competitors)))
              }
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Build analysis
            </button>
          </div>

          {pmt && (
            <>
              {/* Labelled unmistakably: this is generated, not a source fact. */}
              <div className="p-4 rounded-2xl bg-brand-500/5 border border-brand-500/30 space-y-1">
                <span className="text-xs font-mono uppercase tracking-wider text-brand-600 dark:text-brand-400">
                  {pmt.analysis_type}
                </span>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                  {pmt.disclaimer}
                </p>
              </div>

              {([
                ['Positioning observations', pmt.positioning_observations],
                ['Differentiation candidates', pmt.differentiation_candidates],
                ['Competitive advantages', pmt.competitive_advantages],
                ['Competitive disadvantages', pmt.competitive_disadvantages],
                ['Target patient segment', pmt.target_patient_segment],
                ['Target physician segment', pmt.target_physician_segment],
                ['Evidence gaps', pmt.evidence_gaps],
              ] as Array<[string, string[]]>)
                .filter(([, items]) => items.length > 0)
                .map(([title, items]) => (
                  <div key={title} className={card}>
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block mb-2">
                      {title}
                    </span>
                    <ul className="space-y-1.5">
                      {items.map((item, i) => (
                        <li
                          key={i}
                          className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed list-disc ml-4"
                        >
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
