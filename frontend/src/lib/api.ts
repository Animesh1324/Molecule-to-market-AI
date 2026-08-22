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
  VisualAidBrief,
  CoPilotTurn,
  CoPilotResponse,
  MLRAuditEntry,
  MoleculeLifecycle,
  UploadedFile,
  PatientExperience,
  BrandNameCandidates,
  CDSCOIntelligence,
  DrugSearchResult,
  DrugComparison,
  PMTAnalysis,
  MarketDataset,
  EvidenceLibrary
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

const TOKEN_STORAGE_KEY = 'brandplan-api-token';

/** Read the access token the user entered. Empty when the API runs open. */
export function getAccessToken(): string {
  if (typeof window === 'undefined') return '';
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

export function setAccessToken(token: string): void {
  if (typeof window === 'undefined') return;
  try {
    if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // Private browsing: the token simply will not persist across reloads.
  }
}

/**
 * Attach the access token to every API call.
 *
 * The backend rejects unauthenticated requests with 401 once API_ACCESS_TOKEN
 * is set, so this header is what keeps the app working against a secured
 * deployment.
 */
function authHeaders(extra?: HeadersInit): HeadersInit {
  const token = getAccessToken();
  return token ? { ...(extra || {}), 'X-API-Key': token } : (extra || {});
}

/**
 * Raise an Error carrying the API's own `detail` message.
 *
 * The backend validates forecast inputs and returns a specific reason; a
 * generic "Failed to fetch" would hide it and leave the user guessing which
 * assumption was rejected.
 */
async function apiError(res: Response, fallback: string): Promise<Error> {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === 'string') return new Error(detail);
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : null;
      if (first?.msg) return new Error(field ? `${field}: ${first.msg}` : first.msg);
    }
  } catch {
    // Response had no JSON body; fall through to the generic message.
  }
  return new Error(`${fallback} (HTTP ${res.status})`);
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/api/projects`, { cache: 'no-store', headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch projects');
  return res.json();
}

export async function fetchProjectById(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/projects/${id}`, { cache: 'no-store', headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Project not found');
  return res.json();
}

export async function createProject(data: Partial<Project>): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await apiError(res, 'Failed to create project');
  return res.json();
}

export async function fetchMoleculeProfile(moleculeName: string): Promise<MoleculeProfile> {
  const res = await fetch(`${API_BASE}/api/molecules/search?name=${encodeURIComponent(moleculeName)}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch molecule profile');
  return res.json();
}

export async function fetchEvidencePapers(molecule: string, indication?: string): Promise<ResearchPaper[]> {
  const url = `${API_BASE}/api/evidence/papers?molecule=${encodeURIComponent(molecule)}${indication ? `&indication=${encodeURIComponent(indication)}` : ''}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch research papers');
  return res.json();
}

export async function fetchClaimMappings(molecule: string, indication?: string): Promise<ClaimEvidenceMapping[]> {
  const url = `${API_BASE}/api/evidence/claims?molecule=${encodeURIComponent(molecule)}${indication ? `&indication=${encodeURIComponent(indication)}` : ''}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch claim mappings');
  return res.json();
}

export async function fetchClinicalTrials(molecule: string, indication?: string): Promise<ClinicalTrialLandscape> {
  const url = `${API_BASE}/api/trials/landscape?molecule=${encodeURIComponent(molecule)}${indication ? `&indication=${encodeURIComponent(indication)}` : ''}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch clinical trials');
  return res.json();
}

export async function fetchRegulatoryLabels(molecule: string): Promise<RegulatoryIntelligence> {
  const res = await fetch(`${API_BASE}/api/regulatory/labels?molecule=${encodeURIComponent(molecule)}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch regulatory labels');
  return res.json();
}

export async function fetchTrademarkAnalysis(
  molecule: string,
  therapyArea: string = 'Cardiometabolic',
  options?: { indication?: string; requirement?: string; count?: number; exclude?: string[] }
): Promise<TrademarkIntelligence> {
  const params = new URLSearchParams({ molecule, therapy_area: therapyArea });
  if (options?.indication) params.set('indication', options.indication);
  if (options?.requirement) params.set('requirement', options.requirement);
  if (options?.count) params.set('count', String(options.count));
  if (options?.exclude?.length) params.set('exclude', options.exclude.join(','));
  const res = await fetch(`${API_BASE}/api/trademark/analyze?${params.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch trademark analysis');
  return res.json();
}

export async function fetchCompetitors(molecule: string, indication?: string): Promise<CompetitorIntelligence> {
  const url = `${API_BASE}/api/competitors/landscape?molecule=${encodeURIComponent(molecule)}${indication ? `&indication=${encodeURIComponent(indication)}` : ''}`;
  const res = await fetch(url, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch competitor landscape');
  return res.json();
}

export async function fetchMarketForecast(params: {
  therapy_area?: string;
  target_geography?: string;
  total_population?: number;
  prevalence_rate?: number;
  diagnosed_rate?: number;
  treated_rate?: number;
  brand_adoption_rate_y1?: number;
  annual_cost_per_patient_usd?: number;
  mrp_per_patient_year_inr?: number;
  ptr_per_patient_year_inr?: number;
  pts_per_patient_year_inr?: number;
}): Promise<MarketForecast> {
  const q = new URLSearchParams();
  if (params.therapy_area) q.append('therapy_area', params.therapy_area);
  if (params.target_geography) q.append('target_geography', params.target_geography);
  if (params.total_population) q.append('total_population', params.total_population.toString());
  if (params.prevalence_rate !== undefined) q.append('prevalence_rate', params.prevalence_rate.toString());
  if (params.diagnosed_rate !== undefined) q.append('diagnosed_rate', params.diagnosed_rate.toString());
  if (params.treated_rate !== undefined) q.append('treated_rate', params.treated_rate.toString());
  if (params.brand_adoption_rate_y1 !== undefined) q.append('brand_adoption_rate_y1', params.brand_adoption_rate_y1.toString());
  if (params.annual_cost_per_patient_usd !== undefined) q.append('annual_cost_per_patient_usd', params.annual_cost_per_patient_usd.toString());
  if (params.mrp_per_patient_year_inr) q.append('mrp_per_patient_year_inr', params.mrp_per_patient_year_inr.toString());
  if (params.ptr_per_patient_year_inr) q.append('ptr_per_patient_year_inr', params.ptr_per_patient_year_inr.toString());
  if (params.pts_per_patient_year_inr) q.append('pts_per_patient_year_inr', params.pts_per_patient_year_inr.toString());

  const res = await fetch(`${API_BASE}/api/forecasting/model?${q.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch market forecast');
  return res.json();
}

export async function fetchBrandPlan(params: {
  project_id: string;
  molecule: string;
  brand_name?: string;
  therapy_area?: string;
  indication?: string;
  target_geography?: string;
}): Promise<CompleteBrandPlan> {
  const q = new URLSearchParams({
    project_id: params.project_id,
    molecule: params.molecule,
    therapy_area: params.therapy_area || 'Cardiometabolic',
    indication: params.indication || 'Heart Failure & CKD',
    target_geography: params.target_geography || 'Global'
  });
  if (params.brand_name) q.append('brand_name', params.brand_name);

  const res = await fetch(`${API_BASE}/api/brand-plan/generate?${q.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to generate brand plan');
  return res.json();
}

export async function fetchCreativeAssets(molecule: string, brand_name?: string, indication?: string): Promise<CreativeCommercialAssets> {
  const q = new URLSearchParams({ molecule });
  if (brand_name) q.append('brand_name', brand_name);
  if (indication) q.append('indication', indication);

  const res = await fetch(`${API_BASE}/api/assets/generate?${q.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to generate creative assets');
  return res.json();
}

export async function fetchVisualAidBrief(molecule: string, brand_name?: string, indication?: string): Promise<VisualAidBrief> {
  const q = new URLSearchParams({ molecule });
  if (brand_name) q.append('brand_name', brand_name);
  if (indication) q.append('indication', indication);

  const res = await fetch(`${API_BASE}/api/assets/visual-aid-brief?${q.toString()}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to draft the visual aid brief');
  return res.json();
}

export async function askCoPilot(params: {
  molecule: string;
  brand_name: string;
  therapy_area?: string;
  indication?: string;
  question: string;
  history?: CoPilotTurn[];
}): Promise<CoPilotResponse> {
  const res = await fetch(`${API_BASE}/api/copilot/ask`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(params),
  });
  if (!res.ok) throw await apiError(res, 'AI Co-Pilot request failed');
  return res.json();
}

export async function fetchAuditTrail(): Promise<MLRAuditEntry[]> {
  const res = await fetch(`${API_BASE}/api/reports/audit-trail`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch MLR audit trail');
  return res.json();
}

export function getExportDocxUrl(molecule: string, brand_name: string, therapy_area?: string, indication?: string, projectId?: string): string {
  const q = new URLSearchParams({
    molecule,
    brand_name,
    therapy_area: therapy_area || 'Cardiometabolic',
    indication: indication || 'Heart Failure & CKD in T2D'
  });
  if (projectId) q.set('project_id', projectId);
  return `${API_BASE}/api/reports/export/docx?${q.toString()}`;
}

export interface PptxExportForecastState {
  prevalence_rate?: number;
  diagnosed_rate?: number;
  treated_rate?: number;
  brand_adoption_rate_y1?: number;
  annual_cost_per_patient_usd?: number;
  mrp_per_patient_year_inr?: number;
  ptr_per_patient_year_inr?: number;
  pts_per_patient_year_inr?: number;
}

export function getExportPptxUrl(
  molecule: string,
  brand_name: string,
  therapy_area?: string,
  indication?: string,
  projectId?: string,
  forecastState?: PptxExportForecastState,
): string {
  const q = new URLSearchParams({
    molecule,
    brand_name,
    therapy_area: therapy_area || 'Cardiometabolic',
    indication: indication || 'Heart Failure & CKD in T2D'
  });
  if (projectId) q.set('project_id', projectId);
  if (forecastState) {
    for (const [key, value] of Object.entries(forecastState)) {
      if (value !== undefined && value !== null) q.set(key, String(value));
    }
  }
  return `${API_BASE}/api/reports/export/pptx?${q.toString()}`;
}

export function getExportXlsxUrl(brand_name: string, therapy_area?: string): string {
  const q = new URLSearchParams({
    brand_name,
    therapy_area: therapy_area || 'Cardiometabolic'
  });
  return `${API_BASE}/api/reports/export/xlsx?${q.toString()}`;
}

/** Patent, exclusivity, innovator and generic-entry picture (FDA Orange Book). */
export async function fetchMoleculeLifecycle(molecule: string): Promise<MoleculeLifecycle> {
  const res = await fetch(
    `${API_BASE}/api/lifecycle/molecule?molecule=${encodeURIComponent(molecule)}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Failed to fetch molecule lifecycle');
  return res.json();
}

/** One page of the molecule's PubMed literature, with the true corpus size. */
export async function fetchEvidenceLibrary(
  molecule: string,
  indication?: string,
  limit = 100,
  offset = 0,
  refresh = false
): Promise<EvidenceLibrary> {
  const q = new URLSearchParams({
    molecule,
    limit: String(limit),
    offset: String(offset),
  });
  if (indication) q.set('indication', indication);
  if (refresh) q.set('refresh', 'true');
  const res = await fetch(`${API_BASE}/api/evidence/library?${q.toString()}`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to fetch evidence library');
  return res.json();
}

/** Kick off a background pull of the molecule's entire PubMed bibliography. */
export async function fetchEntireCorpus(molecule: string, indication?: string) {
  const q = new URLSearchParams({ molecule });
  if (indication) q.set('indication', indication);
  const res = await fetch(`${API_BASE}/api/evidence/library/fetch-all?${q.toString()}`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to start corpus fetch');
  return res.json();
}

/** Every secondary-data extract ingested into the market tables. */
export interface ManualCompetitor {
  id: string;
  molecule_desc: string;
  brand: string;
  company?: string | null;
  market?: string | null;
  value_estimate?: number | null;
  value_unit?: string | null;
  value_basis?: string | null;
  mrp?: number | null;
  ptr?: number | null;
  pts?: number | null;
  price_unit?: string | null;
  source_note: string;
  added_by: string;
  added_at: string;
}

/** Team-attested competitors for a molecule a licensed extract doesn't cover. */
export async function fetchManualCompetitors(molecule: string): Promise<ManualCompetitor[]> {
  const res = await fetch(
    `${API_BASE}/api/market/competitors/manual?molecule=${encodeURIComponent(molecule)}`,
    { cache: 'no-store', headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Failed to fetch manual competitors');
  return res.json();
}

export async function addManualCompetitor(payload: {
  molecule: string;
  brand: string;
  source_note: string;
  added_by: string;
  company?: string;
  market?: string;
  value_estimate?: number;
  value_unit?: string;
  value_basis?: string;
  mrp?: number;
  ptr?: number;
  pts?: number;
  price_unit?: string;
}): Promise<ManualCompetitor> {
  const res = await fetch(`${API_BASE}/api/market/competitors/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await apiError(res, 'Failed to add competitor');
  return res.json();
}

export async function deleteManualCompetitor(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/market/competitors/manual/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to delete competitor');
}

export async function fetchMarketDatasets(): Promise<MarketDataset[]> {
  const res = await fetch(`${API_BASE}/api/market/datasets`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to list market datasets');
  return res.json();
}

/** Free-text lookup across every ingested extract (brand, molecule, company). */
export async function searchMarket(query: string, limit = 30) {
  const res = await fetch(
    `${API_BASE}/api/market/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Failed to search market data');
  return res.json();
}

export async function deleteMarketDataset(datasetId: string) {
  const res = await fetch(`${API_BASE}/api/market/datasets/${encodeURIComponent(datasetId)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to remove market dataset');
  return res.json();
}

export async function fetchUploads(projectId: string): Promise<UploadedFile[]> {
  const res = await fetch(`${API_BASE}/api/uploads/${encodeURIComponent(projectId)}`, {
    cache: 'no-store',
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to list uploaded files');
  return res.json();
}

export async function uploadSecondaryData(
  projectId: string,
  file: File,
  note?: string
): Promise<UploadedFile> {
  const form = new FormData();
  form.append('project_id', projectId);
  form.append('file', file);
  if (note) form.append('note', note);
  // No Content-Type header: the browser must set the multipart boundary.
  const res = await fetch(`${API_BASE}/api/uploads`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) throw await apiError(res, 'Upload failed');
  return res.json();
}

export async function deleteUpload(projectId: string, fileId: string): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/uploads/${encodeURIComponent(projectId)}/${encodeURIComponent(fileId)}`,
    { method: 'DELETE', headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Could not delete the file');
}

export function getUploadDownloadUrl(projectId: string, fileId: string): string {
  return `${API_BASE}/api/uploads/${encodeURIComponent(projectId)}/${encodeURIComponent(fileId)}/download`;
}

// --- Patient experience, naming, India regulatory ----------------------------

export async function fetchPatientExperience(molecule: string): Promise<PatientExperience> {
  const res = await fetch(
    `${API_BASE}/api/intelligence/patient-experience?molecule=${encodeURIComponent(molecule)}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Failed to fetch patient experience data');
  return res.json();
}

export async function fetchBrandNameCandidates(
  molecule: string,
  therapyArea = '',
  indication = '',
  count = 10,
  requirement = ''
): Promise<BrandNameCandidates> {
  const q = new URLSearchParams({
    molecule,
    therapy_area: therapyArea,
    indication,
    count: String(count),
  });
  if (requirement) q.set('requirement', requirement);
  const res = await fetch(`${API_BASE}/api/intelligence/brand-names?${q}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to generate brand names');
  return res.json();
}

export async function fetchCDSCOIntelligence(
  molecule: string,
  indication = ''
): Promise<CDSCOIntelligence> {
  const q = new URLSearchParams({ molecule, indication });
  const res = await fetch(`${API_BASE}/api/intelligence/cdsco?${q}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw await apiError(res, 'Failed to fetch CDSCO checklist');
  return res.json();
}

// --- Drug Intelligence -------------------------------------------------------

export async function searchDrugs(query: string, pageSize = 10): Promise<DrugSearchResult> {
  const q = new URLSearchParams({ q: query, page_size: String(pageSize) });
  const res = await fetch(`${API_BASE}/api/drugs/search?${q}`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Drug search failed');
  return res.json();
}

export async function compareDrugs(drugA: string, drugB: string): Promise<DrugComparison> {
  const res = await fetch(`${API_BASE}/api/drugs/compare`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ drug_a: drugA, drug_b: drugB }),
  });
  if (!res.ok) throw await apiError(res, 'Drug comparison failed');
  return res.json();
}

export async function fetchPMTAnalysis(
  molecule: string,
  competitors = ''
): Promise<PMTAnalysis> {
  const q = new URLSearchParams();
  if (competitors) q.append('competitors', competitors);
  const res = await fetch(
    `${API_BASE}/api/drugs/pmt/${encodeURIComponent(molecule)}?${q}`,
    { headers: authHeaders() }
  );
  if (!res.ok) throw await apiError(res, 'Failed to build PMT analysis');
  return res.json();
}
