'use client';

import React from 'react';
import { ShieldCheck, Building2, CalendarClock, Users, Info } from 'lucide-react';
import { MoleculeLifecycle } from '../lib/types';

const card =
  'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

export default function LifecyclePanel({ data }: { data: MoleculeLifecycle }) {
  return (
    <div className="space-y-6">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-600 dark:text-brand-400">
          Module 11: Patent, Exclusivity &amp; Competitive Entry
        </span>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
          {data.display_name}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{data.coverage_note}</p>
        {data.is_combination && (
          <p className="text-[11px] text-slate-400 mt-1">
            Fixed-dose combination · matched on {data.components.join(' + ')}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className={card}>
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="w-4 h-4 text-brand-500" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500">Innovator</span>
          </div>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {data.innovator_brand || 'Not listed'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {data.innovator_company || 'No FDA-listed innovator application'}
          </p>
          {data.innovator_application && (
            <p className="text-[11px] font-mono text-slate-400 mt-1">
              {data.innovator_application} · approved {data.first_approval_date}
            </p>
          )}
        </div>

        <div className={card}>
          <div className="flex items-center gap-2 mb-2">
            <CalendarClock className="w-4 h-4 text-amber-500" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500">Patent runway</span>
          </div>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {data.latest_patent_expiry || 'No listed patents'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Latest of {data.patents.length} listed patent{data.patents.length === 1 ? '' : 's'}
          </p>
        </div>

        <div className={card}>
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-emerald-500" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500">Generic entry</span>
          </div>
          <p className="text-sm font-bold text-slate-900 dark:text-white">
            {data.generic_entrant_count} approved filer{data.generic_entrant_count === 1 ? '' : 's'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {data.first_generic_approval_date
              ? `First approval ${data.first_generic_approval_date}`
              : 'No generic approvals on record'}
          </p>
        </div>
      </div>

      {data.exclusivity.length > 0 && (
        <div className={card}>
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-4 h-4 text-brand-500" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500">Exclusivity</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.exclusivity.map((item, i) => (
              <span
                key={`${item.code}-${i}`}
                className="px-2.5 py-1 rounded-lg text-[11px] bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300"
                title={item.description || undefined}
              >
                <span className="font-mono font-semibold">{item.code}</span> · {item.expiry_date}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.patents.length > 0 && (
        <div className={card}>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500 block mb-3">
            Listed patents (latest expiry first)
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <th className="p-2 font-mono font-normal">Patent</th>
                  <th className="p-2 font-mono font-normal">Expires</th>
                  <th className="p-2 font-mono font-normal">Type</th>
                  <th className="p-2 font-mono font-normal">Use code</th>
                </tr>
              </thead>
              <tbody className="text-slate-600 dark:text-slate-300">
                {data.patents.slice(0, 25).map((p, i) => (
                  <tr key={`${p.patent_number}-${i}`} className="border-b border-slate-100 dark:border-slate-850">
                    <td className="p-2 font-mono">{p.patent_number}</td>
                    <td className="p-2 font-semibold text-slate-900 dark:text-white">{p.expiry_date}</td>
                    <td className="p-2">
                      {[p.drug_substance && 'Substance', p.drug_product && 'Product']
                        .filter(Boolean)
                        .join(' + ') || 'Method of use'}
                    </td>
                    <td className="p-2 font-mono text-slate-400">{p.use_code || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.generic_entrants.length > 0 && (
        <div className={card}>
          <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-500 block mb-3">
            Approved generic filers
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <th className="p-2 font-mono font-normal">Brand</th>
                  <th className="p-2 font-mono font-normal">Company</th>
                  <th className="p-2 font-mono font-normal">Strength</th>
                  <th className="p-2 font-mono font-normal">Approved</th>
                </tr>
              </thead>
              <tbody className="text-slate-600 dark:text-slate-300">
                {data.generic_entrants.slice(0, 30).map((g, i) => (
                  <tr key={`${g.application_number}-${i}`} className="border-b border-slate-100 dark:border-slate-850">
                    <td className="p-2 font-semibold text-slate-900 dark:text-white">{g.trade_name}</td>
                    <td className="p-2">{g.applicant_full_name || g.applicant}</td>
                    <td className="p-2 font-mono text-slate-400">{g.strength || '—'}</td>
                    <td className="p-2">{g.approval_date || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/30 space-y-2">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-amber-500 shrink-0" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Not available from public sources
          </span>
        </div>
        <ul className="pl-6 space-y-1">
          {data.unavailable.map((item, i) => (
            <li key={i} className="text-[11px] text-slate-500 dark:text-slate-400 list-disc leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
        {data.data_sources.length > 0 && (
          <p className="pl-6 text-[11px] text-slate-400">Source: {data.data_sources.join('; ')}</p>
        )}
      </div>
    </div>
  );
}
