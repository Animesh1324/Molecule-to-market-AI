'use client';

import React, { useState } from 'react';
import { Sparkles, Copy, Check, Wand2, Loader2, ImageIcon } from 'lucide-react';
import { VisualAidBrief } from '../lib/types';

const card = 'p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800';

interface Props {
  brief: VisualAidBrief | null;
  onGenerate: () => void;
  loading?: boolean;
}

export default function VisualAidBriefPanel({ brief, onGenerate, loading }: Props) {
  const [copied, setCopied] = useState(false);

  const copyPrompt = async () => {
    if (!brief) return;
    try {
      await navigator.clipboard.writeText(brief.image_generation_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable — the prompt is still visible to select manually.
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-brand-500" />
            Visual Aid Brief &amp; Image-Generation Prompt
          </h3>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            8-element single-page detail-aid anatomy. Paste the prompt below into ChatGPT
            (image generation), Gemini &quot;nano banana&quot;, or Canva Magic Media to render the visual.
          </p>
        </div>
        <button
          onClick={onGenerate}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-semibold whitespace-nowrap"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
          {brief ? 'Regenerate' : 'Generate Visual Aid Brief'}
        </button>
      </div>

      {brief && (
        <>
          {brief.ai_drafted && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <Sparkles className="w-3 h-3" /> AI-drafted, compliance-screened
            </span>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">1–2. Indication &amp; Brand</span>
              <p className="text-slate-600 dark:text-slate-300">{brief.main_indication}</p>
              <p className="text-slate-500 dark:text-slate-400">{brief.brand_and_pack_shot}</p>
            </div>
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">3. Punchline</span>
              <p className="text-slate-600 dark:text-slate-300 italic">&quot;{brief.punchline}&quot;</p>
            </div>
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">4. Clinical Message</span>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300">
                {brief.clinical_message_points.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">5. Hero Visual Concept</span>
              <p className="text-slate-600 dark:text-slate-300">{brief.hero_visual_concept}</p>
            </div>
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">6. Composition</span>
              <p className="text-slate-600 dark:text-slate-300">{brief.composition}</p>
            </div>
            <div className={`${card} space-y-1.5`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">7. Scientific Support</span>
              <ol className="list-decimal list-inside space-y-1 text-slate-600 dark:text-slate-300">
                {brief.scientific_support.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
            <div className={`${card} space-y-1.5 md:col-span-2`}>
              <span className="font-bold text-teal-700 dark:text-teal-400 block">8. Call to Prescribe</span>
              <p className="text-slate-600 dark:text-slate-300">{brief.call_to_prescribe}</p>
            </div>
          </div>

          {brief.ai_review_flags.length > 0 && (
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/30 text-[11px] text-amber-700 dark:text-amber-400 space-y-1">
              {brief.ai_review_flags.map((f, i) => <div key={i}>{f}</div>)}
            </div>
          )}

          <div className={`${card} space-y-2`}>
            <div className="flex items-center justify-between">
              <span className="font-bold text-teal-700 dark:text-teal-400 text-xs uppercase tracking-wider">
                Image-Generation Prompt
              </span>
              <button
                onClick={copyPrompt}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-brand-500 hover:text-brand-500 text-xs font-semibold text-slate-600 dark:text-slate-300 transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy Prompt'}
              </button>
            </div>
            <pre className="text-[11px] text-slate-600 dark:text-slate-300 whitespace-pre-wrap font-mono bg-slate-50 dark:bg-slate-950 p-3 rounded-lg border border-slate-200 dark:border-slate-800 max-h-64 overflow-y-auto">
              {brief.image_generation_prompt}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}
