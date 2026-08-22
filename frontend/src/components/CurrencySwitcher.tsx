'use client';

import { useState } from 'react';
import { IndianRupee, ChevronDown } from 'lucide-react';
import { useCurrency } from './CurrencyProvider';
import { CurrencyDisplay } from '../lib/currency';

const OPTIONS: { value: CurrencyDisplay; label: string; hint: string }[] = [
  { value: 'inr-cr', label: '₹ Crore / Lakh', hint: 'Large figures as ₹X.X Cr / ₹X.X L' },
  { value: 'inr-plain', label: '₹ Rupees', hint: 'Indian digit grouping, e.g. ₹1,23,45,678' },
  { value: 'usd', label: '$ US Dollars', hint: `Converted at a fixed planning rate` },
];

/** Global currency-display switch — a display convention, not a live FX
 * feed. Every underlying figure is unchanged; this only changes how it's
 * written, same as the theme toggle changes colours, not content.
 */
export default function CurrencySwitcher() {
  const { display, setDisplay } = useCurrency();
  const [open, setOpen] = useState(false);
  const current = OPTIONS.find((o) => o.value === display) || OPTIONS[0];

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title="Currency display"
        className="flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
      >
        <IndianRupee className="w-3.5 h-3.5" aria-hidden />
        <span className="hidden sm:inline">{current.label}</span>
        <ChevronDown className="w-3 h-3" aria-hidden />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-64 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl z-50 overflow-hidden">
            {OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  setDisplay(opt.value);
                  setOpen(false);
                }}
                className={`w-full text-left px-3.5 py-2.5 text-xs transition ${
                  opt.value === display
                    ? 'bg-brand-50 dark:bg-brand-950/40 text-brand-800 dark:text-brand-300'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-200'
                }`}
              >
                <div className="font-semibold">{opt.label}</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{opt.hint}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
