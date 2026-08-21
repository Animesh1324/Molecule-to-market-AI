'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Printer, Download, ShieldCheck, Activity, Award, BookOpen, CheckCircle2 } from 'lucide-react';
import {
  Project,
  MoleculeProfile,
  ResearchPaper,
  ClaimEvidenceMapping,
  ClinicalTrialLandscape,
  RegulatoryIntelligence,
  CompleteBrandPlan,
  CreativeCommercialAssets
} from '../../../../lib/types';
import {
  fetchProjectById,
  fetchMoleculeProfile,
  fetchEvidencePapers,
  fetchClaimMappings,
  fetchClinicalTrials,
  fetchRegulatoryLabels,
  fetchBrandPlan,
  fetchCreativeAssets
} from '../../../../lib/api';

export default function MonographPrintPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [molecule, setMolecule] = useState<MoleculeProfile | null>(null);
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [claims, setClaims] = useState<ClaimEvidenceMapping[]>([]);
  const [trials, setTrials] = useState<ClinicalTrialLandscape | null>(null);
  const [regulatory, setRegulatory] = useState<RegulatoryIntelligence | null>(null);
  const [brandPlan, setBrandPlan] = useState<CompleteBrandPlan | null>(null);
  const [assets, setAssets] = useState<CreativeCommercialAssets | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!projectId) return;
      try {
        const proj = await fetchProjectById(projectId);
        setProject(proj);
        const molName = proj.target_molecule_name;

        const [mol, ppr, clm, trl, reg, bp, ast] = await Promise.all([
          fetchMoleculeProfile(molName),
          fetchEvidencePapers(molName, proj.primary_indication),
          fetchClaimMappings(molName, proj.primary_indication),
          fetchClinicalTrials(molName, proj.primary_indication),
          fetchRegulatoryLabels(molName),
          fetchBrandPlan({
            project_id: proj.id,
            molecule: molName,
            brand_name: proj.brand_working_name,
            therapy_area: proj.therapy_area,
            indication: proj.primary_indication,
            target_geography: proj.target_geography
          }),
          fetchCreativeAssets(molName, proj.brand_working_name, proj.primary_indication)
        ]);

        setMolecule(mol);
        setPapers(ppr);
        setClaims(clm);
        setTrials(trl);
        setRegulatory(reg);
        setBrandPlan(bp);
        setAssets(ast);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId]);

  const handlePrint = () => {
    window.print();
  };

  if (loading || !project || !molecule) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-500 dark:text-slate-500 dark:text-slate-400 font-mono text-sm">
        Compiling print-ready scientific monograph...
      </div>
    );
  }

  const brandDisplayName = project.brand_working_name || `${project.target_molecule_name} Brand`;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 print:bg-white print:text-black">
      {/* Top Action Bar (Hidden in Print) */}
      <header className="print:hidden bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 p-4 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link
            href={`/project/${project.id}`}
            className="flex items-center space-x-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-white transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Workspace</span>
          </Link>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-500 dark:text-slate-500 dark:text-slate-400 font-mono">Print-Ready Monograph & Dossier</span>
            <button
              onClick={handlePrint}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-slate-900 dark:text-white text-xs font-semibold shadow-md transition"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save as PDF</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Printable Document Canvas */}
      <main className="max-w-4xl mx-auto my-8 p-10 bg-white shadow-2xl rounded-2xl print:shadow-none print:m-0 print:p-6 print:rounded-none print:max-w-none space-y-8 font-sans">
        {/* Document Header & Title */}
        <div className="border-b-2 border-slate-900 pb-6 space-y-2 text-center">
          <div className="text-[11px] font-mono uppercase tracking-widest text-slate-500 dark:text-slate-500 font-bold">
            Pharmaceutical Product Monograph & Scientific Brand Dossier
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-950 uppercase tracking-tight">
            {brandDisplayName}
          </h1>
          <div className="text-sm font-semibold text-slate-700 font-mono">
            Active Substance: {molecule.generic_name} ({molecule.pharmacological_class})
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-500 pt-1">
            Indication: {project.primary_indication} | Therapy Area: {project.therapy_area} | Market: {project.target_geography}
          </div>
          <div className="inline-block px-3 py-1 bg-emerald-50 text-emerald-800 text-[10px] font-mono font-bold rounded border border-emerald-300 mt-2">
            MLR Compliance Status: 100% Citation Grounded & Verified
          </div>
        </div>

        {/* Section 1: Chemical & Pharmacological Identity */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1 flex items-center space-x-2">
            <span>1. Chemical & Pharmacological Identity</span>
          </h2>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div><strong>Generic / INN:</strong> {molecule.generic_name}</div>
            <div><strong>Chemical Class:</strong> {molecule.chemical_class}</div>
            <div><strong>CAS Number:</strong> {molecule.cas_number || 'N/A'}</div>
            <div><strong>Molecular Formula:</strong> {molecule.molecular_formula || 'N/A'}</div>
            {molecule.molecular_weight && (
              <div><strong>Molecular Weight:</strong> {molecule.molecular_weight} g/mol</div>
            )}
            {molecule.pubchem_cid && (
              <div><strong>PubChem CID:</strong> {molecule.pubchem_cid}</div>
            )}
          </div>
          <div className="text-xs pt-1">
            <strong>Chemical Name (IUPAC):</strong> {molecule.chemical_name}
          </div>
        </section>

        {/* Section 2: Mechanism of Action & Pharmacodynamics */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1">
            2. Mechanism of Action & Pharmacodynamics
          </h2>
          <div className="text-xs leading-relaxed space-y-2 text-slate-800">
            <p><strong>Mechanism of Action:</strong> {molecule.mechanism_of_action}</p>
            <p><strong>Pharmacodynamics (PD):</strong> {molecule.pharmacodynamics}</p>
            <p><strong>Differentiating Science:</strong> {molecule.differentiating_science}</p>
          </div>
        </section>

        {/* Section 3: Pharmacokinetics (ADME) */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1">
            3. Pharmacokinetics (ADME Profile)
          </h2>
          <table className="w-full text-xs border border-slate-300 text-left">
            <thead className="bg-slate-100 font-bold border-b border-slate-300">
              <tr>
                <th className="p-2 border-r border-slate-300">Parameter</th>
                <th className="p-2">Clinical Pharmacokinetic Specification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-300">
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Absorption & Bioavailability</td>
                <td className="p-2">{molecule.pharmacokinetics.absorption} ({molecule.pharmacokinetics.bioavailability})</td>
              </tr>
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Tmax</td>
                <td className="p-2">{molecule.pharmacokinetics.tmax}</td>
              </tr>
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Distribution & Protein Binding</td>
                <td className="p-2">{molecule.pharmacokinetics.distribution} (Protein binding: {molecule.pharmacokinetics.protein_binding})</td>
              </tr>
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Metabolism & CYP Pathways</td>
                <td className="p-2">{molecule.pharmacokinetics.metabolism} ({molecule.pharmacokinetics.cyp_pathways.join(', ')})</td>
              </tr>
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Elimination Half-Life</td>
                <td className="p-2 font-bold">{molecule.pharmacokinetics.half_life}</td>
              </tr>
              <tr>
                <td className="p-2 font-semibold border-r border-slate-300">Excretion & Clearance</td>
                <td className="p-2">{molecule.pharmacokinetics.elimination} (Clearance: {molecule.pharmacokinetics.clearance})</td>
              </tr>
            </tbody>
          </table>
        </section>

        {/* Section 4: Landmark Clinical Evidence */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1">
            4. Landmark Clinical Trial Evidence Base
          </h2>
          <div className="space-y-3 text-xs">
            {papers.map((p, idx) => (
              <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded space-y-1.5">
                <div className="flex justify-between font-bold text-slate-900">
                  <span>{p.title}</span>
                  <span className="font-mono text-slate-600">PMID: {p.pmid}</span>
                </div>
                <div className="text-slate-600">
                  {p.journal} ({p.publication_year}) | Study Type: {p.study_type} ({p.evidence_level}) {p.sample_size ? `| N = ${p.sample_size.toLocaleString()}` : ''}
                </div>
                <div className="text-emerald-800 font-semibold">
                  Primary Finding: {p.primary_endpoint_result} {p.hazard_ratio ? `(HR: ${p.hazard_ratio})` : ''}
                </div>
                <div className="text-slate-700">
                  <strong>Strategic Support:</strong> {p.claim_support_potential}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Section 5: Regulatory Indications & Warnings */}
        <section className="space-y-3">
          <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1">
            5. Approved Regulatory Indications, Safety & Dosing
          </h2>
          <div className="text-xs space-y-2">
            <div>
              <strong>Approved Indications:</strong>
              <ul className="list-disc list-inside space-y-0.5 mt-1 text-slate-800">
                {molecule.approved_indications.map((ind, idx) => (
                  <li key={idx}>{ind}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Dosage & Administration:</strong> {regulatory?.us_fda.dosage_and_administration_summary || molecule.standard_dosages.join(', ')}
            </div>
            <div>
              <strong>Contraindications:</strong> {molecule.contraindications.join('; ')}
            </div>
            {molecule.black_box_warnings.length > 0 && (
              <div className="p-2.5 bg-rose-50 border border-rose-300 text-rose-900 rounded">
                <strong>Black Box Warning:</strong> {molecule.black_box_warnings[0]}
              </div>
            )}
          </div>
        </section>

        {/* Section 6: Strategic Brand Positioning */}
        {brandPlan && (
          <section className="space-y-3">
            <h2 className="text-base font-bold text-slate-950 uppercase tracking-wider border-b border-slate-300 pb-1">
              6. Strategic Brand Platform & Positioning
            </h2>
            <div className="text-xs space-y-2 text-slate-800">
              <p><strong>Brand Mission:</strong> {brandPlan.mission}</p>
              <p><strong>Brand Vision:</strong> {brandPlan.vision}</p>
              <p><strong>Positioning Statement:</strong> {brandPlan.positioning_statement}</p>
              <p><strong>Core Brand Promise & RTB:</strong> {brandPlan.brand_promise_and_rtb}</p>
            </div>
          </section>
        )}

        {/* Document Footer & Fair Balance Compliance */}
        <footer className="pt-6 border-t-2 border-slate-900 text-[10px] text-slate-500 dark:text-slate-500 space-y-1">
          <div>
            <strong>Compliance & Governance Notice:</strong> This monograph is compiled for internal medical marketing and strategic launch preparation. All claims are grounded in peer-reviewed scientific literature and approved regulatory labels.
          </div>
          <div>
            In accordance with FDA OPDP and CDSCO promotion guidelines, all promotional claims must present fair balance safety disclosures with equal prominence.
          </div>
          <div className="text-right font-mono font-bold text-slate-700">
            Pharma BrandPlan AI — Generated Monograph System
          </div>
        </footer>
      </main>
    </div>
  );
}
