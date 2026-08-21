'use client';

import React from 'react';
import { ExternalLink, AlertTriangle, Info } from 'lucide-react';
import { CDSCOIntelligence } from '../lib/types';

const card =
  'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

export default function CDSCOPanel({ data }: { data: CDSCOIntelligence }) {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-700 dark:text-brand-400">
          Module 14: India Regulatory (CDSCO) Checklist
        </span>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
          {data.display_name}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          {data.blocking_steps.length} of {data.checklist.length} steps block launch if unresolved.
        </p>
      </div>

      <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/30 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
        <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
          {data.india_specific_warning}
        </p>
      </div>

      <div className="space-y-3">
        {data.checklist.map((item, index) => (
          <div key={item.step} className={card}>
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-start gap-3 min-w-0">
                <span className="font-mono text-xs text-slate-400 shrink-0 mt-0.5">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">{item.step}</h3>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {item.source_register}
                  </p>
                </div>
              </div>
              {item.blocks_launch && (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-red-500/10 text-red-600 dark:text-red-400 shrink-0">
                  BLOCKS LAUNCH
                </span>
              )}
            </div>

            <div className="pl-8 space-y-2">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  What to check
                </span>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {item.what_to_check}
                </p>
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  Why it matters
                </span>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  {item.why_it_matters}
                </p>
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-mono border border-slate-200 dark:border-slate-700 text-slate-500 hover:border-brand-500 hover:text-brand-500 transition-colors"
              >
                Open register
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-start gap-2">
        <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
          {data.automation_note}
        </p>
      </div>
    </div>
  );
}
