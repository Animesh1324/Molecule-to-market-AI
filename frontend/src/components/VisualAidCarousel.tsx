'use client';

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, MessageSquare, Shield, CheckCircle2, Bookmark } from 'lucide-react';
import { VisualAidSlide } from '../lib/types';

interface VisualAidCarouselProps {
  slides: VisualAidSlide[];
  brandName: string;
}

export default function VisualAidCarousel({ slides, brandName }: VisualAidCarouselProps) {
  const [activeIdx, setActiveIdx] = useState(0);

  if (!slides || slides.length === 0) return null;

  const current = slides[activeIdx];

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-teal-700 dark:text-teal-400 uppercase tracking-wider">
            <Bookmark className="w-3.5 h-3.5" />
            <span>Visual Aid Detailer Storyboard</span>
          </div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-1">
            Slide {current.slide_number} of {slides.length}: {current.slide_title}
          </h3>
        </div>

        {/* Carousel slide indicators */}
        <div className="flex items-center space-x-1.5 bg-slate-50 dark:bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800">
          {slides.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setActiveIdx(idx)}
              className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                activeIdx === idx
                  ? 'bg-brand-600 text-slate-900 dark:text-white shadow-md shadow-brand-500/20'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {s.slide_number}
            </button>
          ))}
        </div>
      </div>

      {/* Slide Mockup Canvas */}
      <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-inner">
        {/* Top Slide Header */}
        <div className="bg-gradient-to-r from-white via-brand-50 to-slate-50 dark:from-slate-900 dark:via-brand-950/60 dark:to-slate-900 p-5 border-b border-slate-200 dark:border-slate-800">
          <div className="text-xs font-mono text-brand-700 dark:text-brand-400 tracking-wider uppercase">{brandName} Clinical Detailing</div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-white mt-1 leading-snug">
            {current.headline_for_doctor}
          </h2>
        </div>

        {/* Slide Body: Visual + Key Points */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Visual Concept Box */}
          <div className="md:col-span-5 bg-white dark:bg-slate-900/90 rounded-xl p-5 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4">
            <div>
              <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-2">
                Visual & Infographic Concept
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300 italic bg-slate-50 dark:bg-slate-950/80 p-3 rounded-lg border border-slate-200 dark:border-slate-800/80">
                "{current.visual_concept_description}"
              </p>
            </div>

            <div className="bg-brand-50 dark:bg-brand-950/40 p-3 rounded-lg border border-brand-800/40">
              <div className="text-xs font-semibold text-brand-700 dark:text-brand-300 uppercase tracking-wider mb-1">
                Data Chart / Graph
              </div>
              <p className="text-xs text-brand-800 dark:text-brand-200/90">
                {current.clinical_data_chart_description}
              </p>
            </div>
          </div>

          {/* Key Bullet Points */}
          <div className="md:col-span-7 flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                Key Strategic Proof Points for Physician
              </div>
              {current.key_bullet_points.map((pt, pIdx) => (
                <div key={pIdx} className="flex items-start space-x-3 p-3 rounded-lg bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80">
                  <CheckCircle2 className="w-5 h-5 text-emerald-700 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-slate-700 dark:text-slate-200 font-medium leading-relaxed">{pt}</span>
                </div>
              ))}
            </div>

            {/* MR Verbal Talk-Track Box */}
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/95 border-l-4 border-brand-500 shadow-md">
              <div className="flex items-center space-x-2 text-xs font-bold text-brand-700 dark:text-brand-300 uppercase tracking-wider mb-1.5">
                <MessageSquare className="w-4 h-4 text-brand-700 dark:text-brand-400" />
                <span>Medical Representative (MR) Verbal Talk-Track</span>
              </div>
              <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
                "{current.medical_representative_talk_track}"
              </p>
            </div>
          </div>
        </div>

        {/* Slide Footers: Evidence & Fair Balance */}
        <div className="bg-white dark:bg-slate-900/90 px-6 py-3 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="text-slate-500 dark:text-slate-400">
            <span className="font-semibold text-slate-600 dark:text-slate-300">Reference: </span>
            <span className="font-mono text-teal-700 dark:text-teal-400">{current.evidence_citation}</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-500 text-[11px]">
            <Shield className="w-3.5 h-3.5 text-amber-500/80" />
            <span>{current.safety_fair_balance_footer}</span>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-between mt-4 pt-2">
        <button
          onClick={() => setActiveIdx(prev => Math.max(0, prev - 1))}
          disabled={activeIdx === 0}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium transition disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Previous Slide</span>
        </button>

        <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
          Slide {activeIdx + 1} of {slides.length}
        </span>

        <button
          onClick={() => setActiveIdx(prev => Math.min(slides.length - 1, prev + 1))}
          disabled={activeIdx === slides.length - 1}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-slate-900 dark:text-white text-sm font-medium transition disabled:opacity-30 disabled:cursor-not-allowed shadow-md shadow-brand-600/20"
        >
          <span>Next Slide</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
