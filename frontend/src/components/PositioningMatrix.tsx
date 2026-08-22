import React from 'react';
import { CompetitorProfile } from '../lib/types';
import { Crosshair, Target } from 'lucide-react';

interface PositioningMatrixProps {
  competitors: CompetitorProfile[];
  targetMolecule: string;
  targetBrand?: string;
}

export default function PositioningMatrix({ competitors, targetMolecule, targetBrand }: PositioningMatrixProps) {
  // Target molecule coordinate (premier position)
  const targetPoint = {
    name: targetBrand || `${targetMolecule} (Our Brand)`,
    x: 9.0, // High efficacy
    y: 8.8, // High safety & convenience
    isTarget: true,
    share: 25.0
  };

  const points = [
    targetPoint,
    ...competitors.map(c => ({
      name: c.brand_name,
      x: c.quadrant_x_efficacy,
      y: c.quadrant_y_safety_convenience,
      isTarget: false,
      share: c.market_share_percentage
    }))
  ];

  // Helper to convert -10..+10 to 5%..95% CSS percentage
  const toPercentX = (val: number) => `${((val + 10) / 20) * 85 + 7.5}%`;
  const toPercentY = (val: number) => `${((10 - val) / 20) * 85 + 7.5}%`;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Perceptual Competitive Positioning Quadrant</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Hard Clinical Efficacy (X-Axis) vs. Safety, Tolerability & Convenience (Y-Axis)</p>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="flex items-center space-x-1 text-emerald-700 dark:text-emerald-400 font-semibold">
            <Target className="w-3.5 h-3.5" />
            <span>Target Strategic Sweet Spot</span>
          </span>
        </div>
      </div>

      {/* 2x2 Grid Canvas */}
      <div className="relative w-full h-80 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden my-4 p-4">
        {/* Quadrant Axes */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-200 dark:bg-slate-800"></div>
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200 dark:bg-slate-800"></div>

        {/* Quadrant Labels */}
        <div className="absolute top-2 right-3 text-[10px] font-bold text-emerald-700 dark:text-emerald-400/60 uppercase tracking-wider">
          Premier: High Efficacy & High Safety
        </div>
        <div className="absolute top-2 left-3 text-[10px] font-bold text-slate-500 dark:text-slate-500 uppercase tracking-wider">
          Niche: High Safety / Modest Efficacy
        </div>
        <div className="absolute bottom-2 right-3 text-[10px] font-bold text-slate-500 dark:text-slate-500 uppercase tracking-wider">
          High Efficacy / Safety Burden
        </div>
        <div className="absolute bottom-2 left-3 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
          Legacy Standard of Care
        </div>

        {/* Points Rendering */}
        {points.map((p, idx) => (
          <div
            key={idx}
            className="absolute -translate-x-1/2 -translate-y-1/2 group cursor-pointer transition-transform hover:scale-125 z-10"
            style={{ left: toPercentX(p.x), top: toPercentY(p.y) }}
          >
            <div className="flex flex-col items-center">
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center shadow-lg transition-all ${
                  p.isTarget
                    ? 'bg-emerald-500 ring-4 ring-emerald-500/30 text-slate-950 animate-pulse'
                    : 'bg-brand-600 ring-2 ring-brand-400/40 text-slate-900 dark:text-white'
                }`}
              >
                <span className="text-[9px] font-bold">{p.isTarget ? '★' : idx}</span>
              </div>
              <div className="mt-1 px-2 py-0.5 rounded bg-white dark:bg-slate-900/90 border border-slate-300 dark:border-slate-700 text-[10px] font-semibold text-slate-700 dark:text-slate-200 whitespace-nowrap shadow-md">
                {p.name} {p.share > 0 ? `(${p.share}%)` : ''}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2">
        <span>← Low Clinical Endpoint Separation</span>
        <span className="font-semibold text-slate-700 dark:text-slate-200">X-Axis: Level-1 Hard Endpoint Efficacy</span>
        <span>Superior Endpoint Separation →</span>
      </div>
    </div>
  );
}
