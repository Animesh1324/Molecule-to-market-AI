'use client';

/**
 * Team-attested competitors for a molecule a licensed extract doesn't cover
 * — a brand a team knows is real and marketed, newer than the loaded
 * extract's period, or in a market no extract has ever been loaded for.
 *
 * Deliberately kept visually and structurally separate from the measured
 * market data above it: every entry requires a stated source, is displayed
 * with who added it and when, and is never folded into the audited market
 * size or share figures. This is an attestation, not an audit finding.
 */

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Plus, Trash2, UserCheck } from 'lucide-react';
import {
  addManualCompetitor,
  deleteManualCompetitor,
  fetchManualCompetitors,
  ManualCompetitor,
} from '../lib/api';

interface Props {
  moleculeName: string;
  currentUser?: string;
}

export default function ManualCompetitorPanel({ moleculeName, currentUser }: Props) {
  const [entries, setEntries] = useState<ManualCompetitor[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [brand, setBrand] = useState('');
  const [company, setCompany] = useState('');
  const [sourceNote, setSourceNote] = useState('');
  const [addedBy, setAddedBy] = useState(currentUser || '');

  // Trade pricing is a separate, optional block: MRP can come from a retail
  // listing, but PTR/PTS are confidential distribution terms almost never
  // knowable for a competitor's brand, so this stays collapsed by default
  // rather than implying it's routinely fillable.
  const [showPricing, setShowPricing] = useState(false);
  const [mrp, setMrp] = useState('');
  const [ptr, setPtr] = useState('');
  const [pts, setPts] = useState('');
  const [priceUnit, setPriceUnit] = useState('');

  const refresh = useCallback(async () => {
    try {
      setEntries(await fetchManualCompetitors(moleculeName));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load manual competitors.');
    }
  }, [moleculeName]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleAdd = async () => {
    if (!brand.trim() || !sourceNote.trim() || !addedBy.trim()) {
      setError('Brand, source, and your name are all required — an entry with no stated source is a guess.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await addManualCompetitor({
        molecule: moleculeName,
        brand: brand.trim(),
        company: company.trim() || undefined,
        source_note: sourceNote.trim(),
        added_by: addedBy.trim(),
        mrp: mrp ? parseFloat(mrp) : undefined,
        ptr: ptr ? parseFloat(ptr) : undefined,
        pts: pts ? parseFloat(pts) : undefined,
        price_unit: priceUnit.trim() || undefined,
      });
      setBrand('');
      setCompany('');
      setSourceNote('');
      setMrp('');
      setPtr('');
      setPts('');
      setPriceUnit('');
      setShowForm(false);
      setShowPricing(false);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add this competitor.');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteManualCompetitor(id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed.');
    }
  };

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-amber-600 dark:text-amber-400" aria-hidden />
            Team-attested competitors
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
            For a brand you know is real that the loaded extract doesn't cover — never counted into the measured market size above.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs font-semibold hover:bg-amber-100 dark:hover:bg-amber-950/50 transition"
        >
          <Plus className="w-3.5 h-3.5" aria-hidden />
          {showForm ? 'Cancel' : 'Add a competitor'}
        </button>
      </div>

      {showForm && (
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 space-y-2.5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <input
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="Brand name *"
              className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
            />
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company"
              className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
            />
          </div>
          <textarea
            value={sourceNote}
            onChange={(e) => setSourceNote(e.target.value)}
            placeholder="Source — where does this come from? *  (required: an entry with no stated source is indistinguishable from a guess)"
            rows={2}
            className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
          />
          <input
            value={addedBy}
            onChange={(e) => setAddedBy(e.target.value)}
            placeholder="Your name *"
            className="w-full sm:w-64 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
          />

          <button
            type="button"
            onClick={() => setShowPricing((v) => !v)}
            className="text-xs font-semibold text-amber-700 dark:text-amber-400 hover:underline"
          >
            {showPricing ? '− Hide trade pricing' : '+ Add trade pricing (optional)'}
          </button>

          {showPricing && (
            <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-2.5">
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                MRP can usually be checked on a retail pharmacy listing. PTR and PTS are confidential
                terms in this competitor&apos;s own distribution agreements — no public source carries
                them. Leave blank unless a team contact has genuinely told you one.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                <input
                  type="number"
                  min={0}
                  value={mrp}
                  onChange={(e) => setMrp(e.target.value)}
                  placeholder="MRP"
                  className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
                />
                <input
                  type="number"
                  min={0}
                  value={ptr}
                  onChange={(e) => setPtr(e.target.value)}
                  placeholder="PTR (rarely known)"
                  className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
                />
                <input
                  type="number"
                  min={0}
                  value={pts}
                  onChange={(e) => setPts(e.target.value)}
                  placeholder="PTS (rarely known)"
                  className="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
                />
              </div>
              <input
                value={priceUnit}
                onChange={(e) => setPriceUnit(e.target.value)}
                placeholder='What are these per? e.g. "per strip of 10 tablets"'
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100"
              />
            </div>
          )}

          <button
            type="button"
            onClick={handleAdd}
            disabled={busy}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-60 text-white text-sm font-semibold transition"
          >
            {busy ? 'Adding…' : 'Add competitor'}
          </button>
        </div>
      )}

      {error && (
        <div className="mx-4 mt-3 p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-300 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" aria-hidden />
          {error}
        </div>
      )}

      <div className="p-4">
        {entries.length === 0 ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            No team-attested competitors on file for this molecule.
          </p>
        ) : (
          <ul className="space-y-2">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/60 flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{entry.brand}</span>
                    {entry.company && (
                      <span className="text-xs text-slate-600 dark:text-slate-400">{entry.company}</span>
                    )}
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                      manual · unaudited
                    </span>
                  </div>
                  {(entry.mrp || entry.ptr || entry.pts) && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {entry.mrp != null && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                          MRP ₹{entry.mrp.toLocaleString('en-IN')}
                        </span>
                      )}
                      {entry.ptr != null && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                          PTR ₹{entry.ptr.toLocaleString('en-IN')}
                        </span>
                      )}
                      {entry.pts != null && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                          PTS ₹{entry.pts.toLocaleString('en-IN')}
                        </span>
                      )}
                      {entry.price_unit && (
                        <span className="text-[10px] text-slate-400 dark:text-slate-500 self-center">{entry.price_unit}</span>
                      )}
                    </div>
                  )}
                  <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">{entry.source_note}</p>
                  <p className="text-[10px] font-mono text-slate-400 dark:text-slate-500 mt-1">
                    Added by {entry.added_by} · {entry.added_at}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(entry.id)}
                  className="p-1.5 rounded-md text-slate-400 hover:text-rose-500 shrink-0"
                  title="Remove"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
