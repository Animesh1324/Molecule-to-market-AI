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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-4 min-w-0">
          <Link href="/" className="flex items-center space-x-3 group min-w-0">
            <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform">
              <Activity className="w-5 h-5 text-slate-900 dark:text-white" />
            </div>
            <div className="min-w-0 leading-tight">
              <span className="block font-display text-base sm:text-lg tracking-tight text-navy-900 dark:text-white truncate">
                Molecule to Market AI
              </span>
              {/* Strapline is decorative — dropped on small screens so the two
                  lines never exceed the 64px the sticky tab strip assumes. */}
              <span className="hidden sm:block text-[10px] text-teal-700 dark:text-teal-400 font-mono tracking-wider uppercase font-semibold truncate">
                Molecule to Commercial Plan
              </span>
            </div>
          </Link>

          {projectTitle && (
            <div className="hidden lg:flex items-center space-x-2 pl-4 border-l border-slate-200 dark:border-slate-800 text-sm min-w-0">
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
        <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
          <Link
            href="/"
            className="flex items-center space-x-1.5 px-2 sm:px-3 py-1.5 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <FolderKanban className="w-4 h-4 shrink-0 text-slate-500 dark:text-slate-500 dark:text-slate-400" />
            <span className="hidden sm:inline whitespace-nowrap">Projects Hub</span>
          </Link>

          <div className="hidden sm:block h-4 w-px bg-slate-200 dark:bg-slate-800"></div>

          <div className="flex items-center space-x-2 bg-slate-200 dark:bg-slate-800/80 px-2 sm:px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700/60 text-xs">
            <AccessTokenGate />
            <ThemeToggle />
            <div className="w-2 h-2 shrink-0 rounded-full bg-emerald-500 animate-pulse"></div>
            {/* Status text is the first thing to go when width is tight. */}
            <span className="hidden xl:inline text-slate-600 dark:text-slate-300 font-medium whitespace-nowrap">
              15 Core Modules Active
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
