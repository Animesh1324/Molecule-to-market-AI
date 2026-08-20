'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Activity,
  BookOpen,
  TrendingUp,
  FileCheck2,
  FileText,
  Sparkles,
  BarChart2,
  Layers,
  FileSpreadsheet,
  Download,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Sliders,
  AlertTriangle,
  Send,
  RefreshCw,
  Award
} from 'lucide-react';
import Link from 'next/link';
import Navbar from '../../../components/Navbar';
import PatientFunnel from '../../../components/PatientFunnel';
import ForecastCharts from '../../../components/ForecastCharts';
import PositioningMatrix from '../../../components/PositioningMatrix';
import VisualAidCarousel from '../../../components/VisualAidCarousel';
import MRObjectionSimulator from '../../../components/MRObjectionSimulator';
import AICoPilotDrawer from '../../../components/AICoPilotDrawer';

import {
  Project,
  MoleculeProfile,
  ResearchPaper,
  ClaimEvidenceMapping,
  ClinicalTrialLandscape,
  RegulatoryIntelligence,
  TrademarkIntelligence,
  CompetitorIntelligence,
  MarketForecast,
  CompleteBrandPlan,
  CreativeCommercialAssets,
  MLRAuditEntry
} from '../../../lib/types';

import {
  fetchProjectById,
  fetchMoleculeProfile,
  fetchEvidencePapers,
  fetchClaimMappings,
  fetchClinicalTrials,
  fetchRegulatoryLabels,
  fetchTrademarkAnalysis,
  fetchCompetitors,
  fetchMarketForecast,
  fetchBrandPlan,
  fetchCreativeAssets,
  fetchAuditTrail,
  getExportDocxUrl,
  getExportPptxUrl,
  getExportXlsxUrl
} from '../../../lib/api';

export default function ProjectWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  // Active module tab
  const [activeTab, setActiveTab] = useState('molecule');

  // Core project state
  const [project, setProject] = useState<Project | null>(null);
  const [molecule, setMolecule] = useState<MoleculeProfile | null>(null);
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [claims, setClaims] = useState<ClaimEvidenceMapping[]>([]);
  const [trials, setTrials] = useState<ClinicalTrialLandscape | null>(null);
  const [regulatory, setRegulatory] = useState<RegulatoryIntelligence | null>(null);
  const [trademark, setTrademark] = useState<TrademarkIntelligence | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorIntelligence | null>(null);
  const [forecast, setForecast] = useState<MarketForecast | null>(null);
  const [brandPlan, setBrandPlan] = useState<CompleteBrandPlan | null>(null);
  const [assets, setAssets] = useState<CreativeCommercialAssets | null>(null);
  const [auditTrail, setAuditTrail] = useState<MLRAuditEntry[]>([]);

  // Loading states
  const [loading, setLoading] = useState(true);

  // Interactive Forecasting Form State
  const [prevalenceRate, setPrevalenceRate] = useState(0.105);
  const [diagnosedRate, setDiagnosedRate] = useState(0.72);
  const [treatedRate, setTreatedRate] = useState(0.60);
  const [adoptionRate, setAdoptionRate] = useState(0.04);
  const [annualCost, setAnnualCost] = useState(3600);

  // AI Co-Pilot Drawer State
  const [isCoPilotOpen, setIsCoPilotOpen] = useState(false);

  // Fetch all module data
  useEffect(() => {
    async function loadAllData() {
      if (!projectId) return;
      setLoading(true);
      try {
        const proj = await fetchProjectById(projectId);
        setProject(proj);

        const molName = proj.target_molecule_name;

        // Fetch parallel module data
        const [
          molData,
          paperData,
          claimData,
          trialData,
          regData,
          tmData,
          compData,
          fcData,
          bpData,
          assetData,
          audData
        ] = await Promise.all([
          fetchMoleculeProfile(molName),
          fetchEvidencePapers(molName, proj.primary_indication),
          fetchClaimMappings(molName, proj.primary_indication),
          fetchClinicalTrials(molName, proj.primary_indication),
          fetchRegulatoryLabels(molName),
          fetchTrademarkAnalysis(molName, proj.therapy_area),
          fetchCompetitors(molName, proj.primary_indication),
          fetchMarketForecast({
            therapy_area: proj.therapy_area,
            target_geography: proj.target_geography,
            prevalence_rate: prevalenceRate,
            diagnosed_rate: diagnosedRate,
            treated_rate: treatedRate,
            brand_adoption_rate_y1: adoptionRate,
            annual_cost_per_patient_usd: annualCost
          }),
          fetchBrandPlan({
            project_id: proj.id,
            molecule: molName,
            brand_name: proj.brand_working_name,
            therapy_area: proj.therapy_area,
            indication: proj.primary_indication,
            target_geography: proj.target_geography
          }),
          fetchCreativeAssets(molName, proj.brand_working_name, proj.primary_indication),
          fetchAuditTrail()
        ]);

        setMolecule(molData);
        setPapers(paperData);
        setClaims(claimData);
        setTrials(trialData);
        setRegulatory(regData);
        setTrademark(tmData);
        setCompetitors(compData);
        setForecast(fcData);
        setBrandPlan(bpData);
        setAssets(assetData);
        setAuditTrail(audData);
      } catch (err) {
        console.error('Error loading project data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAllData();
  }, [projectId]);

  // Recalculate forecast on slider change
  const handleRecalculateForecast = async () => {
    if (!project) return;
    try {
      const updated = await fetchMarketForecast({
        therapy_area: project.therapy_area,
        target_geography: project.target_geography,
        prevalence_rate: prevalenceRate,
        diagnosed_rate: diagnosedRate,
        treated_rate: treatedRate,
        brand_adoption_rate_y1: adoptionRate,
        annual_cost_per_patient_usd: annualCost
      });
      setForecast(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const navTabs = [
    { id: 'molecule', label: '1. Molecule Intelligence', icon: Activity },
    { id: 'evidence', label: '2. Research Evidence', icon: BookOpen },
    { id: 'trials', label: '3. Clinical Trials Radar', icon: TrendingUp },
    { id: 'regulatory', label: '4. Regulatory Labels', icon: FileCheck2 },
    { id: 'trademark', label: '5. Trademark & Naming', icon: Sparkles },
    { id: 'competitors', label: '6. Competitors & SWOT', icon: BarChart2 },
    { id: 'forecast', label: '7. Market Forecasting', icon: Sliders },
    { id: 'brand_plan', label: '8. Brand Plan Builder', icon: Layers },
    { id: 'creative', label: '9. Creative & Detailing', icon: Sparkles },
    { id: 'reports', label: '10. Report Center & MLR', icon: Download }
  ];

  if (loading || !project) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-4">
          <div className="w-12 h-12 rounded-full border-4 border-brand-500 border-t-transparent animate-spin"></div>
          <p className="text-slate-400 font-mono text-sm">Synthesizing scientific and commercial intelligence across 10 modules...</p>
        </div>
      </div>
    );
  }

  const brandDisplayName = project.brand_working_name || `${project.target_molecule_name} Brand`;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Navbar
        currentProjectId={project.id}
        projectTitle={project.title}
        moleculeName={project.target_molecule_name}
      />

      {/* Module Tabs Navigation Bar */}
      <div className="bg-slate-900 border-b border-slate-800 sticky top-16 z-40 overflow-x-auto shadow-md">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between min-w-max py-2 gap-3">
          <div className="flex items-center space-x-1">
            {navTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-teal-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center space-x-2 pl-4 border-l border-slate-800">
            <Link
              href={`/project/${project.id}/monograph`}
              target="_blank"
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-teal-300 text-xs font-semibold border border-slate-700 transition"
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              <span>Print Monograph</span>
            </Link>

            <button
              onClick={() => setIsCoPilotOpen(true)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-teal-600 hover:from-brand-500 hover:to-teal-500 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Co-Pilot</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Module Content Canvas */}
      <div className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* ========================================================================= */}
        {/* MODULE 1: MOLECULE INTELLIGENCE */}
        {/* ========================================================================= */}
        {activeTab === 'molecule' && molecule && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 1: Chemoinformatics & Pharmacology</span>
                <h1 className="text-2xl md:text-3xl font-extrabold text-white mt-0.5">{molecule.generic_name}</h1>
                <p className="text-xs text-slate-400 mt-1">{molecule.chemical_name}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300">
                  CAS: {molecule.cas_number || 'N/A'}
                </span>
                {molecule.pubchem_cid && (
                  <a
                    href={`https://pubchem.ncbi.nlm.nih.gov/compound/${molecule.pubchem_cid}`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center space-x-1 px-3 py-1 rounded-full bg-brand-950 border border-brand-800 text-xs font-mono text-brand-300 hover:text-brand-200"
                  >
                    <span>PubChem CID: {molecule.pubchem_cid}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Differentiating Science Callout */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-brand-950/80 via-slate-900 to-slate-900 border border-brand-800/60 shadow-lg">
              <div className="flex items-center space-x-2 text-xs font-bold text-teal-400 uppercase tracking-wider mb-1">
                <Award className="w-4 h-4" />
                <span>Differentiating Science & Core Clinical Advantage</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed font-medium">
                {molecule.differentiating_science}
              </p>
            </div>

            {/* 3-Column Profile Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Pharmacology Card */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-brand-400" />
                  <span>Mechanism & Target Binding</span>
                </h3>
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-slate-500 block">Pharmacological Class</span>
                    <span className="text-slate-200 font-semibold">{molecule.pharmacological_class}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Mechanism of Action (MoA)</span>
                    <p className="text-slate-300 mt-1 leading-relaxed">{molecule.mechanism_of_action}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Pharmacodynamics (PD)</span>
                    <p className="text-slate-300 mt-1 leading-relaxed">{molecule.pharmacodynamics}</p>
                  </div>
                </div>
              </div>

              {/* Pharmacokinetics (ADME) Card */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <Sliders className="w-4 h-4 text-teal-400" />
                  <span>Pharmacokinetics (ADME)</span>
                </h3>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">Half-Life</span>
                    <span className="text-teal-300 font-bold font-mono">{molecule.pharmacokinetics.half_life}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">Tmax</span>
                    <span className="text-teal-300 font-bold font-mono">{molecule.pharmacokinetics.tmax}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">Protein Binding</span>
                    <span className="text-slate-200 font-medium">{molecule.pharmacokinetics.protein_binding}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">Bioavailability</span>
                    <span className="text-slate-200 font-medium">{molecule.pharmacokinetics.bioavailability}</span>
                  </div>
                </div>
                <div className="text-xs space-y-1.5 pt-2">
                  <div>
                    <span className="text-slate-500">Metabolic Enzymes: </span>
                    <span className="text-slate-300">{molecule.pharmacokinetics.metabolism}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Elimination: </span>
                    <span className="text-slate-300">{molecule.pharmacokinetics.elimination}</span>
                  </div>
                </div>
              </div>

              {/* Safety & Adverse Events Card */}
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Safety & Warnings Profile</span>
                </h3>

                {molecule.black_box_warnings.length > 0 && (
                  <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs space-y-1">
                    <div className="font-bold uppercase tracking-wider flex items-center space-x-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      <span>Black Box Warning</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">{molecule.black_box_warnings[0]}</p>
                  </div>
                )}

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-500 block mb-1">Common Adverse Effects</span>
                    <div className="flex flex-wrap gap-1.5">
                      {molecule.adverse_effects.common.map((ae, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px]">
                          {ae}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2">
                    <span className="text-slate-500 block mb-1">Contraindications</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                      {molecule.contraindications.map((c, idx) => (
                        <li key={idx}>{c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Special Populations Table */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Special Population Guidelines & Renal/Hepatic Dosing
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="font-bold text-teal-400 block mb-1">Renal Impairment</span>
                  <p className="text-slate-300 leading-relaxed">{molecule.special_populations.renal_impairment}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="font-bold text-teal-400 block mb-1">Hepatic Impairment</span>
                  <p className="text-slate-300 leading-relaxed">{molecule.special_populations.hepatic_impairment}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="font-bold text-teal-400 block mb-1">Pregnancy & Lactation</span>
                  <p className="text-slate-300 leading-relaxed">{molecule.special_populations.pregnancy}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 2: RESEARCH PAPER FINDER */}
        {/* ========================================================================= */}
        {activeTab === 'evidence' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 2: Literature Ingestion & Evidence Hierarchy</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">PubMed Clinical Evidence Matrix</h1>
                <p className="text-xs text-slate-400 mt-1">Ranked by evidence strength (Systematic Review &gt; RCT &gt; Observational)</p>
              </div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 font-mono">
                  {papers.length} Landmark Papers Ingested
                </span>
              </div>
            </div>

            {/* Papers List */}
            <div className="space-y-4">
              {papers.length === 0 && (
                <div className="p-6 rounded-2xl bg-amber-950/30 border border-amber-800 text-amber-200 text-sm">
                  No PubMed evidence candidates were found for this molecule/indication. Do not create clinical claims until sources are added and reviewed.
                </div>
              )}
              {papers.map((paper, idx) => (
                <div key={idx} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-brand-950 text-brand-300 border border-brand-800 text-xs font-semibold">
                        {paper.study_type}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-semibold">
                        {paper.evidence_level}
                      </span>
                      {paper.sample_size && (
                        <span className="text-xs font-mono text-slate-400">
                          N = {paper.sample_size.toLocaleString()} Patients
                        </span>
                      )}
                    </div>
                    {paper.pmid && (
                      <a
                        href={paper.url || `https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}/`}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center space-x-1 text-xs text-teal-400 hover:underline font-mono"
                      >
                        <span>PMID: {paper.pmid}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-white leading-snug">
                    {paper.title}
                  </h3>

                  <div className="text-xs text-slate-400">
                    <span className="font-semibold text-slate-300">{paper.journal}</span> ({paper.publication_year}) | Authors: {paper.authors.slice(0, 4).join(', ')} et al.
                  </div>

                  {/* Primary Endpoint Results Banner */}
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500 text-[10px] block">Primary Outcome Finding</span>
                      <span className="text-emerald-400 font-bold">{paper.primary_endpoint_result}</span>
                    </div>
                    {paper.hazard_ratio && (
                      <div>
                        <span className="text-slate-500 text-[10px] block">Hazard Ratio (HR)</span>
                        <span className="text-slate-200 font-mono font-semibold">{paper.hazard_ratio}</span>
                      </div>
                    )}
                    {paper.p_value && (
                      <div>
                        <span className="text-slate-500 text-[10px] block">Statistical Significance</span>
                        <span className="text-teal-300 font-mono font-bold">{paper.p_value}</span>
                      </div>
                    )}
                  </div>

                  <div className="text-xs text-slate-300 leading-relaxed">
                    <strong className="text-slate-400">Claim Support Value:</strong> {paper.claim_support_potential}
                  </div>
                </div>
              ))}
            </div>

            {/* Claim Evidence Mapping Table */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Claim-to-Evidence Matrix for MLR Compliance
              </h3>
              <div className="divide-y divide-slate-800">
                {claims.length === 0 && (
                  <div className="py-4 text-sm text-amber-300">
                    No claim mappings are available. Claims remain blocked until evidence and label sources are reviewed.
                  </div>
                )}
                {claims.map((claim, cIdx) => (
                  <div key={cIdx} className="py-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-brand-400 font-semibold">{claim.category} Claim</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-[10px] font-semibold border border-emerald-800">
                        {claim.label_status}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-slate-100">"{claim.claim_text}"</p>
                    <div className="text-xs text-slate-400 flex items-center space-x-2">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Evidence candidates: {claim.supported_by_papers.map(p => p.journal).join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 3: CLINICAL TRIALS INTELLIGENCE */}
        {/* ========================================================================= */}
        {activeTab === 'trials' && trials && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 3: ClinicalTrials.gov Pipeline Radar</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Clinical Trial Landscape</h1>
                <p className="text-xs text-slate-400 mt-1">Tracking ongoing Phase 1-4 studies, endpoints, and competitor pipeline threats</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                  {trials.total_trials_found} Registered Trials Found
                </span>
              </div>
            </div>

            {/* Trial Phase Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'].map((phase, idx) => {
                const count = trials.all_trials.filter(t => t.phase === phase).length || (phase === 'Phase 3' ? trials.landmark_trials.length : 0);
                return (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-500 font-medium">{phase} Studies</span>
                      <div className="text-2xl font-bold text-white font-mono mt-1">{count}</div>
                    </div>
                    <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-teal-400 font-bold font-mono text-xs">
                      P{idx+1}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Landmark Trials List */}
            <div className="space-y-4">
              {trials.landmark_trials.length === 0 && (
                <div className="p-6 rounded-2xl bg-amber-950/30 border border-amber-800 text-amber-200 text-sm">
                  No ClinicalTrials.gov records were found. Trial claims and competitor pipeline conclusions should remain blank.
                </div>
              )}
              {trials.landmark_trials.map((trial, tIdx) => (
                <div key={tIdx} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-semibold">
                        {trial.phase}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 text-xs font-semibold">
                        {trial.status}
                      </span>
                      {trial.acronym && (
                        <span className="px-2 py-0.5 rounded bg-brand-950 text-brand-300 font-mono text-xs font-bold border border-brand-800">
                          {trial.acronym}
                        </span>
                      )}
                    </div>
                    <a
                      href={trial.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center space-x-1 text-xs text-teal-400 hover:underline font-mono"
                    >
                      <span>{trial.nct_id}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <h3 className="text-lg font-bold text-white leading-snug">
                    {trial.title}
                  </h3>

                  <div className="text-xs text-slate-400 flex flex-wrap items-center gap-4">
                    <span>Sponsor: <strong className="text-slate-300">{trial.sponsor}</strong></span>
                    <span>Enrollment: <strong className="text-slate-300">{trial.enrollment?.toLocaleString() || 'N/A'} Patients</strong></span>
                    <span>Indication: <strong className="text-slate-300">{trial.indication}</strong></span>
                  </div>

                  {trial.results_summary && (
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200">
                      <strong className="text-emerald-400 block mb-1">Trial Results Summary:</strong>
                      {trial.results_summary}
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                    <strong className="text-slate-500">Primary Endpoints: </strong>
                    {trial.primary_endpoints.join('; ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 4: REGULATORY INTELLIGENCE */}
        {/* ========================================================================= */}
        {activeTab === 'regulatory' && regulatory && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 4: Global Regulatory & Label Parsers</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Regulatory Intelligence Dossier</h1>
                <p className="text-xs text-slate-400 mt-1">Cross-referencing US FDA (DailyMed), CDSCO (India), and EMA (European Union)</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono">
                  Status: {regulatory.generic_vs_innovator_status}
                </span>
              </div>
            </div>

            {/* Fair Balance Compliance Notice */}
            <div className="p-4 rounded-xl bg-slate-900 border-l-4 border-emerald-500 text-xs text-slate-300 space-y-1">
              <div className="font-bold text-slate-200 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>FDA OPDP & CDSCO UCPMP Fair Balance Standard</span>
              </div>
              <p>{regulatory.compliance_fair_balance_notes}</p>
            </div>

            {/* 3-Agency Comparative Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[regulatory.us_fda, regulatory.india_cdsco, regulatory.eu_ema].map((agency, idx) => (
                <div key={idx} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-bold text-white">{agency.agency_name}</h3>
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-xs font-semibold border border-emerald-800">
                        {agency.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400">
                      <div>Innovator Brand: <strong className="text-slate-200">{agency.innovator_brand_name || 'N/A'}</strong></div>
                      <div>Approved Year: <strong className="text-slate-200">{agency.approval_year || 'N/A'}</strong></div>
                    </div>

                    <div>
                      <span className="text-xs font-semibold text-slate-400 block mb-1">Approved Indications</span>
                      <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                        {agency.approved_indications.map((ind, iIdx) => (
                          <li key={iIdx} className="leading-snug">{ind}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-500">Dosing: </span>
                    {agency.dosage_and_administration_summary}
                  </div>
                </div>
              ))}
            </div>

            {/* Fact vs AI Strategic Interpretation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Regulatory Label Facts Requiring Review</span>
                </h4>
                <ul className="space-y-2 text-xs text-slate-300">
                  {regulatory.key_label_claims_verified.map((f, idx) => (
                    <li key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 leading-relaxed">
                      {f}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold text-brand-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Sparkles className="w-4 h-4" />
                  <span>AI Strategic Interpretation & Positioning Window</span>
                </h4>
                <ul className="space-y-2 text-xs text-slate-300">
                  {regulatory.ai_strategic_interpretation.map((f, idx) => (
                    <li key={idx} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 leading-relaxed">
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 5: TRADEMARK & BRAND NAMING */}
        {/* ========================================================================= */}
        {activeTab === 'trademark' && trademark && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 5: Trademark Clearance & Pharma Brand Naming</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Brand Naming & Phonetic Conflict Analysis</h1>
                <p className="text-xs text-slate-400 mt-1">Phonetic Soundex collision analysis and Class 5 pharmaceutical trademark search links</p>
              </div>
            </div>

            {/* Proposed Brand Names Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {trademark.suggested_brand_names.map((sug, sIdx) => (
                <div key={sIdx} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-brand-500/50 transition space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-bold text-white tracking-tight">{sug.name}</h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                        sug.collision_risk.includes('Low')
                          ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          : 'bg-amber-950 text-amber-300 border-amber-800'
                      }`}>
                        {sug.collision_risk}
                      </span>
                    </div>

                    <div className="text-xs text-teal-400 font-mono">{sug.linguistic_tone}</div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {sug.rationale}
                    </p>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-0.5">
                      <div>Stem Origin: <strong className="text-slate-200">{sug.stem_origin}</strong></div>
                      <div>Soundex Code: <strong className="text-slate-200 font-mono">{sug.phonetic_soundex}</strong></div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
                    <a
                      href={sug.uspto_search_link}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline flex items-center space-x-1"
                    >
                      <span>USPTO Search</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                    <a
                      href={sug.wipo_search_link}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-slate-200 flex items-center space-x-1"
                    >
                      <span>WIPO DB</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>

            {/* Existing Competitor Naming Patterns */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Competitor Naming Patterns & Cadence Analysis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {trademark.competitor_naming_patterns.map((pat, pIdx) => (
                  <div key={pIdx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{pat.brand_name}</span>
                      <span className="text-slate-400">{pat.company}</span>
                    </div>
                    <div className="text-slate-300">Analysis: {pat.prefix_suffix_analysis}</div>
                    <div className="text-slate-500">Cadence: {pat.cadence} ({pat.syllable_count} Syllables)</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 6: COMPETITOR INTELLIGENCE & SWOT */}
        {/* ========================================================================= */}
        {activeTab === 'competitors' && competitors && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 6: Competitive Landscape & Positioning</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Competitor Battleground & SWOT Matrix</h1>
                <p className="text-xs text-slate-400 mt-1">Multi-dimensional head-to-head matrix and 2x2 positioning quadrant</p>
              </div>
            </div>

            {/* 2x2 Positioning Quadrant */}
            <PositioningMatrix
              competitors={competitors.competitors}
              targetMolecule={project.target_molecule_name}
              targetBrand={brandDisplayName}
            />

            {/* Competitor Matrix Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {competitors.competitors.length === 0 && (
                <div className="md:col-span-3 p-6 rounded-2xl bg-amber-950/30 border border-amber-800 text-amber-200 text-sm">
                  No source-backed competitor set is available for this molecule/indication. Add verified competitor labels, claims, pricing, and market-share sources before positioning.
                </div>
              )}
              {competitors.competitors.map((comp, cIdx) => (
                <div key={cIdx} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold text-white">{comp.brand_name}</h3>
                      <span className="text-xs font-mono text-brand-400 bg-brand-950 px-2 py-0.5 rounded border border-brand-800">
                        {comp.market_share_percentage}% Share
                      </span>
                    </div>

                    <div className="text-xs text-slate-400">
                      <div>Company: <strong className="text-slate-200">{comp.company}</strong></div>
                      <div>Molecule: <strong className="text-slate-200">{comp.molecule}</strong></div>
                      {comp.price_per_month_usd && (
                        <div>Price/Month: <strong className="text-emerald-400 font-mono">${comp.price_per_month_usd}</strong></div>
                      )}
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                      <span className="text-[10px] text-slate-500 font-bold uppercase">Positioning Angle</span>
                      <p className="text-slate-300 italic">"{comp.positioning}"</p>
                    </div>

                    <div className="space-y-1 text-xs">
                      <span className="text-[10px] text-slate-500 font-bold uppercase">Key Doctor Messaging</span>
                      <p className="text-slate-300">{comp.doctor_messaging}</p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-emerald-400 font-bold block mb-0.5">Strengths</span>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5">
                        {comp.strengths.slice(0, 2).map((s, idx) => (
                          <li key={idx} className="truncate">{s}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <span className="text-rose-400 font-bold block mb-0.5">Weaknesses</span>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5">
                        {comp.weaknesses.slice(0, 2).map((w, idx) => (
                          <li key={idx} className="truncate">{w}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* SWOT Matrix Grid */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Comprehensive SWOT Analysis for {brandDisplayName}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-2">
                  <span className="font-bold text-emerald-400 text-sm block">Strengths</span>
                  <ul className="list-disc list-inside text-slate-200 space-y-1">
                    {competitors.swot_analysis.strengths.map((s, idx) => (
                      <li key={idx} className="leading-relaxed">{s}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-2">
                  <span className="font-bold text-rose-400 text-sm block">Weaknesses</span>
                  <ul className="list-disc list-inside text-slate-200 space-y-1">
                    {competitors.swot_analysis.weaknesses.map((w, idx) => (
                      <li key={idx} className="leading-relaxed">{w}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-800/40 space-y-2">
                  <span className="font-bold text-blue-400 text-sm block">Opportunities</span>
                  <ul className="list-disc list-inside text-slate-200 space-y-1">
                    {competitors.swot_analysis.opportunities.map((o, idx) => (
                      <li key={idx} className="leading-relaxed">{o}</li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
                  <span className="font-bold text-amber-400 text-sm block">Threats</span>
                  <ul className="list-disc list-inside text-slate-200 space-y-1">
                    {competitors.swot_analysis.threats.map((t, idx) => (
                      <li key={idx} className="leading-relaxed">{t}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 7: MARKET SIZING & FORECASTING */}
        {/* ========================================================================= */}
        {activeTab === 'forecast' && forecast && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 7: Epidemiological Sizing & Scenario Forecaster</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Market Sizing & 5-Year Revenue Forecast</h1>
                <p className="text-xs text-slate-400 mt-1">Adjust epidemiological funnel variables and simulate revenue projections</p>
              </div>
            </div>

            {/* Interactive Funnel Sliders Box */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-brand-400" />
                <span>Dynamic Epidemiological Parameters & Pricing Controls</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-xs">
                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-300">Prevalence Rate</span>
                    <span className="text-brand-400 font-mono">{(prevalenceRate * 100).toFixed(1)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.01"
                    max="0.25"
                    step="0.005"
                    value={prevalenceRate}
                    onChange={(e) => setPrevalenceRate(parseFloat(e.target.value))}
                    className="w-full accent-brand-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-300">Diagnosis Rate</span>
                    <span className="text-teal-400 font-mono">{(diagnosedRate * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.30"
                    max="0.95"
                    step="0.01"
                    value={diagnosedRate}
                    onChange={(e) => setDiagnosedRate(parseFloat(e.target.value))}
                    className="w-full accent-teal-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-300">Treatment Rate</span>
                    <span className="text-cyan-400 font-mono">{(treatedRate * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.20"
                    max="0.90"
                    step="0.01"
                    value={treatedRate}
                    onChange={(e) => setTreatedRate(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-300">Annual Net Price (USD)</span>
                    <span className="text-emerald-400 font-mono">${annualCost.toLocaleString()}</span>
                  </div>
                  <input
                    type="range"
                    min="500"
                    max="15000"
                    step="250"
                    value={annualCost}
                    onChange={(e) => setAnnualCost(parseFloat(e.target.value))}
                    className="w-full accent-emerald-500 cursor-pointer"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleRecalculateForecast}
                  className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition shadow-md shadow-brand-500/20"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Update Forecast Model</span>
                </button>
              </div>
            </div>

            {/* Patient Funnel Visualization */}
            <PatientFunnel forecast={forecast} />

            {/* 5-Year Scenario Chart */}
            <ForecastCharts forecast={forecast} />

            {/* Doctor Specialty Segmentation Table */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Target Prescriber Pool & Specialty Segmentation
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">Specialty Segment</th>
                      <th className="p-3">Prescriber Pool Size</th>
                      <th className="p-3">Prescriber Tier</th>
                      <th className="p-3">Priority</th>
                      <th className="p-3">Target Monthly TRx</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {forecast.doctor_specialties.map((doc, dIdx) => (
                      <tr key={dIdx} className="hover:bg-slate-850/50">
                        <td className="p-3 font-semibold text-white">{doc.specialty}</td>
                        <td className="p-3 font-mono">{doc.estimated_pool_size.toLocaleString()} Doctors</td>
                        <td className="p-3">{doc.tier}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            doc.priority_level === 'Very High' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-brand-950 text-brand-300 border border-brand-800'
                          }`}>
                            {doc.priority_level}
                          </span>
                        </td>
                        <td className="p-3 font-mono font-bold text-emerald-400">{doc.prescription_potential_per_month} Rx/Mo</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 8: BRAND PLAN BUILDER */}
        {/* ========================================================================= */}
        {activeTab === 'brand_plan' && brandPlan && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 8: The 12-Section Strategic Brand Architecture</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Pharma Brand Strategy Plan</h1>
                <p className="text-xs text-slate-400 mt-1">Complete commercial and medical plan for {brandDisplayName} ({project.target_molecule_name})</p>
              </div>
              <div className="flex items-center space-x-2">
                <a
                  href={getExportDocxUrl(project.target_molecule_name, brandDisplayName, project.therapy_area, project.primary_indication)}
                  className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition shadow-md shadow-brand-500/20"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Brand Plan (.docx)</span>
                </a>
              </div>
            </div>

            {/* Strategic Pillars Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider block">Brand Mission</span>
                <p className="text-xs text-slate-200 leading-relaxed font-medium">{brandPlan.mission}</p>
              </div>
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                <span className="text-xs font-mono text-brand-400 uppercase tracking-wider block">Brand Vision</span>
                <p className="text-xs text-slate-200 leading-relaxed font-medium">{brandPlan.vision}</p>
              </div>
              <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block">Core Commercial Objective</span>
                <p className="text-xs text-slate-200 leading-relaxed font-medium">{brandPlan.brand_objective}</p>
              </div>
            </div>

            {/* 12 Sections Canvas */}
            <div className="space-y-6">
              {brandPlan.sections.map((sec, sIdx) => (
                <div key={sIdx} className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <h3 className="text-base font-bold text-white">{sec.section_title}</h3>
                    <span className="px-2.5 py-0.5 rounded-full bg-slate-950 text-slate-400 border border-slate-800 text-[10px] font-mono">
                      {sec.section_category}
                    </span>
                  </div>

                  <div className="prose prose-invert text-xs text-slate-300 max-w-none leading-relaxed whitespace-pre-line">
                    {sec.content_markdown}
                  </div>

                  {sec.key_takeaways.length > 0 && (
                    <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-500 mr-2">Key Takeaways:</span>
                      {sec.key_takeaways.map((t, tIdx) => (
                        <span key={tIdx} className="px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-teal-300 font-medium">
                          ✓ {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 9: CREATIVE & COMMERCIAL ASSET STUDIO */}
        {/* ========================================================================= */}
        {activeTab === 'creative' && assets && (
          <div className="space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 9: Commercial & Detailing Collateral</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Commercial Asset & Visual Aid Studio</h1>
                <p className="text-xs text-slate-400 mt-1">Interactive 6-slide doctor detailer storyboard, LBL brief, and MR objection simulator</p>
              </div>
            </div>

            {/* Campaign Theme Banner */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-950 via-slate-900 to-teal-950 border border-brand-800/60 flex flex-wrap items-center justify-between gap-4 shadow-xl">
              <div className="space-y-1">
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Core Campaign Theme</span>
                <h2 className="text-xl font-extrabold text-white">"{assets.campaign_theme}"</h2>
              </div>
              <div className="text-xs text-slate-300 max-w-xs text-right">
                <span className="font-semibold text-brand-300 block">Logo & Visual Direction:</span>
                {assets.logo_direction}
              </div>
            </div>

            {/* 6-Slide Visual Aid Carousel */}
            <VisualAidCarousel slides={assets.visual_aid_slides} brandName={brandDisplayName} />

            {/* Field Force Doctor Objection Simulator */}
            <MRObjectionSimulator objections={assets.mr_objection_handling_guide} brandName={brandDisplayName} />

            {/* Leave-Behind Literature (LBL) Brief */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Leave-Behind Literature (LBL) 2-Page Brief
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <span className="font-bold text-teal-400 block">Page 1: Clinical Evidence & Landmark Curves</span>
                  <p className="text-slate-300 leading-relaxed">{assets.lbl_brief.page_1_clinical_evidence_summary}</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <span className="font-bold text-teal-400 block">Page 2: Dosing Simplicity & Prescribing Info</span>
                  <p className="text-slate-300 leading-relaxed">{assets.lbl_brief.page_2_dosing_and_safety_summary}</p>
                </div>
              </div>
            </div>

            {/* Patient Education Leaflet */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Patient Education Leaflet (Plain Language)
              </h3>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
                <h4 className="font-bold text-white text-sm">{assets.patient_education_leaflet.title}</h4>
                <p className="text-slate-300">{assets.patient_education_leaflet.plain_language_condition_summary}</p>
                <div className="pt-2 border-t border-slate-800">
                  <span className="font-semibold text-emerald-400 block mb-1">How This Medicine Works:</span>
                  <p className="text-slate-300">{assets.patient_education_leaflet.how_this_medicine_works}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODULE 10: REPORT CENTER & MLR AUDIT */}
        {/* ========================================================================= */}
        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-xs font-mono text-teal-400 uppercase tracking-wider">Module 10: Multi-Format Export Center & MLR Governance</span>
                <h1 className="text-2xl font-extrabold text-white mt-0.5">Report Center & Compliance Signoff</h1>
                <p className="text-xs text-slate-400 mt-1">Export high-fidelity Word, PowerPoint, and Excel deliverables and review timestamped audit logs</p>
              </div>
            </div>

            {/* 1-Click Export Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Word Document */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-blue-950 border border-blue-800 flex items-center justify-center text-blue-400">
                    <FileText className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">Complete Brand Plan (.docx)</h3>
                  <p className="text-xs text-slate-400">
                    Draft Word document covering all 12 strategic sections, tables, and review-required appendices.
                  </p>
                </div>
                <a
                  href={getExportDocxUrl(project.target_molecule_name, brandDisplayName, project.therapy_area, project.primary_indication)}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold transition shadow-md shadow-brand-500/20"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Word Plan (.docx)</span>
                </a>
              </div>

              {/* PowerPoint Pitch Deck */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-amber-950 border border-amber-800 flex items-center justify-center text-amber-400">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">Executive Pitch Deck (.pptx)</h3>
                  <p className="text-xs text-slate-400">
                    Draft 16:9 presentation formatted for internal review and commercial launch alignment.
                  </p>
                </div>
                <a
                  href={getExportPptxUrl(project.target_molecule_name, brandDisplayName, project.therapy_area, project.primary_indication)}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition shadow-md shadow-amber-500/20"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Pitch Deck (.pptx)</span>
                </a>
              </div>

              {/* Excel Spreadsheet */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-emerald-950 border border-emerald-800 flex items-center justify-center text-emerald-400">
                    <FileSpreadsheet className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">Financial Forecast Model (.xlsx)</h3>
                  <p className="text-xs text-slate-400">
                    Multi-tab Excel financial workbook with patient funnel parameters, pricing calculations, and 5-year CAGR formulas.
                  </p>
                </div>
                <a
                  href={getExportXlsxUrl(brandDisplayName, project.therapy_area)}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition shadow-md shadow-emerald-500/20"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Model (.xlsx)</span>
                </a>
              </div>

              {/* Printable Monograph Dossier */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-teal-950 border border-teal-800 flex items-center justify-center text-teal-400">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">Product Monograph & Dossier</h3>
                  <p className="text-xs text-slate-400">
                    Printable 15-page equivalent comprehensive scientific monograph formatted for browser print and PDF export.
                  </p>
                </div>
                <Link
                  href={`/project/${project.id}/monograph`}
                  target="_blank"
                  className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold transition shadow-md shadow-teal-500/20"
                >
                  <FileCheck2 className="w-4 h-4" />
                  <span>Open Monograph Dossier</span>
                </Link>
              </div>
            </div>

            {/* MLR Compliance Audit Log Table */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>MLR Review Trail & Source Candidates</span>
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">Audit ID</th>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Action Type</th>
                      <th className="p-3">Item / Claim Reference</th>
                      <th className="p-3">Source Verification</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Reviewer</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {auditTrail.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-850/50">
                        <td className="p-3 font-mono text-teal-400">{log.id}</td>
                        <td className="p-3 font-mono text-slate-400">{log.timestamp}</td>
                        <td className="p-3 font-semibold text-white">{log.action_type}</td>
                        <td className="p-3">{log.item_reference}</td>
                        <td className="p-3 font-mono text-slate-400">{log.verified_source}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px] font-bold">
                            {log.status}
                          </span>
                        </td>
                        <td className="p-3 text-slate-400">{log.auditor}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Interactive AI Brand Strategist Co-Pilot Drawer */}
      <AICoPilotDrawer
        moleculeName={project.target_molecule_name}
        brandName={brandDisplayName}
        therapyArea={project.therapy_area}
        indication={project.primary_indication}
        isOpen={isCoPilotOpen}
        onClose={() => setIsCoPilotOpen(false)}
      />
    </div>
  );
}
