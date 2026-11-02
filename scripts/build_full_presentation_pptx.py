"""
Build Full 18-Slide PowerPoint Presentation (.pptx)
AI-Powered College Complaint Intelligence System
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Color Palette Constants
COLOR_NAVY_DARK = RGBColor(15, 23, 42)       # #0F172A
COLOR_NAVY_PRIMARY = RGBColor(30, 58, 138)   # #1E3A8A
COLOR_BLUE_ACCENT = RGBColor(37, 99, 235)    # #2563EB
COLOR_CYAN_ACCENT = RGBColor(56, 189, 248)   # #38BDF8
COLOR_SLATE_BG = RGBColor(248, 250, 252)     # #F8FAFC
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_TEXT_DARK = RGBColor(15, 23, 42)       # #0F172A
COLOR_TEXT_MUTED = RGBColor(71, 85, 105)     # #475569
COLOR_TEXT_LIGHT = RGBColor(203, 213, 225)   # #CBD5E1
COLOR_BORDER_LIGHT = RGBColor(226, 232, 240) # #E2E8F0
COLOR_CARD_BG = RGBColor(255, 255, 255)
COLOR_EMERALD = RGBColor(16, 163, 74)        # #10B981
COLOR_AMBER = RGBColor(217, 119, 6)          # #D97706
COLOR_CRIMSON = RGBColor(220, 38, 38)        # #DC2626
COLOR_PURPLE = RGBColor(124, 58, 237)        # #7C3AED

TOTAL_SLIDES = 18

def set_slide_background(slide, prs, color):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    return bg

def add_header(slide, tag_text, title_text, subtitle_text, is_dark=False):
    # Tag / Pill
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.3))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = tag_text.upper()
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN_ACCENT if is_dark else COLOR_BLUE_ACCENT

    # Title
    p2 = tf.add_paragraph()
    p2.text = title_text
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_WHITE if is_dark else COLOR_TEXT_DARK

    # Subtitle
    p3 = tf.add_paragraph()
    p3.text = subtitle_text
    p3.font.size = Pt(11.5)
    p3.font.color.rgb = COLOR_TEXT_LIGHT if is_dark else COLOR_TEXT_MUTED

def add_footer(slide, current_idx, total_slides=TOTAL_SLIDES, is_dark=False):
    # Divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.015))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(51, 65, 85) if is_dark else COLOR_BORDER_LIGHT
    line.line.fill.background()

    # Footer Text Left
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(8.0), Inches(0.3))
    tf = tx_box.text_frame
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "AI-Powered College Complaint Intelligence System | B.Tech Capstone Defense"
    p.font.size = Pt(9)
    p.font.color.rgb = RGBColor(148, 163, 184) if is_dark else COLOR_TEXT_MUTED

    # Footer Text Right (Slide Number)
    tx_box2 = slide.shapes.add_textbox(Inches(9.5), Inches(7.05), Inches(3.0), Inches(0.3))
    tf2 = tx_box2.text_frame
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = f"Slide {current_idx} of {total_slides}"
    p2.alignment = PP_ALIGN.RIGHT
    p2.font.size = Pt(9)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_CYAN_ACCENT if is_dark else COLOR_BLUE_ACCENT

def add_card(slide, left, top, width, height, bg_rgb=COLOR_CARD_BG, border_rgb=COLOR_BORDER_LIGHT):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_rgb
    card.line.color.rgb = border_rgb
    card.line.width = Pt(1)
    return card

def add_bullet_point(tf, bold_prefix, text_content, font_size=11, space_after=8, text_color=COLOR_TEXT_DARK):
    p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
    p.space_after = Pt(space_after)
    
    r1 = p.add_run()
    r1.text = bold_prefix + " "
    r1.font.bold = True
    r1.font.size = Pt(font_size)
    r1.font.color.rgb = text_color

    r2 = p.add_run()
    r2.text = text_content
    r2.font.bold = False
    r2.font.size = Pt(font_size)
    r2.font.color.rgb = text_color

def set_speaker_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text.strip()

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide (Dark Theme)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, prs, COLOR_NAVY_DARK)

    # Accent decorative glow/bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.2), Inches(0.12), Inches(4.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_CYAN_ACCENT
    bar.line.fill.background()

    # Title & Metadata text box
    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(11.0), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p_badge = tf.paragraphs[0]
    p_badge.text = "FINAL YEAR B.TECH CAPSTONE PROJECT DEFENSE | COMPUTER SCIENCE & ENGINEERING"
    p_badge.font.size = Pt(11)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_CYAN_ACCENT
    p_badge.space_after = Pt(12)

    p_title = tf.add_paragraph()
    p_title.text = "AI-Powered College Complaint\nIntelligence System"
    p_title.font.size = Pt(36)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_WHITE
    p_title.space_after = Pt(14)

    p_sub = tf.add_paragraph()
    p_sub.text = "An End-to-End Enterprise Platform for Automated Triage, Duplicate Retrieval, Dynamic Prioritization, and Hotspot Discovery"
    p_sub.font.size = Pt(15)
    p_sub.font.color.rgb = COLOR_TEXT_LIGHT
    p_sub.space_after = Pt(28)

    p_meta = tf.add_paragraph()
    p_meta.text = "Candidate / Student Team: Lead CSE Engineers  |  Academic Year: 2026-2027\nDepartment of Computer Science & Engineering  |  Release Version: v1.0.0"
    p_meta.font.size = Pt(12)
    p_meta.font.color.rgb = RGBColor(148, 163, 184)

    add_footer(s1, 1, is_dark=True)
    set_speaker_notes(s1, 
        "Good morning, respected committee members and external examiners. Today, I am proud to present our final capstone project: "
        "the AI-Powered College Complaint Intelligence System. Higher education campuses function as bustling micro-cities where hundreds "
        "of infrastructure, academic, and safety issues occur daily. Our work bridges the gap between machine learning research and real-world "
        "administrative operations, delivering an end-to-end, sub-millisecond intelligence platform that intakes, analyzes, routes, prioritizes, "
        "and clusters student grievances with proven mathematical calibration and full-stack production stability."
    )

    # =========================================================================
    # SLIDE 2: Problem Introduction
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, prs, COLOR_SLATE_BG)
    add_header(s2, "Context & Challenges", "Campus Grievances & Administrative Bottlenecks", 
               "Higher education institutions struggle with high-volume, unstructured student complaints.")

    # 3 Column Cards
    col_w = 3.65
    top_pos = 1.6
    card_h = 5.0

    # Card 1: Scale & Manual Delay
    add_card(s2, 0.8, top_pos, col_w, card_h)
    tb1 = s2.shapes.add_textbox(Inches(0.95), Inches(top_pos + 0.2), Inches(col_w - 0.3), Inches(card_h - 0.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    add_bullet_point(tf1, "Campus Scale:", "Campuses host 5,000 to 30,000 students generating hundreds of weekly maintenance and service requests.", 11, 12, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf1, "Manual Dispatch:", "Helpdesks rely on manual triage by administrative staff, introducing 2 to 5 days of routing latency.", 10.5, 12)
    add_bullet_point(tf1, "Departmental Ping-Pong:", "Misrouted tickets bounce between departments (e.g., lab equipment misrouted to hostel staff), delaying real repairs.", 10.5, 12)

    # Card 2: Duplicate Ticket Floods
    add_card(s2, 4.8, top_pos, col_w, card_h)
    tb2 = s2.shapes.add_textbox(Inches(4.95), Inches(top_pos + 0.2), Inches(col_w - 0.3), Inches(card_h - 0.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    add_bullet_point(tf2, "Duplicate Flooding:", "Central failures (e.g., library Wi-Fi outage or hostel water tank disruption) trigger dozens of identical reports.", 11, 12, COLOR_AMBER)
    add_bullet_point(tf2, "Wasted Staff Capacity:", "Technicians spend significant hours reviewing duplicate tickets instead of executing repairs on the ground.", 10.5, 12)
    add_bullet_point(tf2, "Fragmented Context:", "Crucial updates from different students regarding the same root cause remain unlinked in separate tickets.", 10.5, 12)

    # Card 3: Priority & Emergency Blind Spots
    add_card(s2, 8.8, top_pos, col_w, card_h)
    tb3 = s2.shapes.add_textbox(Inches(8.95), Inches(top_pos + 0.2), Inches(col_w - 0.3), Inches(card_h - 0.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    add_bullet_point(tf3, "Subjective Inflation:", "Students mark routine issues as 'URGENT' to expedite personal service, skewing queue management.", 11, 12, COLOR_CRIMSON)
    add_bullet_point(tf3, "Hidden Life Safety:", "Acute hazards (exposed high-voltage wiring, gas leaks, structural cracks) get buried in general queues.", 10.5, 12)
    add_bullet_point(tf3, "No Systemic Trend View:", "Administrators treat chronic recurring issues as isolated events, missing opportunities for preventive overhaul.", 10.5, 12)

    add_footer(s2, 2)
    set_speaker_notes(s2,
        "Every student has experienced the frustration of submitting a maintenance complaint only for it to be routed to the wrong department "
        "or buried under hundreds of existing tickets. When an entire floor loses power or water, 50 students might file the exact same complaint. "
        "Manual triage teams spend hours reading duplicate tickets rather than dispatching technicians. More dangerously, genuine physical hazards "
        "can sit unaddressed if priority is self-reported or unsorted. We set out to replace this fragile manual triage with an intelligent cognitive pipeline."
    )

    # =========================================================================
    # SLIDE 3: Motivation and Problem Statement
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, prs, COLOR_SLATE_BG)
    add_header(s3, "Problem Statement & Motivation", "The Core Problem & Research Motivation",
               "Defining the technical requirements for an intelligent institutional grievance platform.")

    # Left: Formal Problem Statement
    add_card(s3, 0.8, 1.6, 5.6, 5.0)
    tb_ps = s3.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.5))
    tf_ps = tb_ps.text_frame
    tf_ps.word_wrap = True
    add_bullet_point(tf_ps, "Formal Problem Statement:", "", 13, 10, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_ps, "Core Research Question:", 
                     "How can an automated system accurately categorize unstructured student text, retrieve duplicate reports in real time, "
                     "compute objective multi-factor priority scores, and uncover systemic infrastructure trends without requiring expensive GPU infrastructure?", 10.5, 12)
    add_bullet_point(tf_ps, "Key Constraints:", 
                     "- Must run on commodity CPU hardware with sub-millisecond inference (<50 ms).\n"
                     "- Must provide calibrated probabilities with confidence gating for human oversight.\n"
                     "- Must guarantee 100% data leakage quarantine during scientific evaluation.\n"
                     "- Must never allow statistical models to override life-safety emergencies.", 10, 10)

    # Right: Institutional Motivation & Value
    add_card(s3, 6.8, 1.6, 5.7, 5.0)
    tb_m = s3.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.5))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    add_bullet_point(tf_m, "Institutional Motivation & Value:", "", 13, 10, COLOR_EMERALD)
    add_bullet_point(tf_m, "Student Experience:", "Instant real-time feedback and transparency. Students see predicted departments and duplicate alerts as they type.", 10.5, 12)
    add_bullet_point(tf_m, "Staff Operational Efficiency:", "Reduces manual sorting by over 95%. Automated selective routing allows staff to focus on verified repairs.", 10.5, 12)
    add_bullet_point(tf_m, "Life-Safety Compliance:", "Immediate 4-hour SLA escalation for electrical fires, chemical leaks, or physical harassment grievances.", 10.5, 12)
    add_bullet_point(tf_m, "Data-Driven Governance:", "Provides facilities managers with spatial hotspot maps and unsupervised recurring issue clusters for proactive planning.", 10.5, 10)

    add_footer(s3, 3)
    set_speaker_notes(s3,
        "Here we articulate our formal problem statement and institutional motivation. Our goal was not just to train another isolated NLP classifier, "
        "but to solve the complete end-to-end operational problem under realistic university constraints: standard CPU hardware, sub-millisecond speed, "
        "calibrated uncertainty, and strict life-safety overrides. A system that routes complaints in milliseconds while eliminating duplicate queue flooding "
        "directly improves campus safety, student satisfaction, and facility maintenance productivity."
    )

    # =========================================================================
    # SLIDE 4: Project Objectives
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, prs, COLOR_SLATE_BG)
    add_header(s4, "Project Scope", "Four Core Technical Objectives",
               "Measurable technical targets guiding the design, experimentation, and implementation.")

    # 4 Pillar Cards (2x2 Grid)
    pw = 5.6
    ph = 2.35
    
    # Pillar 1: Categorization
    add_card(s4, 0.8, 1.6, pw, ph)
    tb_p1 = s4.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(pw - 0.4), Inches(ph - 0.3))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    add_bullet_point(tf_p1, "Objective 1: Multiclass NLP Categorization", "", 12, 6, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_p1, "Target Accuracy:", "Achieve >= 90% accuracy and >= 0.85 Macro-F1 across 11 institutional categories with sub-millisecond CPU latency.", 10, 4)
    add_bullet_point(tf_p1, "Uncertainty Calibration:", "Ensure Expected Calibration Error (ECE) <= 0.15 via Platt scaling, enabling a confidence gate (theta = 0.60).", 10, 4)

    # Pillar 2: Duplicate Detection
    add_card(s4, 6.8, 1.6, pw, ph)
    tb_p2 = s4.shapes.add_textbox(Inches(7.0), Inches(1.75), Inches(pw - 0.4), Inches(ph - 0.3))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True
    add_bullet_point(tf_p2, "Objective 2: Top-k Duplicate Retrieval", "", 12, 6, COLOR_BLUE_ACCENT)
    add_bullet_point(tf_p2, "Retrieval Effectiveness:", "Achieve >= 90% Hit@3 on multi-report queries using sparse TF-IDF cosine similarity search.", 10, 4)
    add_bullet_point(tf_p2, "Advisory Interaction:", "Surface non-destructive advisory duplicate cards to avoid unverified automated ticket closures.", 10, 4)

    # Pillar 3: Priority & Safety
    add_card(s4, 0.8, 4.3, pw, ph)
    tb_p3 = s4.shapes.add_textbox(Inches(1.0), Inches(4.45), Inches(pw - 0.4), Inches(ph - 0.3))
    tf_p3 = tb_p3.text_frame
    tf_p3.word_wrap = True
    add_bullet_point(tf_p3, "Objective 3: Dynamic Prioritization & Safety", "", 12, 6, COLOR_CRIMSON)
    add_bullet_point(tf_p3, "Multi-Factor Formula:", "Combine category severity (35%), safety (25%), scope (20%), wait time (10%), and recurrence (10%).", 10, 4)
    add_bullet_point(tf_p3, "Deterministic Override:", "Enforce 55 regex safety rules triggering instant CRITICAL priority (4h SLA) with mandatory review.", 10, 4)

    # Pillar 4: Hotspot Discovery & Full Stack
    add_card(s4, 6.8, 4.3, pw, ph)
    tb_p4 = s4.shapes.add_textbox(Inches(7.0), Inches(4.45), Inches(pw - 0.4), Inches(ph - 0.3))
    tf_p4 = tb_p4.text_frame
    tf_p4.word_wrap = True
    add_bullet_point(tf_p4, "Objective 4: Hotspot Discovery & Full-Stack System", "", 12, 6, COLOR_EMERALD)
    add_bullet_point(tf_p4, "Unsupervised Clustering:", "Implement DBSCAN to identify recurring systemic breakdowns while isolating unique noise points.", 10, 4)
    add_bullet_point(tf_p4, "Enterprise Integration:", "Build an asynchronous FastAPI + React 18 SPA with PostgreSQL persistence, RBAC, and 155 automated tests.", 10, 4)

    add_footer(s4, 4)
    set_speaker_notes(s4,
        "To achieve our goal, we established four clear, measurable engineering objectives. "
        "First, multiclass classification with calibrated probabilities for selective routing. "
        "Second, top-k duplicate candidate retrieval achieving at least 90% Hit@3 without destructive data loss. "
        "Third, an objective 5-factor priority formula backed by a deterministic safety override for life-safety risks. "
        "And fourth, unsupervised clustering to discover recurring maintenance patterns, integrated into a complete React and FastAPI application."
    )

    # =========================================================================
    # SLIDE 5: Existing System and Proposed Solution
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, prs, COLOR_SLATE_BG)
    add_header(s5, "Comparative Analysis", "Existing Systems vs. Proposed Platform",
               "Contrasting conventional helpdesks against our intelligent, calibrated architecture.")

    # Comparison Table
    table_shape = s5.shapes.add_table(6, 4, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.0))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(3.1)
    table.columns[2].width = Inches(3.1)
    table.columns[3].width = Inches(3.333)

    headers = ["Feature Dimension", "Traditional Helpdesks (e.g. GLPI)", "Commercial ITSM (e.g. Jira)", "Our Intelligent System"]
    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_NAVY_DARK
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

    data_rows = [
        ("Ticket Intake", "Static dropdown forms;\nStudent must guess department", "Complex ticket fields;\nHeavy administrative overhead", "Real-time debounced NLP triage;\nInstant feedback as student types"),
        ("Routing Mechanism", "Manual staff dispatch;\n2-5 days administrative lag", "Rule-based static triggers;\nProne to misclassification", "Calibrated Linear SVM (98.9% acc);\nSub-millisecond latency (0.11 ms)"),
        ("Duplicate Handling", "None; Identical tickets\nclog staff queue", "Manual ticket linking;\nPost-submission manual merge", "Sparse TF-IDF Cosine Retrieval;\n100% Hit@3 advisory cards"),
        ("Priority Assessment", "Student-selected (URGENT);\nSubjective and unreliable", "Static impact/urgency matrix;\nNo temporal aging", "5-Factor Dynamic Formula (0-100);\nTemporal aging + 55 safety overrides"),
        ("Cluster / Trends", "Static spreadsheet exports;\nNo semantic pattern discovery", "Basic BI dashboards;\nNo automated issue clustering", "Unsupervised DBSCAN clustering;\nDiscovers chronic spatial hotspots")
    ]

    for r_idx, row in enumerate(data_rows):
        bg_col = RGBColor(255, 255, 255) if r_idx % 2 == 0 else RGBColor(241, 245, 249)
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_col
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_TEXT_DARK
            if c_idx == 0:
                p.font.bold = True
            elif c_idx == 3:
                p.font.color.rgb = COLOR_NAVY_PRIMARY
                p.font.bold = True

    add_footer(s5, 5)
    set_speaker_notes(s5,
        "This slide presents a direct comparison between conventional helpdesks like GLPI or Jira Service Desk and our proposed platform. "
        "Traditional systems place the entire cognitive burden on the student—forcing them to guess the department and choose a subjective priority. "
        "Our system flips this paradigm: machine learning analyzes the unstructured text in real time, computes calibrated probabilities, "
        "checks for duplicates, and assigns dynamic priority based on institutional SLAs, all in less than a millisecond."
    )

    # =========================================================================
    # SLIDE 6: Overall System Architecture
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, prs, COLOR_SLATE_BG)
    add_header(s6, "System Design", "Overall System Architecture & Tier Decoupling",
               "High-concurrency, asynchronous three-tier platform with thread-safe singleton AI services.")

    # Image: Architecture Diagram
    img_arch = 'reports/figures/system_architecture_diagram.png'
    if os.path.exists(img_arch):
        s6.shapes.add_picture(img_arch, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))

    add_footer(s6, 6)
    set_speaker_notes(s6,
        "Here is the high-level system architecture. The platform operates across three decoupled tiers. "
        "The client tier is built on React 18 and Vite, delivering real-time keystroke triage as students type. "
        "The application tier uses FastAPI, taking advantage of Python's asynchronous event loop. "
        "In the domain tier, our AI models are loaded once during server startup as thread-safe singleton objects, "
        "completely eliminating disk I/O latency during request handling. The persistence tier utilizes PostgreSQL with complete transactional audit logging."
    )

    # =========================================================================
    # SLIDE 7: Technology Stack
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, prs, COLOR_SLATE_BG)
    add_header(s7, "Engineering Foundation", "Technology Stack & Architectural Justifications",
               "Carefully selected production-grade tools optimized for speed, reliability, and maintainability.")

    # 4 Stack Cards
    cw = 2.75
    gap = 0.24
    
    # Python & Scikit-Learn
    add_card(s7, 0.8, 1.6, cw, 5.0)
    tb_s1 = s7.shapes.add_textbox(Inches(0.95), Inches(1.8), Inches(cw - 0.3), Inches(4.5))
    tf_s1 = tb_s1.text_frame
    tf_s1.word_wrap = True
    add_bullet_point(tf_s1, "Machine Learning", "", 12, 8, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_s1, "Python 3.11+:", "Standard scientific computing runtime with native NumPy and Scikit-learn.", 10, 8)
    add_bullet_point(tf_s1, "Scikit-Learn 1.4+:", "Sparse Linear SVM, Platt Sigmoid calibration, and TF-IDF vectorization.", 10, 8)
    add_bullet_point(tf_s1, "Why Not PyTorch/BERT?:", "Linear models run in 0.11 ms on CPU with <100 MB RAM, avoiding expensive GPU cloud instances.", 9.5, 8)

    # FastAPI Backend
    add_card(s7, 0.8 + (cw + gap), 1.6, cw, 5.0)
    tb_s2 = s7.shapes.add_textbox(Inches(0.95 + (cw + gap)), Inches(1.8), Inches(cw - 0.3), Inches(4.5))
    tf_s2 = tb_s2.text_frame
    tf_s2.word_wrap = True
    add_bullet_point(tf_s2, "Backend API Tier", "", 12, 8, COLOR_BLUE_ACCENT)
    add_bullet_point(tf_s2, "FastAPI & Uvicorn:", "High-performance async ASGI framework handling concurrent HTTP requests.", 10, 8)
    add_bullet_point(tf_s2, "Pydantic v2:", "Rigorous request/response schema validation and automatic OpenAPI Swagger docs.", 10, 8)
    add_bullet_point(tf_s2, "Lifespan Singleton:", "Models loaded into memory once at startup, guaranteeing sub-millisecond API response.", 9.5, 8)

    # React + Vite Frontend
    add_card(s7, 0.8 + 2*(cw + gap), 1.6, cw, 5.0)
    tb_s3 = s7.shapes.add_textbox(Inches(0.95 + 2*(cw + gap)), Inches(1.8), Inches(cw - 0.3), Inches(4.5))
    tf_s3 = tb_s3.text_frame
    tf_s3.word_wrap = True
    add_bullet_point(tf_s3, "Frontend Client Tier", "", 12, 8, COLOR_PURPLE)
    add_bullet_point(tf_s3, "React 18.3:", "Component-driven SPA with defensive state rendering and custom hooks.", 10, 8)
    add_bullet_point(tf_s3, "Vite 5.4:", "Next-gen lightning bundler with instant HMR and optimized tree-shaken builds.", 10, 8)
    add_bullet_point(tf_s3, "AbortController:", "Cancels stale in-flight typing requests cleanly to prevent race conditions.", 9.5, 8)

    # Database & Security
    add_card(s7, 0.8 + 3*(cw + gap), 1.6, cw, 5.0)
    tb_s4 = s7.shapes.add_textbox(Inches(0.95 + 3*(cw + gap)), Inches(1.8), Inches(cw - 0.3), Inches(4.5))
    tf_s4 = tb_s4.text_frame
    tf_s4.word_wrap = True
    add_bullet_point(tf_s4, "Persistence & Auth", "", 12, 8, COLOR_EMERALD)
    add_bullet_point(tf_s4, "PostgreSQL 15+:", "Production relational persistence with strict ACID constraints and connection pooling.", 10, 8)
    add_bullet_point(tf_s4, "Alembic Migrations:", "Version-controlled, automated schema evolution and transactional upgrades.", 10, 8)
    add_bullet_point(tf_s4, "PyJWT Security:", "Cryptographic HMAC-SHA256 bearer tokens enforcing strict Student/Staff/Admin RBAC.", 9.5, 8)

    add_footer(s7, 7)
    set_speaker_notes(s7,
        "Our technology stack was chosen based on clear engineering trade-offs rather than chasing trends. "
        "We selected Scikit-learn because sparse Linear SVMs evaluate in 0.11 milliseconds on CPU with minimal memory overhead, "
        "making GPUs unnecessary. FastAPI provides high-concurrency asynchronous execution, while React 18 with Vite provides a responsive, "
        "defensive user interface. For storage, we use PostgreSQL in production for transactional reliability, and SQLite for isolated automated test execution."
    )

    # =========================================================================
    # SLIDE 8: Dataset Collection, Generation and Preprocessing
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, prs, COLOR_SLATE_BG)
    add_header(s8, "Data Engineering", "Dataset Construction, Schema & Quarantine Protocol",
               "1,273 balanced records partitioned with zero data leakage via StratifiedGroupKFold.")

    # Left: Details & Partitioning Table
    add_card(s8, 0.8, 1.6, 5.8, 5.0)
    tb_d = s8.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_d = tb_d.text_frame
    tf_d.word_wrap = True
    add_bullet_point(tf_d, "Synthetic Campus Corpus:", "1,273 complaint records evenly balanced across 11 institutional categories (~115 samples/class).", 10.5, 8, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_d, "10 Schema Fields:", "complaint_id, complaint_text, category, category_name, location, created_at, status, priority_label, incident_group_id, data_source.", 10, 8)
    add_bullet_point(tf_d, "Incident-Aware Splitting:", "StratifiedGroupKFold on incident_group_id ensured that all multi-report complaints for an incident stayed in the same split.", 10, 8)
    add_bullet_point(tf_d, "Split Breakdown:", "- Train: 908 records (71.3%) | 35 incident groups\n- Validation: 183 records (14.4%) | 8 incident groups\n- Held-Out Test: 182 records (14.3%) | 7 incident groups (QUARANTINED)", 9.5, 8)
    add_bullet_point(tf_d, "Auxiliary External Dataset:", "Audited sanchit-19/university-students-complaints (N=332, CC-BY-4.0). Quarantined as an out-of-domain benchmark under D-014.", 9.5, 6)

    # Right: Class Distribution Chart
    add_card(s8, 6.8, 1.6, 5.7, 5.0)
    img_dist = 'reports/figures/class_distribution.png'
    if os.path.exists(img_dist):
        s8.shapes.add_picture(img_dist, Inches(6.9), Inches(1.8), Inches(5.5), Inches(4.5))

    add_footer(s8, 8)
    set_speaker_notes(s8,
        "A machine learning model is only as credible as its evaluation protocol. Our primary dataset contains 1,273 complaints across 11 institutional categories. "
        "To ensure complete scientific validity, we instituted a strict leakage-prevention protocol. When multiple students report the same incident, "
        "those complaints share an incident_group_id. We used StratifiedGroupKFold so that entire incident groups were quarantined into a single split. "
        "Our held-out test set of 182 complaints remained completely untouched until the final validation phase, with zero text or ID leakage."
    )

    # =========================================================================
    # SLIDE 9: NLP Complaint Classification
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, prs, COLOR_SLATE_BG)
    add_header(s9, "Module A: Categorization", "NLP Pipeline, Linear SVM & Platt Sigmoid Calibration",
               "Sub-millisecond inference with well-calibrated posterior probabilities and selective confidence gating.")

    # Image: AI Pipeline Diagram
    img_pipe = 'reports/figures/ai_pipeline_flow.png'
    if os.path.exists(img_pipe):
        s9.shapes.add_picture(img_pipe, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))

    add_footer(s9, 9)
    set_speaker_notes(s9,
        "For Module A, our complaint classifier, we engineered a sparse linear pipeline. We transform lemmatized unigrams and bigrams into sublinear TF-IDF vectors. "
        "For classification, we chose a Linear Support Vector Machine. Linear SVMs find the maximum-margin hyperplane separating classes, but raw SVM outputs "
        "are uncalibrated geometric distances. To convert these into true probabilities, we apply Platt scaling—fitting a sigmoid function over cross-validated "
        "decision margins. This enables selective classification: if the highest probability is 60% or higher, the ticket is auto-routed; otherwise, "
        "it is safely diverted to human review."
    )

    # =========================================================================
    # SLIDE 10: Duplicate and Related Complaint Detection
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, prs, COLOR_SLATE_BG)
    add_header(s10, "Module B: Duplicate Detection", "Top-k Candidate Retrieval & The Imbalance Paradox",
               "100% Hit@3 on multi-report queries, solving helpdesk duplicate flooding without data loss.")

    # Left: Explanation of Imbalance Paradox
    add_card(s10, 0.8, 1.6, 5.8, 5.0)
    tb_dup = s10.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_dup = tb_dup.text_frame
    tf_dup.word_wrap = True
    add_bullet_point(tf_dup, "The Operational Problem:", "When an infrastructure failure occurs, dozens of students file identical tickets, overwhelming support staff.", 10.5, 8, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_dup, "Top-k Retrieval Performance (N=18 Queries):", 
                     "- Hit@1: 77.78% (14 / 18 queries returned duplicate at rank 1)\n"
                     "- Hit@3: 100.00% (18 / 18 queries had duplicate in top-3)\n"
                     "- Mean Reciprocal Rank (MRR): 0.8889\n"
                     "- Average Retrieval Latency: 2.15 ms", 10, 8, COLOR_BLUE_ACCENT)
    add_bullet_point(tf_dup, "The Pairwise Imbalance Paradox:", 
                     "In 182 test tickets, there are 16,471 pairs but only 15 true duplicates (0.091% prevalence). "
                     "While ROC-AUC is 0.9978, pairwise F1 is 0.3182 at validation-fixed tau=0.60 (Precision 19.18%, Recall 93.33%). "
                     "A tiny 0.36% false positive rate over 16,456 negatives produces 59 false pairs.", 9.5, 8)
    add_bullet_point(tf_dup, "Why Retrieval Solves It:", "Staff don't review 16,000 arbitrary pairs; they receive top-3 candidate cards, where Hit@3 is 100%.", 10, 6, COLOR_EMERALD)

    # Right: Retrieval Comparison Chart
    add_card(s10, 6.8, 1.6, 5.7, 5.0)
    img_dup = 'reports/figures/duplicate_retrieval_comparison.png'
    if os.path.exists(img_dup):
        s10.shapes.add_picture(img_dup, Inches(6.9), Inches(1.8), Inches(5.5), Inches(4.5))

    add_footer(s10, 10)
    set_speaker_notes(s10,
        "In Module B, we address duplicate complaint detection. In an active helpdesk, when a central pipe bursts, dozens of students lodge complaints. "
        "If you compare all tickets pairwise, you face an extreme class imbalance: out of 16,471 pairs, only 15 are true duplicates. "
        "A standard binary classifier will suffer from false positives across the massive negative pool. Therefore, we formulated duplicate detection "
        "as an Information Retrieval task—querying the indexed database for top-k semantically similar complaints using sparse cosine similarity. "
        "The system achieved 100% Hit@3 and 0.8889 MRR, proving that non-destructive advisory cards in the UI solve the problem cleanly."
    )

    # =========================================================================
    # SLIDE 11: Rule-Based Priority Assessment
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, prs, COLOR_SLATE_BG)
    add_header(s11, "Module C: Priority Engine", "Multi-Factor Scoring & Deterministic Safety Overrides",
               "Dynamic mathematical prioritization coupled with a fail-safe 55-pattern regex hazard detector.")

    # Left: Formula Breakdown
    add_card(s11, 0.8, 1.6, 5.8, 5.0)
    tb_pri = s11.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_pri = tb_pri.text_frame
    tf_pri.word_wrap = True
    add_bullet_point(tf_pri, "Multi-Factor Mathematical Formula:", "", 11.5, 6, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_pri, "P_base = 0.35(Sev) + 0.25(Saf) + 0.20(Aff) + 0.10(Wait) + 0.10(Rec)", 
                     "\n- Severity (0.35): Inherent category risk (Lab/Power = 80, General = 30)\n"
                     "- Safety (0.25): Physical hazard potential\n"
                     "- Scope (0.20): Spatial range (Room=20, Floor=60, Hall=100)\n"
                     "- Wait Time (0.10): Escalates linearly up to 72 hours\n"
                     "- Recurrence (0.10): Escalates with linked duplicate volume", 9.5, 8)
    add_bullet_point(tf_pri, "SLA Bands:", "CRITICAL (>=80, <4h) | HIGH (>=60, <24h) | MEDIUM (>=35, <48h) | LOW (<35, <72h)", 9.5, 8, COLOR_EMERALD)
    add_bullet_point(tf_pri, "Deterministic Safety Override:", 
                     "55 regex patterns scan for acute emergencies (sparking, gas leak, ceiling collapse, ragging). "
                     "Triggers instant escalation to CRITICAL (100.0) with mandatory human review.", 9.5, 6, COLOR_CRIMSON)
    add_bullet_point(tf_pri, "Formal Boundary Statement:", 
                     "All test-suite safety scenarios triggered expected overrides; keyword matching is bounded and does not guarantee universal emergency detection.", 8.5, 4, COLOR_TEXT_MUTED)

    # Right: Priority Distribution Chart
    add_card(s11, 6.8, 1.6, 5.7, 5.0)
    img_pri = 'reports/figures/priority_distribution.png'
    if os.path.exists(img_pri):
        s11.shapes.add_picture(img_pri, Inches(6.9), Inches(1.8), Inches(5.5), Inches(4.5))

    add_footer(s11, 11)
    set_speaker_notes(s11,
        "Module C replaces subjective student priority inflation with an objective mathematical priority formula. "
        "We combine five normalized dimensions: category severity, safety vulnerability, affected scope, elapsed wait time, and recurrence frequency. "
        "If an issue is left unresolved, the waiting time factor dynamically escalates the priority score over 72 hours to prevent aging tickets from being forgotten. "
        "More importantly, we implemented a deterministic 55-pattern safety override. Acute hazards like sparking wires or ragging immediately bypass mathematical "
        "averaging, force the priority to CRITICAL with a 4-hour SLA, and require mandatory staff review."
    )

    # =========================================================================
    # SLIDE 12: Recurring-Issue Discovery and Clustering
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, prs, COLOR_SLATE_BG)
    add_header(s12, "Module D: Hotspot Discovery", "Unsupervised DBSCAN Recurring-Issue Clustering",
               "Discovering systemic infrastructure decay without manual annotation or supervision.")

    # Left: Methodology & Findings
    add_card(s12, 0.8, 1.6, 5.8, 5.0)
    tb_cl = s12.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_cl = tb_cl.text_frame
    tf_cl.word_wrap = True
    add_bullet_point(tf_cl, "Why DBSCAN over K-Means?:", 
                     "K-Means forces every isolated complaint into an artificial cluster. DBSCAN identifies arbitrary density shapes and separates unique complaints as noise.", 10.5, 8, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_cl, "Hyperparameter Tuning (Validation N=183):", 
                     "- Cosine distance metric: eps = 0.58\n"
                     "- Density threshold: min_samples = 3\n"
                     "- Non-noise Silhouette Score: 0.4274", 10, 8, COLOR_BLUE_ACCENT)
    add_bullet_point(tf_cl, "Discovered Cluster Themes:", 
                     "- Cluster 3: Water purifier contamination in Hostel Block C\n"
                     "- Cluster 7: Wi-Fi DHCP timeouts in Central Library 2nd Floor\n"
                     "- Cluster 12: Faulty AC compressor in Mechanical Lab 102", 9.5, 8)
    add_bullet_point(tf_cl, "Evaluation Integrity Status:", 
                     "Test split clustering is labeled N/A to prevent exploratory data snooping on quarantined data. Validated on external dataset sanchit-19 as well.", 9.5, 6, COLOR_TEXT_MUTED)

    # Right: K-Means vs DBSCAN Tuning Chart
    add_card(s12, 6.8, 1.6, 5.7, 5.0)
    img_cl = 'reports/figures/clustering_kmeans_tuning.png'
    if os.path.exists(img_cl):
        s12.shapes.add_picture(img_cl, Inches(6.9), Inches(1.8), Inches(5.5), Inches(4.5))

    add_footer(s12, 12)
    set_speaker_notes(s12,
        "Beyond individual ticket processing, university leadership needs strategic insights into recurring infrastructure problems. "
        "In Module D, we applied unsupervised DBSCAN clustering. We chose DBSCAN over K-Means because it does not force unrelated tickets into artificial clusters; "
        "instead, it cleanly isolates unique complaints as noise points. On our validation corpus, it identified 21 dense recurring problem clusters "
        "with a non-noise silhouette score of 0.4274—pinpointing issues like chronic water contamination in Hostel Block C and Wi-Fi outages in the library. "
        "In compliance with academic integrity standards, clustering metrics are marked N/A on the held-out test set to avoid exploratory snooping."
    )

    # =========================================================================
    # SLIDE 13: Student Portal Demonstration
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, prs, COLOR_SLATE_BG)
    add_header(s13, "System Demonstration", "Student Experience: Live Keystroke Triage & Duplicate Alerts",
               "Real-time feedback as students type, featuring debounced inference and duplicate warnings.")

    # Image: Student Portal UI Flow
    img_stu = 'reports/figures/student_portal_ui_flow.png'
    if os.path.exists(img_stu):
        s13.shapes.add_picture(img_stu, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))

    add_footer(s13, 13)
    set_speaker_notes(s13,
        "Here is the Student Portal interface. As the student types their grievance, our debounced keystroke handler queries our singleton NLP service. "
        "In less than two milliseconds, the model identifies the category with high confidence and displays an advisory duplicate alert if a matching ticket exists. "
        "Notice the 300 millisecond debouncing: requests fire smoothly without freezing the UI, and stale in-flight requests are cancelled via AbortController."
    )

    # =========================================================================
    # SLIDE 14: Staff Review and Admin Analytics
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, prs, COLOR_SLATE_BG)
    add_header(s14, "System Demonstration", "Staff Queue, Deep Explainability & Admin Analytics",
               "Total transparency with Platt probability breakdowns, factor factorizations, and immutable audit logs.")

    # Image: Staff Admin UI Flow
    img_staff = 'reports/figures/staff_admin_ui_flow.png'
    if os.path.exists(img_staff):
        s14.shapes.add_picture(img_staff, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))

    add_footer(s14, 14)
    set_speaker_notes(s14,
        "Here is the Staff Portal and Explainability Modal. In the departmental queue, tickets are sorted by priority with critical emergencies highlighted at the top. "
        "When staff open a ticket, the Explainability Modal reveals the exact posterior probabilities from Platt scaling and the exact mathematical breakdown "
        "of the priority formula. If authorized staff execute a priority override, the system records an immutable audit record containing the user ID, timestamp, and textual justification."
    )

    # =========================================================================
    # SLIDE 15: Experimental Results and Model Comparison
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15, prs, COLOR_SLATE_BG)
    add_header(s15, "Empirical Validation", "Experimental Results & Held-Out Test Confusion Matrix",
               "Verified results on quarantined held-out synthetic test data (N=182) with zero data leakage.")

    # Left: Model Comparison Table
    add_card(s15, 0.8, 1.6, 6.0, 5.0)
    tb_exp = s15.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.6), Inches(4.6))
    tf_exp = tb_exp.text_frame
    tf_exp.word_wrap = True
    add_bullet_point(tf_exp, "Model Benchmarking (Validation N=183):", "", 11.5, 6, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_exp, "- E0 Majority Baseline:", "Accuracy: 9.84% | Macro-F1: 0.0179", 9.5, 4)
    add_bullet_point(tf_exp, "- E1 Logistic Regression:", "Accuracy: 98.91% | Macro-F1: 0.9890 | 0.073 ms", 9.5, 4)
    add_bullet_point(tf_exp, "- E2 Calibrated Linear SVM:", "Accuracy: 99.45% | Macro-F1: 0.9952 | 0.110 ms (CHAMPION)", 9.5, 4, COLOR_BLUE_ACCENT)
    add_bullet_point(tf_exp, "- E3 Naive Bayes:", "Accuracy: 97.81% | Macro-F1: 0.9774 | 0.081 ms", 9.5, 4)
    add_bullet_point(tf_exp, "- E4 Char n-grams Linear SVM:", "Accuracy: 99.45% | Macro-F1: 0.9948 | 0.415 ms", 9.5, 6)
    
    add_bullet_point(tf_exp, "Held-Out Test Results (E2 Champion, N=182):", "", 11.5, 6, COLOR_EMERALD)
    add_bullet_point(tf_exp, "Test Accuracy: 98.90% (180/182)", "Macro-F1: 0.9882 | Weighted-F1: 0.9889", 9.5, 4)
    add_bullet_point(tf_exp, "Calibration Quality:", "ECE: 0.0825 | Brier Score: 0.0195 | Log Loss: 0.1093", 9.5, 4)
    add_bullet_point(tf_exp, "Generalization Gap:", "Delta Macro-F1 = -0.0070 (<1% drop; zero overfitting)", 9.5, 4)

    # Right: Held-Out Confusion Matrix
    add_card(s15, 7.0, 1.6, 5.5, 5.0)
    img_cm = 'reports/figures/final_test_confusion_matrix.png'
    if os.path.exists(img_cm):
        s15.shapes.add_picture(img_cm, Inches(7.1), Inches(1.8), Inches(5.3), Inches(4.5))

    add_footer(s15, 15)
    set_speaker_notes(s15,
        "Here are our empirical experimental results. On the validation set, the Calibrated Linear SVM achieved 99.45% accuracy and 0.9952 Macro-F1, "
        "outperforming Logistic Regression and Naive Bayes. On the quarantined held-out test set of 182 complaints, the champion model achieved 98.90% accuracy "
        "and 0.9882 Macro-F1. The generalization gap is less than 1%, proving that the model did not overfit. On the right, the confusion matrix shows "
        "clean diagonal performance across all 11 categories, with exactly two errors between lab and sanitation equipment."
    )

    # =========================================================================
    # SLIDE 16: Limitations, Responsible AI and Human Oversight
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16, prs, COLOR_SLATE_BG)
    add_header(s16, "Responsible AI", "Selective Classification, Error Analysis & Governance Boundaries",
               "Human-in-the-loop oversight catches 100% of test errors at confidence threshold theta = 0.60.")

    # Left: Error Analysis & Confidence Gate
    add_card(s16, 0.8, 1.6, 5.8, 5.0)
    tb_lim = s16.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_lim = tb_lim.text_frame
    tf_lim.word_wrap = True
    add_bullet_point(tf_lim, "Deep Error Analysis (The 2 Test Errors):", "", 11.5, 6, COLOR_CRIMSON)
    add_bullet_point(tf_lim, "SYN-00196 (True: C06 Lab, Pred: C07 Sanit):", 
                     "Lab oscilloscope reported in Sports Complex badminton court. Conf: 40.52%.", 9.5, 4)
    add_bullet_point(tf_lim, "SYN-00326 (True: C06 Lab, Pred: C07 Sanit):", 
                     "Lab oscilloscope reported in Hostel Block A during exams. Conf: 20.75%.", 9.5, 6)
    add_bullet_point(tf_lim, "Confidence Gate Efficacy (theta = 0.60):", 
                     "- Auto-routed: 98.9% of tickets with 100.00% accuracy\n"
                     "- Human Review Queue: 1.1% of tickets\n"
                     "- Error Recall: 100.0% (Both errors caught safely!)\n"
                     "- False Review Rate: 0.0%", 9.5, 8, COLOR_EMERALD)
    add_bullet_point(tf_lim, "Ethical & Technical Boundaries:", 
                     "- Synthetic data may not fully capture local campus slang or misspellings.\n"
                     "- 55 regex safety rules cannot detect unlisted novel metaphors.\n"
                     "- Student privacy requires client-side PII scrubbing in cloud environments.", 9.0, 4)

    # Right: Threshold Tradeoff Chart
    add_card(s16, 6.8, 1.6, 5.7, 5.0)
    img_to = 'reports/figures/final_test_threshold_tradeoff.png'
    if os.path.exists(img_to):
        s16.shapes.add_picture(img_to, Inches(6.9), Inches(1.8), Inches(5.5), Inches(4.5))

    add_footer(s16, 16)
    set_speaker_notes(s16,
        "In the spirit of scientific integrity, this slide examines our model's errors and ethical safeguards. "
        "Out of 182 test complaints, exactly two were misclassified—both involving synthetic prompt anomalies where lab oscilloscopes "
        "were placed in sports complexes or hostel rooms. Because the vocabulary conflicted, the model was uncertain, assigning confidence scores of 40% and 20%. "
        "Because our confidence gate is set at 60%, both errors were safely intercepted into the human review queue, giving our live system "
        "an effective 100.00% auto-routing accuracy. We also explicitly acknowledge that keyword overrides cannot catch unlisted metaphors, "
        "which is why human oversight remains an architectural invariant."
    )

    # =========================================================================
    # SLIDE 17: Future Scope and Conclusion
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17, prs, COLOR_SLATE_BG)
    add_header(s17, "Looking Forward", "Future Roadmap & Summary of Contributions",
               "A validated, deployable platform establishing a new standard for campus grievance intelligence.")

    # Left: Future Scope (3 Horizons)
    add_card(s17, 0.8, 1.6, 5.8, 5.0)
    tb_fut = s17.shapes.add_textbox(Inches(1.0), Inches(1.75), Inches(5.4), Inches(4.6))
    tf_fut = tb_fut.text_frame
    tf_fut.word_wrap = True
    add_bullet_point(tf_fut, "Future Research & Roadmap:", "", 12, 8, COLOR_NAVY_PRIMARY)
    add_bullet_point(tf_fut, "Horizon 1: Dense Semantic Embeddings", 
                     "Transition Module B to hybrid BM25 + dense sentence embeddings (e.g. all-MiniLM-L6-v2) via pgvector to capture semantic synonymy without lexical overlap.", 10, 8)
    add_bullet_point(tf_fut, "Horizon 2: Multilingual & Code-Mixed NLP", 
                     "Support regional languages and Hinglish expressions commonly used by students across Indian university campuses.", 10, 8)
    add_bullet_point(tf_fut, "Horizon 3: Multimodal Vision Triage", 
                     "Accept photographic evidence (cracked walls, water leakage) and fuse visual damage probabilities with textual priority factors.", 10, 8)

    # Right: Summary of Contributions
    add_card(s17, 6.8, 1.6, 5.7, 5.0)
    tb_con = s17.shapes.add_textbox(Inches(7.0), Inches(1.75), Inches(5.3), Inches(4.6))
    tf_con = tb_con.text_frame
    tf_con.word_wrap = True
    add_bullet_point(tf_con, "Summary of Key Contributions:", "", 12, 8, COLOR_EMERALD)
    add_bullet_point(tf_con, "Scientific Rigor:", "98.90% test accuracy, 0.9882 Macro-F1, 0.0825 ECE, sub-millisecond (0.11 ms) CPU inference with zero data leakage.", 10, 8)
    add_bullet_point(tf_con, "Operational Safety:", "Selective confidence gate (theta=0.60) catches 100% of errors; 55-pattern regex guarantees instant escalation for physical hazards.", 10, 8)
    add_bullet_point(tf_con, "Effective Retrieval:", "100% Hit@3 on duplicate queries; surfaces advisory cards to avoid queue flooding without destructive auto-merges.", 10, 8)
    add_bullet_point(tf_con, "Enterprise Implementation:", "Full-stack React 18 + FastAPI application backed by PostgreSQL, RBAC, and 155 passing automated tests.", 10, 8)

    add_footer(s17, 17)
    set_speaker_notes(s17,
        "In conclusion, this project demonstrates that modern machine learning, when properly calibrated and coupled with deterministic safeguards, "
        "can transform campus administration. We have delivered a system that routes complaints in less than a millisecond with 98.9% accuracy, "
        "eliminates duplicate queue congestion with 100% top-3 retrieval, and prioritizes life safety above all else. "
        "Our future roadmap includes dense vector search via pgvector, multilingual language support, and multimodal computer vision triage. "
        "Thank you, respected committee members. I am now eager to take your questions."
    )

    # =========================================================================
    # SLIDE 18: Q&A Slide (Dark Theme)
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18, prs, COLOR_NAVY_DARK)

    # Accent decorative glow/bar
    bar18 = s18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.12), Inches(4.5))
    bar18.fill.solid()
    bar18.fill.fore_color.rgb = COLOR_CYAN_ACCENT
    bar18.line.fill.background()

    tb_qa = s18.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(11.0), Inches(4.5))
    tf_qa = tb_qa.text_frame
    tf_qa.word_wrap = True

    p_q1 = tf_qa.paragraphs[0]
    p_q1.text = "CAPSTONE DEFENSE & VIVA VOCE"
    p_q1.font.size = Pt(12)
    p_q1.font.bold = True
    p_q1.font.color.rgb = COLOR_CYAN_ACCENT
    p_q1.space_after = Pt(14)

    p_q2 = tf_qa.add_paragraph()
    p_q2.text = "Questions & Technical Defense"
    p_q2.font.size = Pt(36)
    p_q2.font.bold = True
    p_q2.font.color.rgb = COLOR_WHITE
    p_q2.space_after = Pt(20)

    p_q3 = tf_qa.add_paragraph()
    p_q3.text = "Thank you for your time, guidance, and evaluation."
    p_q3.font.size = Pt(16)
    p_q3.font.color.rgb = COLOR_TEXT_LIGHT
    p_q3.space_after = Pt(24)

    p_q4 = tf_qa.add_paragraph()
    p_q4.text = (
        "Key Deliverables & Verification Recap:\n"
        "- 128 / 128 Python Backend Tests Passing  |  27 / 27 React Frontend Tests Passing\n"
        "- Test Accuracy: 98.90%  |  Macro-F1: 0.9882  |  ECE: 0.0825  |  Latency: 0.11 ms\n"
        "- Duplicate Retrieval Hit@3: 100.00%  |  MRR: 0.8889  |  Pairwise ROC-AUC: 0.9978\n"
        "- Production PostgreSQL & SQLite CI Harness  |  JWT Bearer RBAC  |  155 Passing Tests"
    )
    p_q4.font.size = Pt(12)
    p_q4.font.color.rgb = RGBColor(148, 163, 184)

    add_footer(s18, 18, is_dark=True)
    set_speaker_notes(s18,
        "Thank you, respected committee members and external evaluators. All deliverables, test suites, and documentation are verified "
        "and ready for inspection. I welcome your questions and look forward to the viva voce examination."
    )

    # Save presentation
    output_path = 'reports/AI_Powered_College_Complaint_Intelligence_System.pptx'
    prs.save(output_path)
    print(f"Successfully generated presentation at: {output_path}")

if __name__ == '__main__':
    build_presentation()

