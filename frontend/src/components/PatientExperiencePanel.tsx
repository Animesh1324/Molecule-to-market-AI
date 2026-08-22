'use client';

import React from 'react';
import { Activity, AlertTriangle, Users, Info } from 'lucide-react';
import { PatientExperience } from '../lib/types';

const card =
  'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

export default function PatientExperiencePanel({ data }: { data: PatientExperience }) {
  const maxCount = data.top_reported_problems[0]?.report_count || 1;

  return (
    <div className="space-y-6">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-700 dark:text-brand-400">
          Module 7: Real-World Patient Experience
        </span>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
          {data.display_name}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{data.coverage_note}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {[
          { label: 'Total reports', value: data.total_reports, icon: Activity, tone: 'text-brand-500' },
          { label: 'Coded serious', value: data.serious_reports, icon: AlertTriangle, tone: 'text-amber-500' },
          { label: 'Non-serious', value: data.non_serious_reports, icon: Users, tone: 'text-emerald-500' },
        ].map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className={card}>
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${tone}`} />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-500">{label}</span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {value.toLocaleString()}
            </p>
          </div>
        ))}
      </div>

      {data.top_reported_problems.length > 0 && (
        <div className={card}>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block mb-4">
            Most reported problems
          </span>
          <div className="space-y-2.5">
            {data.top_reported_problems.slice(0, 12).map((problem) => (
              <div key={problem.term} className="space-y-1">
                <div className="flex items-baseline justify-between gap-3 text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-200 truncate">
                    {problem.term}
                  </span>
                  <span className="font-mono text-slate-500 shrink-0">
                    {problem.report_count.toLocaleString()} · {problem.share_of_reports.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${Math.max(2, (problem.report_count / maxCount) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.adherence_considerations.length > 0 && (
        <div className={card}>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block mb-3">
            Adherence considerations
          </span>
          <ul className="space-y-2">
            {data.adherence_considerations.map((note, i) => (
              <li key={i} className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed list-disc ml-4">
                {note}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {[
          { title: 'Age distribution', rows: data.age_distribution },
          { title: 'Sex distribution', rows: data.sex_distribution },
        ]
          .filter((g) => g.rows.length > 0)
          .map((group) => (
            <div key={group.title} className={card}>
              <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block mb-3">
                {group.title}
              </span>
              <div className="space-y-1.5">
                {group.rows.slice(0, 6).map((row) => (
                  <div key={row.label} className="flex justify-between text-xs">
                    <span className="text-slate-600 dark:text-slate-300">{row.label}</span>
                    <span className="font-mono text-slate-500">{row.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
      </div>

      {/* The caveat travels with the data: report counts are not incidence. */}
      <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/30 space-y-2">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-amber-500 shrink-0" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-600 dark:text-slate-300">
            How to read these numbers
          </span>
        </div>
        <p className="pl-6 text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
          {data.interpretation_caveat}
        </p>
        <p className="pl-6 text-[11px] text-slate-400">Source: {data.data_sources.join('; ')}</p>
      </div>
    </div>
  );
}
