'use client';

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { MarketForecast } from '../lib/types';

interface ForecastChartsProps {
  forecast: MarketForecast;
}

export default function ForecastCharts({ forecast }: ForecastChartsProps) {
  const chartData = [
    {
      year: 'Year 1',
      Conservative: forecast.conservative_scenario.year_1 / 1e6,
      Realistic: forecast.realistic_scenario.year_1 / 1e6,
      Aggressive: forecast.aggressive_scenario.year_1 / 1e6,
    },
    {
      year: 'Year 2',
      Conservative: forecast.conservative_scenario.year_2 / 1e6,
      Realistic: forecast.realistic_scenario.year_2 / 1e6,
      Aggressive: forecast.aggressive_scenario.year_2 / 1e6,
    },
    {
      year: 'Year 3',
      Conservative: forecast.conservative_scenario.year_3 / 1e6,
      Realistic: forecast.realistic_scenario.year_3 / 1e6,
      Aggressive: forecast.aggressive_scenario.year_3 / 1e6,
    },
    {
      year: 'Year 4',
      Conservative: forecast.conservative_scenario.year_4 / 1e6,
      Realistic: forecast.realistic_scenario.year_4 / 1e6,
      Aggressive: forecast.aggressive_scenario.year_4 / 1e6,
    },
    {
      year: 'Year 5',
      Conservative: forecast.conservative_scenario.year_5 / 1e6,
      Realistic: forecast.realistic_scenario.year_5 / 1e6,
      Aggressive: forecast.aggressive_scenario.year_5 / 1e6,
    },
  ];

  const formatYAxis = (val: number) => `$${val.toFixed(0)}M`;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">5-Year Multi-Scenario Revenue Trajectory</h3>
          <p className="text-xs text-slate-500 dark:text-slate-500 dark:text-slate-400">Comparing Conservative, Base-Case Realistic, and Aggressive Guideline Adoption</p>
        </div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-500"></span>
            <span className="text-slate-600 dark:text-slate-300">Conservative ({forecast.conservative_scenario.cagr_percentage}% CAGR)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-brand-500"></span>
            <span className="text-slate-600 dark:text-slate-300 font-semibold">Realistic ({forecast.realistic_scenario.cagr_percentage}% CAGR)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-400"></span>
            <span className="text-slate-600 dark:text-slate-300">Aggressive ({forecast.aggressive_scenario.cagr_percentage}% CAGR)</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAggressive" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
              </linearGradient>
              <linearGradient id="colorRealistic" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0c87eb" stopOpacity={0.5}/>
                <stop offset="95%" stopColor="#0c87eb" stopOpacity={0.05}/>
              </linearGradient>
              <linearGradient id="colorConservative" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#64748b" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#64748b" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="year" stroke="#64748b" fontSize={12} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={12} tickFormatter={formatYAxis} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
              formatter={(val: number) => [`$${val.toFixed(2)}M USD`, '']}
            />
            <Area type="monotone" dataKey="Aggressive" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorAggressive)" />
            <Area type="monotone" dataKey="Realistic" stroke="#0c87eb" strokeWidth={3} fillOpacity={1} fill="url(#colorRealistic)" />
            <Area type="monotone" dataKey="Conservative" stroke="#64748b" strokeWidth={1.5} fillOpacity={1} fill="url(#colorConservative)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
          <div className="text-xs text-slate-500 dark:text-slate-500 dark:text-slate-400 font-medium">Conservative Peak (Yr 5)</div>
          <div className="text-xl font-bold text-slate-600 dark:text-slate-300 font-mono mt-1">
            ${(forecast.conservative_scenario.year_5 / 1e6).toFixed(1)}M
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-500 mt-0.5">Assumes heavy generic discounting & slow uptake</div>
        </div>

        <div className="p-3.5 rounded-xl bg-brand-950/40 border border-brand-800/60">
          <div className="text-xs text-brand-700 dark:text-brand-300 font-medium">Realistic Base-Case Peak (Yr 5)</div>
          <div className="text-xl font-bold text-brand-700 dark:text-brand-400 font-mono mt-1">
            ${(forecast.realistic_scenario.year_5 / 1e6).toFixed(1)}M
          </div>
          <div className="text-[11px] text-brand-700 dark:text-brand-300/70 mt-0.5">Standard field execution & guideline backing</div>
        </div>

        <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60">
          <div className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">Aggressive Peak (Yr 5)</div>
          <div className="text-xl font-bold text-emerald-700 dark:text-emerald-400 font-mono mt-1">
            ${(forecast.aggressive_scenario.year_5 / 1e6).toFixed(1)}M
          </div>
          <div className="text-[11px] text-emerald-700 dark:text-emerald-300/70 mt-0.5">First-line class endorsement & rapid digital scale</div>
        </div>
      </div>
    </div>
  );
}
