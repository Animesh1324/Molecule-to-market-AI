'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { FileUp, Loader2, Trash2, Download, AlertTriangle, Database, CheckCircle2 } from 'lucide-react';
import {
  deleteUpload,
  fetchMarketDatasets,
  fetchUploads,
  getUploadDownloadUrl,
  uploadSecondaryData,
} from '../lib/api';
import { MarketDataset, UploadedFile } from '../lib/types';

const ACCEPT =
  '.csv,.tsv,.xlsx,.xls,.pdf,.docx,.doc,.pptx,.ppt,.txt,.json,.png,.jpg,.jpeg';

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function SecondaryDataUploader({ projectId }: { projectId: string }) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState('');
  // Datasets that were recognised as market extracts and parsed into the
  // competitor tables. Shown here so a user can see an upload actually became
  // usable data rather than just another stored attachment.
  const [datasets, setDatasets] = useState<MarketDataset[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setFiles(await fetchUploads(projectId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not list uploaded files.');
    }
    // Dataset listing is best-effort: a failure here must not mask the file
    // list, which is the primary content of this panel.
    try {
      setDatasets(await fetchMarketDatasets());
    } catch {
      setDatasets([]);
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Market ingestion runs in the background after the upload responds, so a
  // freshly dropped extract is not in the dataset list yet. Poll briefly while
  // one is pending rather than making the user reload.
  useEffect(() => {
    const pending = files.some((f) => f.market_ingest === 'queued'
      && !datasets.some((d) => d.upload_file_id === f.id || d.original_filename === f.original_filename));
    if (!pending) return;
    const timer = setInterval(() => {
      fetchMarketDatasets().then(setDatasets).catch(() => undefined);
    }, 4000);
    return () => clearInterval(timer);
  }, [files, datasets]);

  const handleFiles = useCallback(
    async (incoming: FileList | null) => {
      if (!incoming || incoming.length === 0) return;
      setBusy(true);
      setError(null);
      try {
        // Sequential rather than parallel so one rejected file gives a clear
        // message instead of a race of competing errors.
        for (const file of Array.from(incoming)) {
          await uploadSecondaryData(projectId, file, note || undefined);
        }
        setNote('');
        await refresh();
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Upload failed.');
      } finally {
        setBusy(false);
        if (inputRef.current) inputRef.current.value = '';
      }
    },
    [projectId, note, refresh]
  );

  return (
    <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
      <div>
        <span className="text-xs font-mono uppercase tracking-wider text-brand-600 dark:text-brand-400 block">
          Secondary Data
        </span>
        <p className="text-xs text-slate-500 dark:text-slate-500 dark:text-slate-400 mt-1">
          Attach the data no public source carries — IQVIA/AWACS extracts, internal price
          lists, market research. Stored against this project.
        </p>
      </div>

      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Optional: what is this file? (e.g. AWACS MAT Jun-25 extract)"
        className="w-full px-3 py-2 rounded-lg text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 placeholder:text-slate-400"
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click();
        }}
        className={`flex flex-col items-center justify-center gap-2 py-8 px-4 rounded-xl border-2 border-dashed cursor-pointer transition-colors ${
          dragging
            ? 'border-brand-500 bg-brand-500/10'
            : 'border-slate-300 dark:border-slate-700 hover:border-brand-500'
        }`}
      >
        {busy ? (
          <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        ) : (
          <FileUp className="w-6 h-6 text-slate-400" />
        )}
        <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">
          {busy ? 'Uploading…' : 'Drop files here, or click to browse'}
        </p>
        <p className="text-[11px] text-slate-400">
          CSV, Excel, PDF, Word, PowerPoint, images — up to 25 MB each
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {error && (
        <p className="flex items-start gap-1.5 text-xs text-red-500">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      )}

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file) => (
            <li
              key={file.id}
              className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800"
            >
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">
                  {file.original_filename}
                </p>
                <p className="text-[11px] text-slate-400">
                  {formatSize(file.size_bytes)} · {file.uploaded_at}
                  {file.note ? ` · ${file.note}` : ''}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <a
                  href={getUploadDownloadUrl(projectId, file.id)}
                  className="p-1.5 rounded-md text-slate-400 hover:text-brand-500"
                  title="Download"
                >
                  <Download className="w-3.5 h-3.5" />
                </a>
                <button
                  type="button"
                  title="Delete"
                  onClick={async () => {
                    try {
                      await deleteUpload(projectId, file.id);
                      await refresh();
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Delete failed.');
                    }
                  }}
                  className="p-1.5 rounded-md text-slate-400 hover:text-red-500"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Parsed market datasets. Their presence is what makes the competitor
          and market panels work, so it is stated explicitly rather than left
          for the user to infer from another screen. */}
      {datasets.length > 0 && (
        <div className="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
          <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
            <Database className="w-3 h-3" aria-hidden />
            Parsed into market intelligence
          </div>
          <ul className="space-y-1.5">
            {datasets.map((dataset) => (
              <li
                key={dataset.id}
                className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/60"
              >
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">
                      {dataset.original_filename}
                    </p>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 tabular-nums">
                      {dataset.brand_count.toLocaleString()} brands ·{' '}
                      {dataset.molecule_count.toLocaleString()} molecules ·{' '}
                      {dataset.company_count.toLocaleString()} companies
                    </p>
                    <p className="text-[10px] font-mono text-slate-500 dark:text-slate-500 mt-0.5">
                      {dataset.market} · {dataset.period_label || 'period not stated'} ·{' '}
                      {dataset.total_value.toLocaleString()} {dataset.value_unit}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
