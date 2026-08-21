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
  MLRAuditEntry,
  MoleculeLifecycle,
  UploadedFile
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

export async function fetchTrademarkAnalysis(molecule: string, therapyArea: string = 'Cardiometabolic'): Promise<TrademarkIntelligence> {
  const res = await fetch(`${API_BASE}/api/trademark/analyze?molecule=${encodeURIComponent(molecule)}&therapy_area=${encodeURIComponent(therapyArea)}`, { headers: authHeaders() });
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

export async function fetchAuditTrail(): Promise<MLRAuditEntry[]> {
  const res = await fetch(`${API_BASE}/api/reports/audit-trail`, { headers: authHeaders() });
  if (!res.ok) throw await apiError(res, 'Failed to fetch MLR audit trail');
  return res.json();
}

export function getExportDocxUrl(molecule: string, brand_name: string, therapy_area?: string, indication?: string): string {
  const q = new URLSearchParams({
    molecule,
    brand_name,
    therapy_area: therapy_area || 'Cardiometabolic',
    indication: indication || 'Heart Failure & CKD in T2D'
  });
  return `${API_BASE}/api/reports/export/docx?${q.toString()}`;
}

export function getExportPptxUrl(molecule: string, brand_name: string, therapy_area?: string, indication?: string): string {
  const q = new URLSearchParams({
    molecule,
    brand_name,
    therapy_area: therapy_area || 'Cardiometabolic',
    indication: indication || 'Heart Failure & CKD in T2D'
  });
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
