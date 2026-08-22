'use client';

import React, { useState } from 'react';
import { HelpCircle, AlertCircle, CheckCircle, BookOpen } from 'lucide-react';
import { MRObjectionHandling } from '../lib/types';

interface MRObjectionSimulatorProps {
  objections: MRObjectionHandling[];
  brandName: string;
}

export default function MRObjectionSimulator({ objections, brandName }: MRObjectionSimulatorProps) {
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (!objections || objections.length === 0) return null;

  const current = objections[selectedIdx];

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center space-x-2 mb-4">
        <HelpCircle className="w-5 h-5 text-brand-700 dark:text-brand-400" />
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
          Doctor Objection Handling & Field Force Roleplay Simulator
        </h3>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
        Prepare your medical sales representatives to confidently handle tough physician pushbacks using source-backed clinical evidence.
      </p>

      {/* Objection selector tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {objections.map((obj, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedIdx(idx)}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold text-left transition border ${
              selectedIdx === idx
                ? 'bg-brand-600/20 border-brand-500 text-brand-700 dark:text-brand-300 shadow-sm'
                : 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:text-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            Objection {idx + 1}: {obj.doctor_objection.slice(0, 38)}...
          </button>
        ))}
      </div>

      {/* Objection details card */}
      <div className="space-y-4">
        {/* Doctor's Stated Objection */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center space-x-2 text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider mb-1">
            <AlertCircle className="w-4 h-4" />
            <span>Doctor's Stated Pushback</span>
          </div>
          <p className="text-base font-semibold text-slate-800 dark:text-slate-100 italic">
            "{current.doctor_objection}"
          </p>
          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            <span className="font-semibold text-slate-600 dark:text-slate-300">Underlying Concern: </span>
            {current.underlying_concern}
          </div>
        </div>

        {/* Recommended MR Response */}
        <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-800/60">
          <div className="flex items-center space-x-2 text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider mb-2">
            <CheckCircle className="w-4 h-4" />
            <span>Recommended Scientific Response Strategy for MR</span>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            "{current.recommended_mr_response.replace('{brand}', brandName)}"
          </p>
        </div>

        {/* Supporting evidence */}
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-teal-700 dark:text-teal-400" />
            <span className="text-slate-500 dark:text-slate-400">Supporting Landmark Clinical Trial:</span>
            <span className="font-semibold text-teal-700 dark:text-teal-300">{current.supporting_clinical_trial}</span>
          </div>
          <div className="text-slate-500 dark:text-slate-400">
            <span>Refer to Visual Aid: </span>
            <span className="font-bold text-brand-700 dark:text-brand-400">Slide {current.recommended_visual_aid_page}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
