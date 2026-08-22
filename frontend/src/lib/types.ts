export interface Project {
  id: string;
  title: string;
  target_molecule_name: string;
  brand_working_name?: string;
  therapy_area: string;
  primary_indication: string;
  target_geography: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Pharmacokinetics {
  absorption: string;
  bioavailability: string;
  tmax: string;
  distribution: string;
  protein_binding: string;
  metabolism: string;
  cyp_pathways: string[];
  elimination: string;
  half_life: string;
  clearance: string;
}

export interface SpecialPopulations {
  pregnancy: string;
  lactation: string;
  pediatric: string;
  geriatric: string;
  renal_impairment: string;
  hepatic_impairment: string;
}

export interface AdverseEffects {
  common: string[];
  rare: string[];
  serious: string[];
}

export interface MoleculeProfile {
  generic_name: string;
  chemical_name?: string;
  chemical_class: string;
  pharmacological_class: string;
  cas_number?: string;
  pubchem_cid?: number;
  smiles?: string;
  molecular_formula?: string;
  molecular_weight?: number;
  mechanism_of_action: string;
  pharmacodynamics: string;
  pharmacokinetics: Pharmacokinetics;
  approved_indications: string[];
  investigational_indications: string[];
  dosage_forms: string[];
  routes_of_administration: string[];
  standard_dosages: string[];
  contraindications: string[];
  black_box_warnings: string[];
  drug_interactions: string[];
  adverse_effects: AdverseEffects;
  special_populations: SpecialPopulations;
  differentiating_science: string;
  key_targets: string[];
}

export interface ResearchPaper {
  id: string;
  pmid?: string;
  pmcid?: string;
  doi?: string;
  title: string;
  authors: string[];
  journal: string;
  publication_year: number;
  study_type: string;
  evidence_level: string;
  sample_size?: number;
  primary_endpoint_result?: string;
  hazard_ratio?: string;
  relative_risk_reduction?: string;
  p_value?: string;
  key_findings: string;
  limitations: string;
  claim_support_potential: string;
  relevance_score: number;
  url?: string;
}

export interface ClaimEvidenceMapping {
  claim_text: string;
  category: string;
  strength_of_evidence: string;
  supported_by_papers: ResearchPaper[];
  label_status: string;
}

export interface ClinicalTrial {
  nct_id: string;
  title: string;
  acronym?: string;
  sponsor: string;
  sponsor_type: string;
  phase: string;
  status: string;
  indication: string;
  study_design: Record<string, any>;
  interventions: string[];
  primary_endpoints: string[];
  secondary_endpoints: string[];
  enrollment?: number;
  geography: string[];
  start_date?: string;
  completion_date?: string;
  results_available: boolean;
  results_summary?: string;
  competitor_molecules: string[];
  url: string;
}

export interface ClinicalTrialLandscape {
  total_trials_found: number;
  phase_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  landmark_trials: ClinicalTrial[];
  all_trials: ClinicalTrial[];
}

export interface RegulatoryAgencyInfo {
  agency_name: string;
  status: string;
  approval_year?: number;
  innovator_brand_name?: string;
  application_numbers: string[];
  approved_indications: string[];
  dosage_and_administration_summary: string;
  boxed_warnings: string[];
  warnings_and_precautions: string[];
  contraindications: string[];
  source_spl_or_url?: string;
}

export interface RegulatoryIntelligence {
  generic_name: string;
  us_fda: RegulatoryAgencyInfo;
  india_cdsco: RegulatoryAgencyInfo;
  eu_ema: RegulatoryAgencyInfo;
  generic_vs_innovator_status: string;
  patent_expiry_timeline?: string;
  key_label_claims_verified: string[];
  ai_strategic_interpretation: string[];
  compliance_fair_balance_notes: string;
}

export interface TrademarkNameSuggestion {
  name: string;
  rationale: string;
  linguistic_tone: string;
  stem_origin: string;
  phonetic_soundex: string;
  double_metaphone: string;
  collision_risk: string;
  uspto_search_link: string;
  ip_india_search_link: string;
  wipo_search_link: string;
}

export interface CompetitorNamingPattern {
  brand_name: string;
  company: string;
  prefix_suffix_analysis: string;
  syllable_count: number;
  cadence: string;
}

export interface TrademarkIntelligence {
  molecule_name: string;
  existing_brand_names: string[];
  similar_sounding_names: string[];
  competitor_naming_patterns: CompetitorNamingPattern[];
  suggested_brand_names: TrademarkNameSuggestion[];
  trademark_risk_advisory: string;
  ai_generated: boolean;
  requirement_applied: string | null;
  existing_brands_source: 'market_data' | 'reference_class' | 'none';
}

export interface CompetitorProfile {
  id: string;
  molecule: string;
  brand_name: string;
  company: string;
  indication: string;
  strengths_available: string[];
  dosage_form: string;
  price_per_month_usd?: number;
  key_claims: string[];
  positioning: string;
  packaging_direction: string;
  visual_aid_angle: string;
  doctor_messaging: string;
  patient_promise: string;
  strengths: string[];
  weaknesses: string[];
  market_share_percentage: number;
  quadrant_x_efficacy: number;
  quadrant_y_safety_convenience: number;

  // Provenance. "curated" rows carry hand-checked strategy text; "secondary_market"
  // rows are measured sales facts from an ingested audit extract.
  data_source?: 'curated' | 'secondary_market';
  source_label?: string | null;

  // Measured market facts, present only on secondary_market rows.
  market_value?: number | null;
  value_unit?: string | null;
  market_value_prev?: number | null;
  market_growth_percent?: number | null;
  units_latest?: number | null;
  ownership?: string | null;
  pack_count?: number | null;
  period?: string | null;
  is_combination?: boolean;
  therapy_group?: string | null;
  subgroup?: string | null;
}

export interface ClassRival {
  molecule_desc: string;
  molecule_key?: string | null;
  value_latest: number;
  growth_percent?: number | null;
  brand_count: number;
  class_share_percent: number;
}

export interface CompanyShare {
  company: string;
  ownership?: string | null;
  value_latest: number;
  growth_percent?: number | null;
  brand_count: number;
  market_share_percent: number;
}

export interface MarketSummary {
  has_data: boolean;
  market?: string | null;
  period?: string | null;
  value_unit?: string | null;
  market_size?: number | null;
  market_size_prev?: number | null;
  market_growth_percent?: number | null;
  total_brands: number;
  total_companies: number;
  therapy_group?: string | null;
  group_value?: number | null;
  source_files: string[];
}

export interface MarketDataset {
  id: string;
  original_filename: string;
  source_label: string;
  market: string;
  period_label?: string | null;
  value_unit: string;
  row_count: number;
  brand_count: number;
  molecule_count: number;
  company_count: number;
  total_value: number;
  project_id?: string | null;
  upload_file_id?: string | null;
  status: string;
  message?: string | null;
  ingested_at: string;
}

export interface SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface CompetitorIntelligence {
  molecule: string;
  competitors: CompetitorProfile[];
  swot_analysis: SWOTAnalysis;
  positioning_gap_summary: string;
  head_to_head_differentiators: string[];
  market_summary: MarketSummary;
  company_leaderboard: CompanyShare[];
  class_rivals: ClassRival[];
  data_sources: string[];
}

export interface ScenarioProjections {
  year_1: number;
  year_2: number;
  year_3: number;
  year_4: number;
  year_5: number;
  cagr_percentage: number;
}

export interface DoctorSpecialtySegment {
  specialty: string;
  estimated_pool_size: number;
  tier: string;
  priority_level: string;
  expected_reach_rate: number;
  prescription_potential_per_month: number;
}

export interface TradePriceStructure {
  mrp_per_patient_year: number;
  ptr_per_patient_year: number;
  pts_per_patient_year: number;
  retailer_margin_amount: number;
  retailer_margin_percent: number;
  stockist_margin_amount: number;
  stockist_margin_percent: number;
  manufacturer_realization_percent_of_mrp: number;
}

export interface MarketForecast {
  therapy_area: string;
  target_geography: string;
  total_population: number;
  prevalence_rate: number;
  diagnosed_rate: number;
  treated_rate: number;
  brand_adoption_rate_y1: number;
  annual_cost_per_patient_usd: number;
  prevalent_patient_pool: number;
  diagnosed_patient_pool: number;
  treated_patient_pool: number;
  current_therapy_market_size_usd: number;
  therapy_market_cagr: number;
  conservative_scenario: ScenarioProjections;
  realistic_scenario: ScenarioProjections;
  aggressive_scenario: ScenarioProjections;
  doctor_specialties: DoctorSpecialtySegment[];
  region_wise_opportunity: Record<string, string>;
  channel_strategy_breakdown: Record<string, string>;
  trade_price_structure?: TradePriceStructure | null;
  therapy_market_size_inr_at_trade_price?: number | null;
}

export interface BrandPlanSection {
  section_id: string;
  section_title: string;
  section_category: string;
  content_markdown: string;
  key_takeaways: string[];
  citations: Array<{ ref: string; note: string }>;
}

export interface KPIMetric {
  kpi_name: string;
  category: string;
  target_q1: string;
  target_q2: string;
  target_q4: string;
  target_year1: string;
}

export interface MonthlyTacticalMilestone {
  month_number: number;
  month_name: string;
  activity: string;
  responsible_team: string;
  status: string;
}

export interface CompleteBrandPlan {
  project_id: string;
  molecule_name: string;
  brand_name: string;
  therapy_area: string;
  indication: string;
  target_geography: string;
  mission: string;
  vision: string;
  brand_objective: string;
  therapy_area_opportunity: string;
  target_customer_and_patient_profile: string;
  doctor_and_market_insights: string;
  competitor_gap_and_differentiation: string;
  positioning_statement: string;
  brand_promise_and_rtb: string;
  key_messages_and_claim_strategy: string;
  commercial_launch_strategy: string;
  kol_and_cme_strategy: string;
  digital_and_sales_force_strategy: string;
  sections: BrandPlanSection[];
  monthly_action_plan: MonthlyTacticalMilestone[];
  kpi_scorecard: KPIMetric[];
  mlr_compliance_signoff_ready: boolean;
  last_updated: string;
  ai_drafted?: boolean;
  ai_model?: string | null;
  ai_review_flags?: string[];
  ai_status?: 'template' | 'drafted' | 'drafting_failed';
}

export interface VisualAidSlide {
  slide_number: number;
  slide_title: string;
  headline_for_doctor: string;
  visual_concept_description: string;
  clinical_data_chart_description: string;
  key_bullet_points: string[];
  medical_representative_talk_track: string;
  evidence_citation: string;
  safety_fair_balance_footer: string;
}

export interface LBLBrief {
  title: string;
  target_audience: string;
  page_1_content_headline: string;
  page_1_clinical_evidence_summary: string;
  page_2_dosing_and_safety_summary: string;
  call_to_action: string;
  prescribing_info_footnote: string;
}

export interface MRObjectionHandling {
  doctor_objection: string;
  underlying_concern: string;
  recommended_mr_response: string;
  supporting_clinical_trial: string;
  recommended_visual_aid_page: number;
}

export interface PatientEducationLeaflet {
  title: string;
  plain_language_condition_summary: string;
  how_this_medicine_works: string;
  how_to_take_and_adherence: string;
  what_to_expect_and_side_effects: string;
  lifestyle_and_diet_tips: string[];
}

export interface VisualAidBrief {
  molecule_name: string;
  brand_name: string;
  main_indication: string;
  brand_and_pack_shot: string;
  punchline: string;
  clinical_message_points: string[];
  hero_visual_concept: string;
  composition: string;
  scientific_support: string[];
  call_to_prescribe: string;
  image_generation_prompt: string;
  ai_drafted: boolean;
  ai_review_flags: string[];
}

export interface CreativeCommercialAssets {
  molecule_name: string;
  brand_name: string;
  campaign_theme: string;
  logo_direction: string;
  pack_mockup_brief: string;
  visual_aid_slides: VisualAidSlide[];
  lbl_brief: LBLBrief;
  mr_objection_handling_guide: MRObjectionHandling[];
  patient_education_leaflet: PatientEducationLeaflet;
  conference_booth_concept: string;
  digital_email_copy: string;
  banner_ad_copy: string;
}

export interface MLRAuditEntry {
  id: string;
  timestamp: string;
  action_type: string;
  item_reference: string;
  verified_source: string;
  status: string;
  auditor: string;
}

// --- Patent, exclusivity & competitive entry (FDA Orange Book) ---------------

export interface PatentRecord {
  patent_number: string;
  expiry_date: string;
  submission_date?: string | null;
  drug_substance: boolean;
  drug_product: boolean;
  use_code?: string | null;
}

export interface ExclusivityRecord {
  code: string;
  expiry_date: string;
  description?: string | null;
}

export interface MarketedProduct {
  trade_name: string;
  applicant: string;
  applicant_full_name?: string | null;
  strength?: string | null;
  dosage_form_route?: string | null;
  application_type: string;
  application_number: string;
  approval_date?: string | null;
  is_reference_listed_drug: boolean;
  therapeutic_equivalence_code?: string | null;
}

export interface MoleculeLifecycle {
  query: string;
  display_name: string;
  components: string[];
  is_combination: boolean;
  innovator_company?: string | null;
  innovator_brand?: string | null;
  innovator_application?: string | null;
  first_approval_date?: string | null;
  patents: PatentRecord[];
  latest_patent_expiry?: string | null;
  exclusivity: ExclusivityRecord[];
  generic_entrants: MarketedProduct[];
  generic_entrant_count: number;
  first_generic_approval_date?: string | null;
  all_products: MarketedProduct[];
  data_sources: string[];
  coverage_note: string;
  unavailable: string[];
}

export interface UploadedFile {
  id: string;
  project_id: string;
  original_filename: string;
  stored_filename: string;
  size_bytes: number;
  content_type?: string | null;
  uploaded_at: string;
  note?: string | null;
  /** 'queued' when the file was recognised as a market extract and is being parsed. */
  market_ingest?: string | null;
}

// --- Patient experience (FDA FAERS) -----------------------------------------

export interface ReportedProblem {
  term: string;
  report_count: number;
  share_of_reports: number;
}

export interface DemographicSplit {
  label: string;
  count: number;
}

export interface PatientExperience {
  query: string;
  display_name: string;
  components: string[];
  is_combination: boolean;
  total_reports: number;
  serious_reports: number;
  non_serious_reports: number;
  top_reported_problems: ReportedProblem[];
  discontinuation_signals: ReportedProblem[];
  off_label_use_reports: number;
  age_distribution: DemographicSplit[];
  sex_distribution: DemographicSplit[];
  patient_counselling_from_label: string[];
  adherence_considerations: string[];
  data_sources: string[];
  coverage_note: string;
  interpretation_caveat: string;
}

// --- Brand name candidates ---------------------------------------------------

export interface BrandNameCandidate {
  name: string;
  rationale: string;
  construction: string;
  length: number;
  syllable_estimate: number;
  soundex: string;
  exact_collision_with_marketed_brand: boolean;
  phonetic_collision_with_marketed_brand: boolean;
  screening_status: string;
  ip_india_search_url: string;
  ip_india_search_term: string;
  uspto_search_url: string;
  wipo_search_url: string;
  verification_required: string;
  ai_generated?: boolean;
}

export interface BrandNameCandidates {
  molecule: string;
  therapy_area: string;
  indication: string;
  candidates: BrandNameCandidate[];
  screening_basis: string;
  next_step: string;
  ai_generated: boolean;
  requirement_applied: string;
}

// --- CDSCO India checklist ---------------------------------------------------

export interface CDSCOChecklistItem {
  step: string;
  source_register: string;
  url: string;
  what_to_check: string;
  why_it_matters: string;
  blocks_launch: boolean;
}

export interface CDSCOIntelligence {
  query: string;
  display_name: string;
  components: string[];
  is_combination: boolean;
  checklist: CDSCOChecklistItem[];
  blocking_steps: string[];
  automation_note: string;
  india_specific_warning: string;
}

// --- Drug Intelligence -------------------------------------------------------

export interface DrugSourceOut {
  id?: string | null;
  source_name: string;
  source_url?: string | null;
  source_identifier?: string | null;
  data_version?: string | null;
  published_at?: string | null;
  attribution?: string | null;
  confidence: string;
  retrieved_at?: string | null;
}

export interface DrugOut {
  id: string;
  generic_name: string;
  brand_name?: string | null;
  active_ingredients: string[];
  drug_class?: string | null;
  therapeutic_class?: string | null;
  dosage_forms: string[];
  strengths: string[];
  routes: string[];
  manufacturer?: string | null;
  indications?: string | null;
  dosage?: string | null;
  contraindications?: string | null;
  warnings?: string | null;
  precautions?: string | null;
  adverse_effects?: string | null;
  drug_interactions?: string | null;
  pregnancy_information?: string | null;
  lactation_information?: string | null;
  mechanism?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
  sources: DrugSourceOut[];
}

export interface DrugSearchResult {
  items: DrugOut[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  query: string;
  matched_on: string;
  ingested_on_demand: boolean;
  note: string;
}

export interface ComparisonField {
  field: string;
  label: string;
  drug_a_value?: string | null;
  drug_b_value?: string | null;
  both_available: boolean;
  differs: boolean;
}

export interface DrugComparison {
  drug_a?: DrugOut | null;
  drug_b?: DrugOut | null;
  fields: ComparisonField[];
  shared_interactions: unknown[];
  fields_missing_for_both: string[];
  comparison_note: string;
  caveat: string;
}

export interface PMTProductProfile {
  brand?: string | null;
  generic?: string | null;
  molecule?: string | null;
  company?: string | null;
  drug_class?: string | null;
  indication_summary?: string | null;
  dosage_summary?: string | null;
}

export interface PMTAnalysis {
  analysis_type: string;
  disclaimer: string;
  product_profile: PMTProductProfile;
  competitive_products: PMTProductProfile[];
  positioning_observations: string[];
  differentiation_candidates: string[];
  competitive_advantages: string[];
  competitive_disadvantages: string[];
  target_patient_segment: string[];
  target_physician_segment: string[];
  evidence_gaps: string[];
  source_records_used: string[];
}


export interface EvidenceLibrary {
  molecule: string;
  papers: ResearchPaper[];
  /** What PubMed reports exists — always distinct from what is cached locally. */
  total_available: number;
  fetched_count: number;
  returned: number;
  offset: number;
  limit: number;
  complete: boolean;
  source: string;
  fetched_at?: string | null;
  query?: string;
}
