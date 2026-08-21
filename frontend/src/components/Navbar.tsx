import React from 'react';
import Link from 'next/link';
import ThemeToggle from './ThemeToggle';
import AccessTokenGate from './AccessTokenGate';
import { Activity, Layers, FileText, BarChart3, ShieldCheck, Sparkles, FolderKanban } from 'lucide-react';

interface NavbarProps {
  currentProjectId?: string;
  projectTitle?: string;
  moleculeName?: string;
}

export default function Navbar({ currentProjectId, projectTitle, moleculeName }: NavbarProps) {
  return (
    <header className="bg-white dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5 text-slate-900 dark:text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-brand-300 bg-clip-text text-transparent">
                Pharma BrandPlan AI
              </span>
              <span className="block text-[10px] text-teal-700 dark:text-teal-400 font-mono tracking-wider uppercase font-semibold">
                Molecule to Commercial Plan
              </span>
            </div>
          </Link>

          {projectTitle && (
            <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-200 dark:border-slate-800 text-sm">
              <span className="text-slate-500 dark:text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider font-mono">Active Initiative:</span>
              <span className="font-semibold text-slate-700 dark:text-slate-200 truncate max-w-xs">{projectTitle}</span>
              {moleculeName && (
                <span className="bg-brand-950 text-brand-700 dark:text-brand-300 text-xs px-2.5 py-0.5 rounded-full border border-brand-800 font-mono">
                  {moleculeName}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Global Nav Links */}
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <FolderKanban className="w-4 h-4 text-slate-500 dark:text-slate-500 dark:text-slate-400" />
            <span>Projects Hub</span>
          </Link>
          
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-800"></div>

          <div className="flex items-center space-x-2 bg-slate-200 dark:bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700/60 text-xs">
            <AccessTokenGate />
          <ThemeToggle />
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-slate-600 dark:text-slate-300 font-medium">11 Core Modules Active</span>
          </div>
        </div>
      </div>
    </header>
  );
}
