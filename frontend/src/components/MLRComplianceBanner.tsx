import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

export default function MLRComplianceBanner() {
  return (
    <div className="bg-slate-900 border-b border-slate-800 px-6 py-2 flex flex-wrap items-center justify-between text-xs text-slate-400">
      <div className="flex items-center space-x-3">
        <span className="flex items-center space-x-1 text-emerald-400 font-medium">
          <ShieldCheck className="w-4 h-4" />
          <span>MLR Status: Review Required</span>
        </span>
        <span className="text-slate-600">|</span>
        <span>Claims must be source-backed before external use</span>
      </div>
      <div className="flex items-center space-x-2 text-slate-500">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-500/80" />
        <span>Internal draft only. Medical, regulatory, and legal review required.</span>
      </div>
    </div>
  );
}
