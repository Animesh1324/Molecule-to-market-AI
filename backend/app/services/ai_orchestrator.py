from datetime import datetime
from typing import Dict, Any, List, Optional
from ..models.brand_plan import CompleteBrandPlan, BrandPlanSection, KPIMetric, MonthlyTacticalMilestone
from ..models.assets import CreativeCommercialAssets, VisualAidSlide, LBLBrief, MRObjectionHandling, PatientEducationLeaflet

def _competitor_section_text(competitor_data: Optional[Dict[str, Any]]) -> tuple:
    """Real competitor facts for the template, or the honest placeholder.

    Only ever states what `competitor_data` itself already measured — the
    brand names, companies, share, and growth `generate_competitor_intelligence`
    sourced from a licensed extract or a team's own attested entry. Nothing
    here infers a strategy or a claim; that stays explicitly marked as pending
    review, same as before this data existed.
    """
    if not competitor_data:
        return (
            "### Competitive Defense & Differentiation Gap\n\nBuild competitor "
            "comparison from verified labels, trial publications, pricing sources, "
            "access data, and approved claim language.",
            "Differentiation pending source-backed competitor and label comparison.",
        )

    rows = competitor_data.get("competitors") or []
    summary = competitor_data.get("market_summary") or {}
    if not rows:
        return (
            "### Competitive Defense & Differentiation Gap\n\nNo source-backed "
            "competitor set is on file for this molecule yet. Upload a licensed "
            "market extract, or record a known competitor manually, before this "
            "section can be built.",
            "Differentiation pending source-backed competitor and label comparison.",
        )

    lines = ["### Competitive Defense & Differentiation Gap", ""]
    if summary.get("has_data"):
        lines.append(
            f"**Measured market**: {summary.get('market_size')} {summary.get('value_unit')} "
            f"across {summary.get('total_brands')} brands and {summary.get('total_companies')} "
            f"companies in {summary.get('market')} ({summary.get('period')})."
        )
        lines.append("")
    lines.append("**Brands on file:**")
    for row in rows[:8]:
        share = row.get("market_share_percentage")
        share_text = f" — {share:.1f}% share" if share else ""
        tag = " *(team-attested, unaudited)*" if row.get("data_source") == "manual" else ""
        lines.append(f"- {row.get('brand_name')} ({row.get('company')}){share_text}{tag}")
    lines.append("")
    lines.append(
        "Positioning, claims, and messaging above are not yet drafted — the "
        "figures here are measured facts, not a differentiation strategy. "
        "Complete that comparison against verified labels and approved claim "
        "language before use."
    )

    gap_text = (
        f"{len(rows)} competitor(s) on file for this molecule "
        f"({summary.get('period', 'no licensed period on file')}). Positioning and "
        "claim-level differentiation still require source-backed comparison."
    )
    return "\n".join(lines), gap_text


def generate_strategic_brand_plan(
    project_id: str,
    molecule_name: str,
    brand_name: Optional[str] = None,
    therapy_area: str = "Cardiometabolic",
    indication: str = "Heart Failure & Chronic Kidney Disease in Type 2 Diabetes",
    target_geography: str = "Global",
    competitor_data: Optional[Dict[str, Any]] = None,
) -> CompleteBrandPlan:
    """Create a draft brand plan scaffold.

    This function is deliberately conservative: it produces planning structure
    and placeholders, not verified medical claims. MLR signoff is false until
    claim-level evidence and label review are completed.

    `competitor_data` (from `generate_competitor_intelligence`) is optional and
    additive: when supplied, the competitive-defense section states the real
    brands, companies, and measured share already on file instead of a bare
    placeholder — every other section is unaffected.
    """
    competitor_markdown, competitor_gap_text = _competitor_section_text(competitor_data)
    
    brand = brand_name or f"{molecule_name.title()} Brand"
    mol = molecule_name.title()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    mission = f"To define a source-backed launch strategy for {brand} ({mol}) in {indication}, pending medical, regulatory, legal, and market-access review."
    
    vision = f"To build a compliant, evidence-led brand plan for {therapy_area} across {target_geography}, with all claims traceable to approved labels or reviewed literature."
    
    obj = "Define editable commercial assumptions, evidence gaps, target segments, launch activities, and KPIs before any external promotional use."
    
    sections = [
        BrandPlanSection(
            section_id="sec-1",
            section_title="1. Executive Summary & Brand Charter",
            section_category="Strategic Foundation",
            content_markdown=(
                f"### Brand Charter for {brand}\n\n"
                f"- **Molecule**: {mol}\n"
                f"- **Core Indication**: {indication}\n"
                f"- **Geography**: {target_geography}\n\n"
                "Before drafting the strategic ambition, confirm:\n"
                "- Label status\n"
                "- Clinical evidence strength\n"
                "- Unmet need\n"
                "- Reimbursement context\n"
                "- Competitor claims"
            ),
            key_takeaways=["Draft strategy scaffold", "Requires source-backed completion"],
            citations=[{"ref": "REVIEW_REQUIRED", "note": "No automatic MLR signoff"}]
        ),
        BrandPlanSection(
            section_id="sec-2",
            section_title="2. Molecule Scientific Platform & MoA",
            section_category="Clinical Science",
            content_markdown=(
                f"### The Scientific Platform of {mol}\n\n"
                "Insert from approved labels and reviewed references:\n"
                "- Verified mechanism of action\n"
                "- Pharmacodynamics\n"
                "- Pharmacokinetics\n"
                "- Dosing\n"
                "- Safety profile"
            ),
            key_takeaways=["Verify MOA", "Verify PK/PD", "Verify safety"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "Regulatory label and pharmacology review required"}]
        ),
        BrandPlanSection(
            section_id="sec-3",
            section_title="3. Epidemiology & Unmet Medical Need",
            section_category="Market Context",
            content_markdown=(
                f"### Disease Burden and Therapeutic Gaps\n\n"
                f"Document, for {indication} in {target_geography}:\n"
                "- Sourced epidemiology\n"
                "- Diagnosis and treatment rates\n"
                "- Patient journey friction points\n"
                "- Unmet needs"
            ),
            key_takeaways=["Add sourced patient pool", "Add treatment gap evidence"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "Epidemiology source required"}]
        ),
        BrandPlanSection(
            section_id="sec-4",
            section_title="4. Landmark Clinical Evidence & Study Hierarchy",
            section_category="Clinical Science",
            content_markdown=(
                "### Clinical Evidence Hierarchy\n\n"
                "- List pivotal trials, systematic reviews, guidelines, and real-world evidence.\n"
                "- Do not add effect sizes, p-values, or superiority language until each claim is traced to a citation."
            ),
            key_takeaways=["Rank evidence", "Map claims to PMID/DOI/label"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "Claim-level evidence required"}]
        ),
        BrandPlanSection(
            section_id="sec-5",
            section_title="5. Regulatory Landscape & Labeling Fact Base",
            section_category="Regulatory",
            content_markdown=(
                "### Regulatory Landscape & Labeling Fact Base\n\n"
                "Confirm, for each target jurisdiction before release:\n"
                "- Approval status\n"
                "- Indications\n"
                "- Contraindications\n"
                "- Warnings\n"
                "- Dosage\n"
                "- Promotional boundaries"
            ),
            key_takeaways=["Verify label status", "Define fair-balance requirements"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "DailyMed/EMA/CDSCO review required"}]
        ),
        BrandPlanSection(
            section_id="sec-6",
            section_title="6. Competitive Defense & Differentiation Gap",
            section_category="Commercial Strategy",
            content_markdown=competitor_markdown,
            key_takeaways=["No unsourced superiority claims", "Add competitor claim sources"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "Competitor source review required"}]
        ),
        BrandPlanSection(
            section_id="sec-7",
            section_title="7. Target Customer & Patient Personas",
            section_category="Commercial Strategy",
            content_markdown=f"### Prescriber & Patient Segmentation\n\n- **Primary Prescribers**: Define the Tier A specialties that treat {indication} and validate pool sizes for {target_geography}.\n- **Patient Persona**: Define the target patient for {indication} — age, comorbidity burden, treatment history, and the outcome they are seeking.",
            key_takeaways=["Validate Tier A specialty mix before allocating field effort", "Empower patients with disease awareness tools"],
            citations=[{"ref": "ASSUMPTION", "note": "Segment sizing requires sourced validation"}]
        ),
        BrandPlanSection(
            section_id="sec-8",
            section_title="8. Brand Positioning & Core Promise",
            section_category="Brand Identity",
            content_markdown=(
                "### Positioning Statement\n\n"
                "- Draft positioning only within the verified indication and label boundaries.\n"
                "- Mark any aspirational positioning as internal strategy, not promotional copy."
            ),
            key_takeaways=["Stay within label", "Separate strategy from claims"],
            citations=[{"ref": "REVIEW_REQUIRED", "note": "Positioning requires MLR/legal review"}]
        ),
        BrandPlanSection(
            section_id="sec-9",
            section_title="9. Key Promotional Messages & RTB Strategy",
            section_category="Brand Identity",
            content_markdown=(
                "### Core Reasons to Believe (RTB)\n\n"
                "Add only claims that have all of the following:\n"
                "- A mapped label/evidence source\n"
                "- The jurisdiction it applies to\n"
                "- The intended audience\n"
                "- Required safety balance\n"
                "- Reviewer approval"
            ),
            key_takeaways=["Claim text pending", "Safety balance pending", "Review pending"],
            citations=[{"ref": "SOURCE_NEEDED", "note": "RTB evidence map required"}]
        ),
        BrandPlanSection(
            section_id="sec-10",
            section_title="10. Multi-Channel Commercial Launch Plan",
            section_category="Execution",
            content_markdown=(
                "### Integrated Go-To-Market Execution\n\n"
                "Draft launch activities across:\n"
                "- Field force\n"
                "- Medical education\n"
                "- Digital\n"
                "- Market access\n"
                "- Internal enablement\n\n"
                "External-facing assets must wait for approved claims."
            ),
            key_takeaways=["3-Pillar commercial launch", "Rapid hospital formulary penetration in Month 1-3"],
            citations=[{"ref": "Commercial Launch Playbook", "note": "Omnichannel Strategy"}]
        ),
        BrandPlanSection(
            section_id="sec-11",
            section_title="11. KOL Advocacy & CME Education Roadmap",
            section_category="Medical Affairs",
            content_markdown=(
                "### Scientific Engagement & Medical Affairs\n\n"
                f"- Establish a National Advisory Board drawn from leading specialists in {therapy_area}.\n"
                "- Plan regional Clinical Masterclasses (CMEs).\n"
                "- Plan investigator-initiated real-world registries.\n"
                "- Confirm board size, cadence, and budget against local transparency and anti-bribery codes."
            ),
            key_takeaways=["Top-down scientific endorsement", "Peer-to-peer physician education"],
            citations=[{"ref": "Medical Affairs Strategy", "note": "KOL Engagement Framework"}]
        ),
        BrandPlanSection(
            section_id="sec-12",
            section_title="12. Balanced KPI Scorecard & Compliance Audit",
            section_category="Governance",
            content_markdown=(
                "### Commercial and Clinical Metrics\n\n"
                "Track monthly:\n"
                "- New-to-Brand Prescriptions (NBRx)\n"
                "- Total Prescriptions (TRx)\n"
                "- Tier-A doctor call frequency (target >3 calls/month)\n\n"
                "Ensure 100% compliance with FDA OPDP and CDSCO promotion guidelines."
            ),
            key_takeaways=["Monthly NBRx tracking", "Strict promotional compliance and Fair Balance auditing"],
            citations=[{"ref": "MLR Standard Operating Procedures", "note": "Compliance Audit Trail"}]
        )
    ]
    
    milestones = [
        MonthlyTacticalMilestone(month_number=1, month_name="Month 1", activity="National Sales Force Training & Certification on Landmark Evidence", responsible_team="Brand & Medical"),
        MonthlyTacticalMilestone(month_number=2, month_name="Month 2", activity="Official Commercial Launch & National Advisory Board Meeting", responsible_team="Brand Team"),
        MonthlyTacticalMilestone(month_number=3, month_name="Month 3", activity="Top 100 Hospital Formulary Applications Submitted", responsible_team="Market Access"),
        MonthlyTacticalMilestone(month_number=4, month_name="Month 4", activity="Regional CME Masterclass Series Kickoff (20 Cities)", responsible_team="Medical Affairs"),
        MonthlyTacticalMilestone(month_number=6, month_name="Month 6", activity="Mid-Year TRx Review & Digital Omnichannel Scale-Up", responsible_team="Brand Team"),
        MonthlyTacticalMilestone(month_number=9, month_name="Month 9", activity="Real-World Patient Registry Interim Analysis Release", responsible_team="Medical Affairs"),
        MonthlyTacticalMilestone(month_number=12, month_name="Month 12", activity="Annual Brand Review & Year 2 Strategy Refinement", responsible_team="Executive Leadership")
    ]
    
    kpis = [
        KPIMetric(kpi_name="Evidence Gaps Closed", category="Medical/Clinical", target_q1="80%", target_q2="100%", target_q4="100%", target_year1="100%"),
        KPIMetric(kpi_name="MLR-Approved Claims", category="Governance", target_q1="0", target_q2="TBD", target_q4="TBD", target_year1="TBD"),
        KPIMetric(kpi_name="Validated Forecast Assumptions", category="Commercial", target_q1="50%", target_q2="90%", target_q4="100%", target_year1="100%"),
        KPIMetric(kpi_name="Target Segment Validation", category="Prescriber Reach", target_q1="Draft", target_q2="Validated", target_q4="Validated", target_year1="Validated")
    ]
    
    return CompleteBrandPlan(
        project_id=project_id,
        molecule_name=mol,
        brand_name=brand,
        therapy_area=therapy_area,
        indication=indication,
        target_geography=target_geography,
        mission=mission,
        vision=vision,
        brand_objective=obj,
        therapy_area_opportunity=f"Opportunity sizing for {therapy_area} requires sourced epidemiology and access assumptions.",
        target_customer_and_patient_profile=f"Specialist and generalist segments should be validated for {indication} in {target_geography}.",
        doctor_and_market_insights="Insights are placeholders until validated by market research or advisory input.",
        competitor_gap_and_differentiation=competitor_gap_text,
        positioning_statement=f"Draft positioning for {brand}; final claims require MLR and legal approval.",
        brand_promise_and_rtb="Reasons to believe pending citation-level evidence mapping.",
        key_messages_and_claim_strategy="Key messages are not claim-ready until evidence, label, and fair-balance review are complete.",
        commercial_launch_strategy=f"Internal launch planning scaffold for {target_geography}.",
        kol_and_cme_strategy=f"National Advisory Board + regional masterclass clinical workshops.",
        digital_and_sales_force_strategy=f"Closed-loop marketing visual aids and doctor digital portal integration.",
        sections=sections,
        monthly_action_plan=milestones,
        kpi_scorecard=kpis,
        mlr_compliance_signoff_ready=False,
        last_updated=now_str
    )

def generate_commercial_assets(
    molecule_name: str,
    brand_name: Optional[str] = None,
    indication: str = "Heart Failure & Chronic Kidney Disease in Type 2 Diabetes"
) -> CreativeCommercialAssets:
    """Generate draft commercial asset briefs for internal review only."""
    
    brand = brand_name or f"{molecule_name.title()} Brand"
    mol = molecule_name.title()
    
    slides = [
        VisualAidSlide(
            slide_number=1,
            slide_title="Slide 1: Clinical Hook & Unmet Need",
            headline_for_doctor="Unmet Need and Patient Burden: Draft Visual Hook",
            visual_concept_description="Concept visual showing the patient journey, disease burden, and treatment decision points for review.",
            clinical_data_chart_description="Placeholder for sourced epidemiology chart. Add citation, geography, date, and population definition before use.",
            key_bullet_points=[
                "Insert sourced unmet-need statement.",
                "Insert approved disease-state fact.",
                "Keep product claims out until label and evidence mapping are complete."
            ],
            medical_representative_talk_track=f"Draft only: discuss the validated unmet need for {indication}. Do not make efficacy or safety claims until approved by MLR.",
            evidence_citation="SOURCE_NEEDED: epidemiology/guideline source",
            safety_fair_balance_footer="Internal draft. Add approved safety information and fair balance before external use."
        ),
        VisualAidSlide(
            slide_number=2,
            slide_title="Slide 2: The Breakthrough Mechanism",
            headline_for_doctor=f"Mechanism of Action: {mol} Scientific Storyboard",
            visual_concept_description="Mechanism diagram concept pending validated pharmacology and label review.",
            clinical_data_chart_description="Placeholder for approved MOA diagram with source attribution.",
            key_bullet_points=[
                "Insert validated target/pathway.",
                "Insert label-consistent pharmacology language.",
                "Flag any mechanistic inference as interpretation."
            ],
            medical_representative_talk_track=f"Draft only: explain the verified mechanism for {brand} using approved, source-backed language.",
            evidence_citation="SOURCE_NEEDED: pharmacology/label source",
            safety_fair_balance_footer="Contraindications must be copied from the approved local label."
        ),
        VisualAidSlide(
            slide_number=3,
            slide_title="Slide 3: Landmark Survival Efficacy",
            headline_for_doctor="Clinical Evidence Summary: Insert Verified Endpoint",
            visual_concept_description="Concept: outcome curve for the reviewed primary endpoint, showing the treatment and comparator arms. Confirm the endpoint type before choosing the chart form.",
            clinical_data_chart_description="Placeholder for approved clinical chart. Add PMID/DOI, population, endpoint, comparator, and confidence interval.",
            key_bullet_points=[
                "Insert verified primary endpoint result.",
                "Insert validated comparator and population.",
                "Confirm on-label use and required limitations."
            ],
            medical_representative_talk_track=f"Draft only: summarize reviewed evidence for {brand}. Do not include effect sizes until checked against the source publication.",
            evidence_citation="SOURCE_NEEDED: trial publication and label",
            safety_fair_balance_footer="Add local prescribing information and fair-balance safety text."
        ),
        VisualAidSlide(
            slide_number=4,
            slide_title="Slide 4: Secondary Endpoint or Biomarker Story",
            headline_for_doctor="Outcome or Biomarker Story: Draft Placeholder",
            visual_concept_description="Concept: longitudinal trajectory of the reviewed secondary endpoint or biomarker versus comparator. Insert the verified measure before design.",
            clinical_data_chart_description="Placeholder for sourced outcome or biomarker chart.",
            key_bullet_points=[
                "Insert source-backed endpoint.",
                "Clarify approved vs investigational context.",
                "Include limitations and safety caveats."
            ],
            medical_representative_talk_track=f"Draft only: use label-consistent language for {brand} and avoid unapproved outcome claims.",
            evidence_citation="SOURCE_NEEDED",
            safety_fair_balance_footer="Add adverse reactions and warnings from approved label."
        ),
        VisualAidSlide(
            slide_number=5,
            slide_title="Slide 5: Safety, Tolerability & Dosing Simplicity",
            headline_for_doctor="Dosing and Safety: Label-Verified Content Required",
            visual_concept_description="Concept: dosage form and administration schedule graphic. Insert the approved strength, form, and route from the local label before design.",
            clinical_data_chart_description="Placeholder for adverse event table from approved label or reviewed study.",
            key_bullet_points=[
                "Insert approved dose and route.",
                "Insert contraindications and warnings.",
                "Insert common adverse reactions with source."
            ],
            medical_representative_talk_track=f"Draft only: dosing and safety for {brand} must match the approved local prescribing information.",
            evidence_citation="SOURCE_NEEDED: approved prescribing information",
            safety_fair_balance_footer="Fair balance required before external use."
        ),
        VisualAidSlide(
            slide_number=6,
            slide_title="Slide 6: The Brand Commitment",
            headline_for_doctor=f"{brand}: Draft Closing Slide",
            visual_concept_description="Inspirational brand visual of an active patient with family, with the core 3 proof-point pillars highlighted in gold/blue.",
            clinical_data_chart_description="Placeholder for final approved claims summary.",
            key_bullet_points=[
                "Insert approved indication.",
                "Insert reviewed reasons to believe.",
                "Add next-step CTA only after promotional review."
            ],
            medical_representative_talk_track=f"Draft only: close with a compliant, approved action once claims are reviewed.",
            evidence_citation="SOURCE_NEEDED",
            safety_fair_balance_footer="Include full prescribing information reference."
        )
    ]
    
    lbl = LBLBrief(
        title=f"{brand} ({mol}) Clinical Leave-Behind Literature",
        target_audience=f"Target prescriber specialties for {indication} — confirm segments before production.",
        page_1_content_headline="Clinical Evidence Summary Pending Review",
        page_1_clinical_evidence_summary="Add only source-backed clinical evidence with claim-level citations and limitations.",
        page_2_dosing_and_safety_summary="Add approved dosing, warnings, contraindications, adverse reactions, and fair balance.",
        call_to_action="Internal draft only. Final call to action requires promotional review.",
        prescribing_info_footnote="Reference approved local prescribing information before external use."
    )
    
    # Objection frames are deliberately molecule-agnostic. Pre-filling concrete
    # clinical objections would put another molecule's safety and efficacy
    # profile into this brand's field material.
    objections = [
        MRObjectionHandling(
            doctor_objection=f"Why should I switch a stable patient to {brand}?",
            underlying_concern="Perceived lack of incremental benefit over the incumbent standard of care.",
            recommended_mr_response=f"Doctor, patient selection should follow the approved indication and local guideline context for {brand}. Insert the reviewed switch rationale once the claim, population, and safety balance are MLR-approved.",
            supporting_clinical_trial="SOURCE_NEEDED: comparative or switch-study evidence",
            recommended_visual_aid_page=1
        ),
        MRObjectionHandling(
            doctor_objection=f"What is the tolerability and monitoring burden with {brand}?",
            underlying_concern="Concern about adverse events, monitoring requirements, and discontinuation risk.",
            recommended_mr_response=f"Doctor, adverse event frequency, monitoring, and counselling language must be taken directly from the approved prescribing information for {mol}. Insert the label-verified safety summary here.",
            supporting_clinical_trial="SOURCE_NEEDED: approved prescribing information",
            recommended_visual_aid_page=5
        ),
        MRObjectionHandling(
            doctor_objection=f"How strong is the evidence base behind {brand}?",
            underlying_concern="Doubt about trial quality, endpoint relevance, or generalisability to their patients.",
            recommended_mr_response=f"Doctor, insert the reviewed pivotal trial design, population, comparator, and primary endpoint for {mol}. Do not quote effect sizes until each figure is traced to the publication and cleared by MLR.",
            supporting_clinical_trial="SOURCE_NEEDED: pivotal trial publication",
            recommended_visual_aid_page=3
        )
    ]
    
    patient_leaf = PatientEducationLeaflet(
        title=f"Understanding Your Treatment with {brand} ({mol})",
        plain_language_condition_summary="Patient education copy must be reviewed against the approved label and local patient information leaflet.",
        how_this_medicine_works=f"Explain how {brand} works only after the mechanism is verified from an approved source.",
        how_to_take_and_adherence="Insert approved dosing instructions from local prescribing information.",
        what_to_expect_and_side_effects="Insert approved adverse reactions and instructions on when to contact a healthcare professional.",
        lifestyle_and_diet_tips=[
            "Insert diet guidance reviewed against the approved patient information leaflet for this condition.",
            "Insert activity guidance appropriate to this patient population and cleared by medical review.",
            "Follow your doctor's instructions about fluid, diet, and activity — these vary by condition and by patient.",
            "Never stop or change your medication without consulting your doctor first."
        ]
    )
    
    return CreativeCommercialAssets(
        molecule_name=mol,
        brand_name=brand,
        campaign_theme="Evidence-Led Care: Draft Campaign Theme Pending Review",
        logo_direction="Clean modern typography with a brand mark that reflects the confirmed therapeutic benefit. Finalise symbolism once positioning is approved.",
        pack_mockup_brief="Premium primary pack concept with embossed brand lettering and braille safety markings. Confirm the approved dosage form, pack count, and regulatory pack artwork requirements before production.",
        visual_aid_slides=slides,
        lbl_brief=lbl,
        mr_objection_handling_guide=objections,
        patient_education_leaflet=patient_leaf,
        conference_booth_concept="Interactive booth concept with immersive touchscreens demonstrating the verified mechanism of action. Confirm the scientific narrative before build.",
        digital_email_copy=f"Subject: Draft {brand} Evidence Update for Internal Review\n\nDear Doctor,\n\nThis copy is a placeholder. Insert only approved, source-backed claims for {brand} ({mol}) after MLR review.\n\n[Reviewed Evidence Link]",
        banner_ad_copy=f"{brand} ({mol}) draft campaign copy. Not for external use until MLR approval."
    )
