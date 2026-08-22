'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Activity,
  Plus,
  ArrowRight,
  Sparkles,
  BookOpen,
  TrendingUp,
  FileCheck2,
  Layers,
  Search,
  CheckCircle2,
  BarChart2
} from 'lucide-react';
import Navbar from '../components/Navbar';
import { Project } from '../lib/types';
import { fetchProjects, createProject } from '../lib/api';

const PRESET_MOLECULES = [
  { name: 'Empagliflozin', therapy: 'Cardiometabolic & Renal', indication: 'Heart Failure & CKD in T2D', geography: 'Global' },
  { name: 'Semaglutide', therapy: 'Metabolic & Cardiovascular', indication: 'Chronic Weight Management & MACE Reduction', geography: 'US & Global' },
  { name: 'Dapagliflozin', therapy: 'Cardio-Renal', indication: 'Heart Failure across all Ejection Fractions', geography: 'Global' },
  { name: 'Apixaban', therapy: 'Hematology & Cardiology', indication: 'Non-Valvular Atrial Fibrillation & VTE', geography: 'Global' },
  { name: 'Pembrolizumab', therapy: 'Immuno-Oncology', indication: 'First-line Advanced NSCLC & Solid Tumors', geography: 'Global' }
];

export default function HomePage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [targetMolecule, setTargetMolecule] = useState('');
  const [brandName, setBrandName] = useState('');
  const [therapyArea, setTherapyArea] = useState('Cardiometabolic');
  const [primaryIndication, setPrimaryIndication] = useState('');
  const [targetGeography, setTargetGeography] = useState('Global');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchProjects();
        setProjects(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetMolecule || !primaryIndication) return;

    setCreating(true);
    try {
      const newProj = await createProject({
        title: `${targetMolecule.trim()} Brand Strategy Plan`,
        target_molecule_name: targetMolecule.trim(),
        brand_working_name: brandName.trim() || `${targetMolecule.trim()} Brand`,
        therapy_area: therapyArea,
        primary_indication: primaryIndication.trim(),
        target_geography: targetGeography,
      });
      router.push(`/project/${newProj.id}`);
    } catch (err) {
      console.error(err);
      setCreating(false);
    }
  };

  const handleSelectPreset = (preset: typeof PRESET_MOLECULES[0]) => {
    setTargetMolecule(preset.name);
    setTherapyArea(preset.therapy);
    setPrimaryIndication(preset.indication);
    setTargetGeography(preset.geography);
    setBrandName(`${preset.name} Brand`);
    setShowCreateModal(true);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-slate-200 dark:border-slate-800/80 bg-gradient-to-b from-brand-50 via-white to-slate-50 dark:from-slate-900/60 dark:via-slate-950 dark:to-slate-950 py-16 px-6">
        <div className="max-w-6xl mx-auto text-center space-y-5">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-50 dark:bg-brand-950/80 border border-brand-800/60 text-brand-700 dark:text-brand-300 text-xs font-mono tracking-wide">
            <Sparkles className="w-3.5 h-3.5 text-teal-700 dark:text-teal-400" />
            <span>AI Operating System for Pharma Commercialization</span>
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight max-w-4xl mx-auto">
            From <span className="bg-gradient-to-r from-brand-500 via-brand-400 to-brand-300 bg-clip-text text-transparent">Molecule Discovery</span> to Market-Dominating <span className="underline decoration-brand-500 underline-offset-8">Brand Plan</span>
          </h1>

          <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Unify pharmacology, landmark PubMed trials, FDA/CDSCO labels, trademark vetting, epidemiological forecasting, and doctor visual aids in a single, audit-ready platform.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => {
                setTargetMolecule('');
                setBrandName('');
                setPrimaryIndication('');
                setShowCreateModal(true);
              }}
              className="flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-brand-600 to-teal-600 hover:from-brand-500 hover:to-teal-500 text-slate-900 dark:text-white font-semibold shadow-lg shadow-brand-500/25 transition-transform hover:scale-105"
            >
              <Plus className="w-5 h-5" />
              <span>Create New Brand Initiative</span>
            </button>
          </div>

          {/* Preset quick pills */}
          <div className="pt-6 flex flex-wrap items-center justify-center gap-2 text-xs">
            <span className="text-slate-500 dark:text-slate-500 mr-1">Quick Start Presets:</span>
            {PRESET_MOLECULES.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPreset(preset)}
                className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition flex items-center space-x-1.5"
              >
                <Activity className="w-3.5 h-3.5 text-teal-700 dark:text-teal-400" />
                <span>{preset.name}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-6 py-12 flex-1 w-full space-y-12">
        {/* Active Projects Grid */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center space-x-2">
                <Layers className="w-5 h-5 text-brand-700 dark:text-brand-400" />
                <span>Active Pharma Brand Initiatives</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Select a project to access its 15 integrated scientific and commercial modules
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-1.5 text-xs font-semibold text-brand-700 dark:text-brand-400 hover:text-brand-900 dark:hover:text-brand-300 transition"
            >
              <Plus className="w-4 h-4" />
              <span>New Initiative</span>
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-500">Loading initiatives...</div>
          ) : projects.length === 0 ? (
            <div className="p-12 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-3">
              <p className="text-slate-500 dark:text-slate-400">No initiatives created yet.</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 rounded-lg bg-brand-600 text-slate-900 dark:text-white text-sm font-medium"
              >
                Create Your First Brand Plan
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {projects.map((proj) => (
                <Link
                  key={proj.id}
                  href={`/project/${proj.id}`}
                  className="group block p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-brand-500/50 hover:bg-slate-850 transition-all shadow-lg hover:shadow-brand-500/10 flex flex-col justify-between space-y-6"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-400 border border-brand-800">
                        {proj.therapy_area}
                      </span>
                      <span className="text-xs font-medium text-emerald-700 dark:text-emerald-400 flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Draft Workspace</span>
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-slate-900 dark:text-white group-hover:text-brand-700 dark:group-hover:text-brand-300 transition">
                      {proj.title}
                    </h3>

                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      <strong className="text-slate-600 dark:text-slate-300">Indication:</strong> {proj.primary_indication}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <div className="flex items-center space-x-3">
                      <span>Molecule: <strong className="text-slate-700 dark:text-slate-200">{proj.target_molecule_name}</strong></span>
                      <span>Market: <strong className="text-slate-700 dark:text-slate-200">{proj.target_geography}</strong></span>
                    </div>
                    <span className="flex items-center space-x-1 text-brand-700 dark:text-brand-400 font-semibold group-hover:translate-x-1 transition-transform">
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* The 10 Modules Feature Overview */}
        <div className="pt-8 border-t border-slate-200 dark:border-slate-800/80 space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">15 Integrated Commercialization Modules</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
              Everything required to take a compound from pharmacological validation to final field force execution
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { title: '1. Molecule Intelligence', desc: 'Pharmacology, MoA, PK/PD (ADME), safety, and receptor pathways.', icon: Activity },
              { title: '2. Research Evidence', desc: 'PubMed trial extraction, sample size, hazard ratios, and claim backing.', icon: BookOpen },
              { title: '3. Clinical Trials', desc: 'Active pipeline radar, phase status, and competitor trials on CT.gov.', icon: TrendingUp },
              { title: '4. Regulatory Labels', desc: 'DailyMed SPL and CDSCO labels with black-box alert tracking.', icon: FileCheck2 },
              { title: '5. Trademark Studio', desc: 'Phonetic Soundex collision analysis and pharma stem generation.', icon: Sparkles },
              { title: '6. Competitors & SWOT', desc: '2x2 positioning quadrant, battlecards, and claim differentiation.', icon: BarChart2 },
              { title: '7. Market Forecasting', desc: 'Epidemiological patient funnel and 3-scenario 5-year revenue modeling.', icon: TrendingUp },
              { title: '8. Brand Plan Builder', desc: '12-section Notion-style strategic canvas with live citation backing.', icon: Layers },
              { title: '9. Creative & Detailing', desc: 'Visual Aid 6-slide detailer flow, LBL brief, and MR objection simulator.', icon: Sparkles },
              { title: '10. Report Center', desc: '1-click export to Word (.docx), PowerPoint (.pptx), and Excel (.xlsx).', icon: FileCheck2 }
            ].map((mod, idx) => {
              const Icon = mod.icon;
              return (
                <div key={idx} className="p-4 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80 space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-teal-700 dark:text-teal-400">
                    <Icon className="w-4 h-4" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200">{mod.title}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{mod.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Modal: Create New Initiative */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-50 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-brand-700 dark:text-brand-400" />
                <span>Initialize Brand Plan Strategy</span>
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-500 dark:text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-600 dark:text-slate-300 font-semibold mb-1">Target Molecule Name (Generic/INN) *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Empagliflozin, Semaglutide, Apixaban"
                  value={targetMolecule}
                  onChange={(e) => setTargetMolecule(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-300 font-semibold mb-1">Working Brand Name (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Cardioflo, Semavive (Leave blank for auto-suggestion)"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 font-semibold mb-1">Therapy Area</label>
                  <input
                    type="text"
                    value={therapyArea}
                    onChange={(e) => setTherapyArea(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 dark:text-slate-300 font-semibold mb-1">Target Geography</label>
                  <select
                    value={targetGeography}
                    onChange={(e) => setTargetGeography(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl px-3.5 py-2 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:border-brand-500"
                  >
                    <option value="Global">Global</option>
                    <option value="United States">United States (FDA)</option>
                    <option value="India">India (CDSCO)</option>
                    <option value="European Union">European Union (EMA)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-300 font-semibold mb-1">Primary Clinical Indication *</label>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. Heart Failure & Chronic Kidney Disease in Type 2 Diabetes"
                  value={primaryIndication}
                  onChange={(e) => setPrimaryIndication(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500"
                ></textarea>
              </div>

              <div className="pt-4 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-sm font-medium hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-slate-900 dark:text-white text-sm font-semibold shadow-lg shadow-brand-500/20 transition disabled:opacity-50"
                >
                  {creating ? 'Initializing AI Engine...' : 'Launch Brand Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
