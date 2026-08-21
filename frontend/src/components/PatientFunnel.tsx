import React from 'react';
import { Users, UserCheck, Stethoscope, Award } from 'lucide-react';
import { MarketForecast } from '../lib/types';

interface PatientFunnelProps {
  forecast: MarketForecast;
}

export default function PatientFunnel({ forecast }: PatientFunnelProps) {
  const steps = [
    {
      label: '1. Total Population',
      count: forecast.total_population.toLocaleString(),
      percentage: '100%',
      icon: Users,
      color: 'from-slate-700 to-slate-800',
      textColor: 'text-slate-600 dark:text-slate-300'
    },
    {
      label: '2. Prevalent Patients',
      count: forecast.prevalent_patient_pool.toLocaleString(),
      percentage: `${(forecast.prevalence_rate * 100).toFixed(1)}% Prevalence`,
      icon: Users,
      color: 'from-blue-900/80 to-blue-950',
      textColor: 'text-blue-300'
    },
    {
      label: '3. Diagnosed Patients',
      count: forecast.diagnosed_patient_pool.toLocaleString(),
      percentage: `${(forecast.diagnosed_rate * 100).toFixed(0)}% Diagnosis Rate`,
      icon: UserCheck,
      color: 'from-cyan-900/80 to-cyan-950',
      textColor: 'text-cyan-700 dark:text-cyan-300'
    },
    {
      label: '4. Treated Patient Pool',
      count: forecast.treated_patient_pool.toLocaleString(),
      percentage: `${(forecast.treated_rate * 100).toFixed(0)}% Treatment Rate`,
      icon: Stethoscope,
      color: 'from-teal-900/80 to-teal-950',
      textColor: 'text-teal-700 dark:text-teal-300'
    }
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-gradient-to-b ${step.color} relative overflow-hidden flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-500 dark:text-slate-400 mb-2">
                <span>{step.label}</span>
                <Icon className={`w-4 h-4 ${step.textColor}`} />
              </div>
              <div>
                <div className="text-xl font-bold text-slate-900 dark:text-white font-mono tracking-tight">{step.count}</div>
                <div className={`text-xs font-medium mt-1 ${step.textColor}`}>{step.percentage}</div>
              </div>
              <div className="absolute right-0 bottom-0 w-24 h-24 bg-white/5 rounded-full blur-2xl pointer-events-none"></div>
            </div>
          );
        })}
      </div>

      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div>
          <span className="text-slate-500 dark:text-slate-500 dark:text-slate-400">Total Available Treated Market Size: </span>
          <span className="text-lg font-bold text-emerald-700 dark:text-emerald-400 font-mono ml-2">
            ${(forecast.current_therapy_market_size_usd / 1e6).toFixed(1)} Million USD
          </span>
        </div>
        <div>
          <span className="text-slate-500 dark:text-slate-500 dark:text-slate-400">Therapy Area CAGR: </span>
          <span className="font-semibold text-brand-700 dark:text-brand-300 ml-1">+{forecast.therapy_market_cagr}% / Year</span>
        </div>
        <div>
          <span className="text-slate-500 dark:text-slate-500 dark:text-slate-400">Net Patient-Year Cost: </span>
          <span className="font-semibold text-slate-700 dark:text-slate-200 ml-1">${forecast.annual_cost_per_patient_usd.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
