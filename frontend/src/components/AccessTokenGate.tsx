'use client';

import React, { useEffect, useState } from 'react';
import { KeyRound, Check } from 'lucide-react';
import { getAccessToken, setAccessToken } from '../lib/api';

/**
 * Entry point for the API access token.
 *
 * When the backend runs with API_ACCESS_TOKEN set, every call returns 401 until
 * the token is supplied. It is held in localStorage rather than a cookie so it
 * is never sent automatically to any other origin.
 */
export default function AccessTokenGate() {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState('');
  const [saved, setSaved] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(getAccessToken()));
  }, []);

  const save = () => {
    setAccessToken(value.trim());
    setHasToken(Boolean(value.trim()));
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      setOpen(false);
      window.location.reload();
    }, 600);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title={hasToken ? 'API token saved' : 'Set API access token'}
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border transition-colors ${
          hasToken
            ? 'border-emerald-500/40 text-emerald-500'
            : 'border-slate-300 dark:border-slate-700 text-slate-500 dark:text-slate-500 hover:border-brand-500'
        }`}
      >
        <KeyRound className="w-3.5 h-3.5" />
        <span className="text-[11px] font-mono uppercase tracking-wider hidden sm:inline">
          {hasToken ? 'Authorised' : 'Token'}
        </span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-xl z-50 space-y-3">
          <div>
            <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">API access token</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-500 dark:text-slate-400 mt-1">
              Required when the backend runs with <code className="font-mono">API_ACCESS_TOKEN</code> set.
              Stored in this browser only.
            </p>
          </div>
          <input
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && save()}
            placeholder="Paste token"
            autoComplete="off"
            className="w-full px-3 py-2 rounded-lg text-xs font-mono bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={save}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold"
            >
              {saved ? <Check className="w-3.5 h-3.5" /> : null}
              {saved ? 'Saved' : 'Save token'}
            </button>
            {hasToken && (
              <button
                type="button"
                onClick={() => {
                  setAccessToken('');
                  setHasToken(false);
                  setValue('');
                  window.location.reload();
                }}
                className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-500 dark:text-slate-500 text-xs"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
