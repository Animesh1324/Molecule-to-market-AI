'use client';

import React, { useState } from 'react';
import { Sparkles, ExternalLink, ShieldCheck, AlertTriangle, Wand2, Plus, Loader2 } from 'lucide-react';
import { BrandNameCandidates } from '../lib/types';

const card =
  'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

interface Props {
  data: BrandNameCandidates;
  onGenerate?: (requirement: string) => void;
  onMoreOptions?: () => void;
  loading?: boolean;
}

export default function BrandNamesPanel({ data, onGenerate, onMoreOptions, loading }: Props) {
  const [requirement, setRequirement] = useState(data.requirement_applied || '');

  return (
    <div className="space-y-6">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-700 dark:text-brand-400">
          Module 13: Brand Name Generation &amp; Screening
        </span>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
          Candidate names for {data.molecule}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{data.screening_basis}</p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
          For phonetic collision checks against real competitor brands in the loaded market extract instead of the FDA Orange Book, see Module 12: Trademark &amp; Naming.
        </p>
        {data.ai_generated && (
          <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400">
            <Sparkles className="w-3 h-3" /> AI-drafted to your requirement, screened against the Orange Book
          </span>
        )}
      </div>

      {onGenerate && (
        <div className={`${card} flex flex-col sm:flex-row gap-3 items-stretch sm:items-center`}>
          <input
            type="text"
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            placeholder="Naming requirement, e.g. &quot;should evoke once-weekly convenience, premium sound, under 8 letters&quot;"
            className="flex-1 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white placeholder:text-slate-400"
          />
          <button
            onClick={() => onGenerate(requirement)}
            disabled={loading || !requirement.trim()}
            className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold whitespace-nowrap"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            Generate with AI
          </button>
        </div>
      )}

      {data.candidates.length === 0 ? (
        <div className={card}>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            No candidates were generated. The FDA Orange Book index may still be loading —
            retry in a moment.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.candidates.map((candidate) => {
            const caution = candidate.phonetic_collision_with_marketed_brand;
            return (
              <div key={candidate.name} className={card}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    {candidate.name}
                    {candidate.ai_generated && <Sparkles className="w-3.5 h-3.5 text-brand-500" />}
                  </h3>
                  <span
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold shrink-0 ${
                      caution
                        ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                        : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                    }`}
                  >
                    {caution ? (
                      <AlertTriangle className="w-3 h-3" />
                    ) : (
                      <ShieldCheck className="w-3 h-3" />
                    )}
                    {caution ? 'Sounds close' : 'Clear'}
                  </span>
                </div>

                <p className="text-[11px] font-mono text-slate-400 mb-2">
                  {candidate.length} characters · {candidate.syllable_estimate} syllables ·{' '}
                  {candidate.construction}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-3">
                  {candidate.rationale}
                </p>

                <div className="flex flex-wrap gap-2">
                  {[
                    { label: 'IP India', url: candidate.ip_india_search_url },
                    { label: 'USPTO', url: candidate.uspto_search_url },
                    { label: 'WIPO', url: candidate.wipo_search_url },
                  ].map((link) => (
                    <a
                      key={link.label}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-mono border border-slate-200 dark:border-slate-700 text-slate-500 hover:border-brand-500 hover:text-brand-500 transition-colors"
                    >
                      {link.label}
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {onMoreOptions && data.candidates.length > 0 && (
        <div className="flex justify-center">
          <button
            onClick={onMoreOptions}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-brand-500 hover:text-brand-500 disabled:opacity-50 text-sm font-semibold text-slate-600 dark:text-slate-300 transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            More options
          </button>
        </div>
      )}

      <div className="p-4 rounded-2xl bg-brand-500/5 border border-brand-500/30 flex items-start gap-2">
        <Sparkles className="w-4 h-4 text-brand-500 shrink-0 mt-0.5" />
        <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
          {data.next_step}
        </p>
      </div>
    </div>
  );
}
