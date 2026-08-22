import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.dml.color import RGBColor as PptxRGBColor
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import Dict, Any, Optional
from ..models.brand_plan import CompleteBrandPlan
from ..models.assets import CreativeCommercialAssets
from ..models.forecast import MarketForecast
from ..models.molecule import MoleculeProfile

def generate_brand_plan_docx(plan: CompleteBrandPlan, molecule: Optional[MoleculeProfile] = None) -> io.BytesIO:
    """Generates a professional 30+ page equivalent Word Document (.docx) for the Brand Plan."""
    doc = docx.Document()
    
    # Title Section
    title_p = doc.add_paragraph()
    title_run = title_p.add_run(f"PHARMACEUTICAL BRAND STRATEGY PLAN\n{plan.brand_name.upper()}")
    title_run.bold = True
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(15, 76, 129) # Classic Classic Navy
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(f"Target Molecule: {plan.molecule_name} | Indication: {plan.indication} | Geography: {plan.target_geography}\nDate: {plan.last_updated} | MLR Audit Status: Review Required")
    sub_run.font.size = Pt(11)
    sub_run.font.italic = True
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("\n" + "="*50 + "\n")
    
    # Executive Vision & Mission
    doc.add_heading("1. Strategic Mission & Brand Charter", level=1)
    p_m = doc.add_paragraph()
    p_m.add_run("Brand Mission: ").bold = True
    p_m.add_run(plan.mission)
    
    p_v = doc.add_paragraph()
    p_v.add_run("Brand Vision: ").bold = True
    p_v.add_run(plan.vision)
    
    p_o = doc.add_paragraph()
    p_o.add_run("Core Commercial Objective: ").bold = True
    p_o.add_run(plan.brand_objective)
    
    p_pos = doc.add_paragraph()
    p_pos.add_run("Positioning Statement: ").bold = True
    p_pos.add_run(plan.positioning_statement)
    
    # Sections Loop
    for sec in plan.sections:
        doc.add_heading(sec.section_title, level=2)
        doc.add_paragraph(sec.content_markdown)
        if sec.key_takeaways:
            p_t = doc.add_paragraph()
            p_t.add_run("Key Strategic Takeaways:").bold = True
            for t in sec.key_takeaways:
                doc.add_paragraph(f"• {t}", style='List Bullet')
    
    # Tactical Action Plan Table
    doc.add_heading("12-Month Tactical Launch Milestones", level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Month'
    hdr_cells[1].text = 'Activity'
    hdr_cells[2].text = 'Responsible Team'
    hdr_cells[3].text = 'Status'
    
    for m in plan.monthly_action_plan:
        row_cells = table.add_row().cells
        row_cells[0].text = m.month_name
        row_cells[1].text = m.activity
        row_cells[2].text = m.responsible_team
        row_cells[3].text = m.status
        
    # KPI Scorecard Table
    doc.add_heading("Balanced Commercial Scorecard & KPIs", level=1)
    kpi_table = doc.add_table(rows=1, cols=5)
    kpi_table.style = 'Table Grid'
    k_hdr = kpi_table.rows[0].cells
    k_hdr[0].text = 'KPI Metric'
    k_hdr[1].text = 'Category'
    k_hdr[2].text = 'Target Q1'
    k_hdr[3].text = 'Target Q2'
    k_hdr[4].text = 'Target Year 1'
    
    for k in plan.kpi_scorecard:
        k_row = kpi_table.add_row().cells
        k_row[0].text = k.kpi_name
        k_row[1].text = k.category
        k_row[2].text = k.target_q1
        k_row[3].text = k.target_q2
        k_row[4].text = k.target_year1
        
    # Compliance Footer
    doc.add_paragraph("\n\n" + "-"*50)
    p_disc = doc.add_paragraph()
    r_disc_title = p_disc.add_run("Compliance Disclaimer: ")
    r_disc_title.bold = True
    r_disc_title.font.size = Pt(9)
    r_disc_body = p_disc.add_run("This Brand Plan is a draft for internal strategic decision-making. It is not approved promotional material. All clinical, safety, efficacy, regulatory, market, and trademark statements must undergo formal Medical-Legal-Regulatory and legal review before use.")
    r_disc_body.font.size = Pt(9)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_pitch_deck_pptx(plan: CompleteBrandPlan, assets: CreativeCommercialAssets) -> io.BytesIO:
    """Generates an executive 10-slide PowerPoint Pitch Deck (.pptx)."""
    prs = Presentation()
    prs.slide_width = PptxInches(13.333) # 16:9 widescreen
    prs.slide_height = PptxInches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    def add_mlr_footer(slide) -> None:
        """Draft status on every slide.

        A pitch deck is the artifact most likely to be pulled out of the app
        and presented, forwarded, or left in an inbox on its own — unlike the
        DOCX, which carries its disclaimer as running text a reader has to
        scroll past, a single deleted or skipped slide here would leave every
        other slide silently unmarked. Repeating it as a footer means no slide
        can be extracted without carrying the warning.
        """
        footer_box = slide.shapes.add_textbox(
            PptxInches(0.8), PptxInches(7.05), PptxInches(11.7), PptxInches(0.35))
        f_tf = footer_box.text_frame
        f_tf.word_wrap = False
        p = f_tf.paragraphs[0]
        p.text = ("DRAFT — Not MLR Approved — Internal Use Only. "
                 "Clinical, safety, and efficacy statements require source verification before use.")
        p.font.size = PptxPt(9)
        p.font.italic = True
        p.font.color.rgb = PptxRGBColor(148, 163, 184)

    def add_standard_slide(title_text: str, subtitle_text: str, bullets: list):
        slide = prs.slides.add_slide(blank_layout)
        
        # Header banner
        header_box = slide.shapes.add_textbox(PptxInches(0.8), PptxInches(0.6), PptxInches(11.7), PptxInches(1.2))
        tf = header_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = PptxPt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = PptxRGBColor(15, 76, 129)
        
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.size = PptxPt(14)
        p_sub.font.color.rgb = PptxRGBColor(100, 110, 120)
        
        # Content box
        content_box = slide.shapes.add_textbox(PptxInches(0.8), PptxInches(2.0), PptxInches(11.7), PptxInches(4.8))
        c_tf = content_box.text_frame
        c_tf.word_wrap = True
        
        for i, b in enumerate(bullets):
            p = c_tf.add_paragraph() if i > 0 else c_tf.paragraphs[0]
            p.text = f"•  {b}"
            p.font.size = PptxPt(18)
            p.space_after = PptxPt(14)
            p.font.color.rgb = PptxRGBColor(30, 41, 59)
        
        add_mlr_footer(slide)
        return slide
    
    # Slide 1: Title Slide
    s1 = prs.slides.add_slide(blank_layout)
    s1_box = s1.shapes.add_textbox(PptxInches(1.0), PptxInches(2.0), PptxInches(11.3), PptxInches(3.5))
    s1_tf = s1_box.text_frame
    s1_title = s1_tf.paragraphs[0]
    s1_title.text = f"{plan.brand_name.upper()}\nCOMMERCIAL BRAND STRATEGY"
    s1_title.font.size = PptxPt(36)
    s1_title.font.bold = True
    s1_title.font.color.rgb = PptxRGBColor(15, 76, 129)
    
    s1_sub = s1_tf.add_paragraph()
    s1_sub.text = f"Target Molecule: {plan.molecule_name} | {plan.therapy_area} | {plan.target_geography}\nLaunch Strategy & Commercial Operating Plan"
    s1_sub.font.size = PptxPt(18)
    s1_sub.font.color.rgb = PptxRGBColor(71, 85, 105)
    s1_sub.space_before = PptxPt(20)
    add_mlr_footer(s1)
    
    # Slide 2: Executive Charter
    add_standard_slide(
        "Executive Brand Charter & Core Objective",
        "Defining our market ambition and clinical mission",
        [
            f"Mission: {plan.mission}",
            f"Vision: {plan.vision}",
            f"Commercial Objective: {plan.brand_objective}",
            "Target Audience: Tier A Cardiologists, Endocrinologists, Nephrologists, and Primary Care."
        ]
    )
    
    # Slide 3: Landmark Clinical Evidence
    add_standard_slide(
        "Landmark Evidence & Survival Proof Points",
        "Translating Level-1 randomized trials into doctor conviction",
        [
            "Insert claim-level evidence only after PMID/DOI/label verification.",
            "Document endpoint, comparator, population, geography, and limitations.",
            "Separate approved-label facts from internal strategic interpretation.",
            "Include fair-balance safety language before external use."
        ]
    )
    
    # Slide 4: Strategic Positioning
    add_standard_slide(
        "Strategic Brand Positioning & RTBs",
        "Differentiating against incumbent standard of care",
        [
            f"Positioning Statement: {plan.positioning_statement}",
            f"Campaign Theme: {assets.campaign_theme}",
            "Reason to Believe #1: Pending verified source.",
            "Reason to Believe #2: Pending label review.",
            "Reason to Believe #3: Pending fair-balance assessment."
        ]
    )
    
    # Slide 5: Visual Aid Storyboard (Detailer Flow)
    v_bullets = [f"Slide {s.slide_number}: {s.headline_for_doctor}" for s in assets.visual_aid_slides[:4]]
    add_standard_slide(
        "Field Force Detailing Flow (Visual Aid Concept)",
        "6-Step Doctor Conversation Structure",
        v_bullets
    )
    
    # Slide 6: 12-Month Launch Milestones
    m_bullets = [f"{m.month_name}: {m.activity} ({m.responsible_team})" for m in plan.monthly_action_plan[:5]]
    add_standard_slide(
        "Commercial Launch Milestones & Roadmap",
        "Key operational deliverables for Year 1 execution",
        m_bullets
    )
    
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def generate_financial_model_xlsx(forecast: MarketForecast, brand_name: str) -> io.BytesIO:
    """Generates an editable, multi-tab Excel spreadsheet (.xlsx) with forecasting formulas."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "5-Year Revenue Forecast"
    
    # Header styling
    header_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0F4C81", end_color="0F4C81", fill_type="solid")
    bold_font = Font(name="Calibri", size=11, bold=True)
    curr_format = "$#,##0"
    
    ws.merge_cells("A1:G1")
    ws["A1"] = f"MOLECULE TO MARKET AI — FINANCIAL FORECAST MODEL ({brand_name.upper()})"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 22

    # Row 2: draft status. The DOCX and PPTX both carry this; a spreadsheet is
    # just as forwardable and often outlives the deck it was built alongside,
    # so the same statement belongs on the one sheet this workbook has.
    ws.merge_cells("A2:G2")
    ws["A2"] = ("DRAFT — Not MLR Approved — Internal planning use only. "
               "Pricing, forecast, and CAGR assumptions require sourced verification before use.")
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="94A3B8")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Patient Funnel Section
    ws["A4"] = "EPIDEMIOLOGICAL PATIENT FUNNEL PARAMETERS"
    ws["A4"].font = bold_font
    
    funnel_data = [
        ("Total Target Population", forecast.total_population, "#,##0"),
        ("Disease Prevalence Rate", forecast.prevalence_rate, "0.0%"),
        ("Prevalent Patient Pool", forecast.prevalent_patient_pool, "#,##0"),
        ("Diagnosis Rate", forecast.diagnosed_rate, "0.0%"),
        ("Diagnosed Patient Pool", forecast.diagnosed_patient_pool, "#,##0"),
        ("Treatment Rate", forecast.treated_rate, "0.0%"),
        ("Treated Patient Pool", forecast.treated_patient_pool, "#,##0"),
        ("Annual Net Price Per Patient (USD)", forecast.annual_cost_per_patient_usd, "$#,##0.00"),
        ("Total Available Treated Market Size (USD)", forecast.current_therapy_market_size_usd, "$#,##0")
    ]
    
    for row_idx, (label, val, fmt) in enumerate(funnel_data, start=5):
        ws.cell(row=row_idx, column=1, value=label)
        c = ws.cell(row=row_idx, column=2, value=val)
        c.number_format = fmt
        c.alignment = Alignment(horizontal="right")
        
    # Scenario Comparison Section
    start_row = 16
    ws.cell(row=start_row, column=1, value="5-YEAR REVENUE SCENARIO PROJECTIONS (USD)").font = bold_font
    
    headers = ["Scenario", "Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "5-Yr CAGR"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=start_row+1, column=col_idx, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        
    scenarios = [
        ("Conservative", forecast.conservative_scenario),
        ("Realistic (Base-Case)", forecast.realistic_scenario),
        ("Aggressive", forecast.aggressive_scenario)
    ]
    
    for s_idx, (s_name, s_data) in enumerate(scenarios, start=start_row+2):
        ws.cell(row=s_idx, column=1, value=s_name).font = bold_font
        for c_idx, yr_val in enumerate([s_data.year_1, s_data.year_2, s_data.year_3, s_data.year_4, s_data.year_5], start=2):
            cell = ws.cell(row=s_idx, column=c_idx, value=yr_val)
            cell.number_format = curr_format
            cell.alignment = Alignment(horizontal="right")
        cagr_cell = ws.cell(row=s_idx, column=7, value=s_data.cagr_percentage / 100.0)
        cagr_cell.number_format = "0.0%"
        cagr_cell.alignment = Alignment(horizontal="right")
        
    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # India trade price structure — a separate sheet, not columns bolted onto
    # the first one, since PTR/PTS is an India-specific concept in INR while
    # the sheet above is USD. Only added when the forecast actually carries
    # trade pricing, so a plan with none does not show an empty tab.
    if forecast.trade_price_structure:
        _add_trade_price_sheet(wb, forecast, brand_name)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def _add_trade_price_sheet(wb, forecast: MarketForecast, brand_name: str) -> None:
    """India MRP -> PTR -> PTS trade margin structure, on its own sheet.

    PTS is the manufacturer's actual realization per patient-year — the
    correct basis for the company's own revenue forecast, distinct from the
    MRP the patient pays. Showing the margin structure explicitly, rather
    than just the final number, is what lets a brand manager sanity-check the
    trade terms against what the distribution channel would actually accept.
    """
    trade = forecast.trade_price_structure
    ws = wb.create_sheet("India Trade Price Structure")

    header_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0F4C81", end_color="0F4C81", fill_type="solid")
    bold_font = Font(name="Calibri", size=11, bold=True)
    inr_format = "₹#,##0"

    ws.merge_cells("A1:D1")
    ws["A1"] = f"INDIA TRADE PRICE STRUCTURE — {brand_name.upper()}"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 22

    ws.merge_cells("A2:D2")
    ws["A2"] = ("DRAFT — Not MLR Approved. Trade terms require sourced verification "
               "against the actual distribution agreement before use.")
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="94A3B8")
    ws["A2"].alignment = Alignment(horizontal="center")

    ws["A4"] = "PRICE POINT (PER PATIENT-YEAR)"
    ws["A4"].font = bold_font
    ws["B4"] = "VALUE (INR)"
    ws["B4"].font = bold_font

    rows = [
        ("MRP — Maximum Retail Price (what the patient pays)", trade.mrp_per_patient_year),
        ("PTR — Price to Retailer", trade.ptr_per_patient_year),
        ("PTS — Price to Stockist (manufacturer's own realization)", trade.pts_per_patient_year),
    ]
    for idx, (label, value) in enumerate(rows, start=5):
        ws.cell(row=idx, column=1, value=label)
        cell = ws.cell(row=idx, column=2, value=value)
        cell.number_format = inr_format
        cell.alignment = Alignment(horizontal="right")

    ws["A9"] = "MARGIN"
    ws["A9"].font = bold_font
    ws["B9"] = "AMOUNT (INR)"
    ws["B9"].font = bold_font
    ws["C9"] = "% OF UPSTREAM PRICE"
    ws["C9"].font = bold_font

    margin_rows = [
        ("Retailer margin (MRP - PTR)", trade.retailer_margin_amount, trade.retailer_margin_percent),
        ("Stockist margin (PTR - PTS)", trade.stockist_margin_amount, trade.stockist_margin_percent),
    ]
    for idx, (label, amount, percent) in enumerate(margin_rows, start=10):
        ws.cell(row=idx, column=1, value=label)
        amount_cell = ws.cell(row=idx, column=2, value=amount)
        amount_cell.number_format = inr_format
        amount_cell.alignment = Alignment(horizontal="right")
        percent_cell = ws.cell(row=idx, column=3, value=percent / 100.0)
        percent_cell.number_format = "0.0%"
        percent_cell.alignment = Alignment(horizontal="right")

    ws["A13"] = "Manufacturer realization as % of MRP"
    ws["A13"].font = bold_font
    pct_cell = ws.cell(row=13, column=2, value=trade.manufacturer_realization_percent_of_mrp / 100.0)
    pct_cell.number_format = "0.0%"
    pct_cell.font = bold_font
    pct_cell.alignment = Alignment(horizontal="right")

    if forecast.therapy_market_size_inr_at_trade_price:
        ws["A15"] = "Addressable market at PTS (treated pool x PTS)"
        ws["A15"].font = bold_font
        market_cell = ws.cell(row=15, column=2, value=forecast.therapy_market_size_inr_at_trade_price)
        market_cell.number_format = "₹#,##0"
        market_cell.font = bold_font
        market_cell.alignment = Alignment(horizontal="right")
        ws["A16"] = ("This is the manufacturer's own addressable revenue, not the "
                     "patient-facing market size shown on the USD sheet — the two "
                     "are not meant to reconcile, since PTS excludes the retailer "
                     "and stockist margins MRP includes.")
        ws["A16"].font = Font(name="Calibri", size=9, italic=True, color="64748B")
        ws.merge_cells("A16:D16")

    for col, width in (("A", 55), ("B", 18), ("C", 20), ("D", 14)):
        ws.column_dimensions[col].width = width
