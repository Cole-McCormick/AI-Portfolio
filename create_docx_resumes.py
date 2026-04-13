"""
Generate 5 sample resumes in .docx format, each with a distinct layout.

Layouts used:
  1. frank_nguyen.docx   — sidebar table (two-column contact/skills sidebar)
  2. grace_kim.docx      — classic single-column with thick ruled headers
  3. henry_patel.docx    — skills grid table + experience bullets
  4. isabella_ross.docx  — compact two-column experience table
  5. james_okafor.docx   — modern shaded header block + clean sections

Run:  python create_docx_resumes.py
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_DIR = Path("sample_resumes")
OUT_DIR.mkdir(exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str) -> None:
    """Set a table cell's background shading."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_borders(cell, **kwargs) -> None:
    """Set borders on a table cell. kwargs: top, bottom, left, right → hex color."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side, color in kwargs.items():
        border = OxmlElement(f"w:{side}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "12")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)


def add_horizontal_rule(doc: Document, color: str = "2563EB") -> None:
    """Add a coloured horizontal rule paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def bold_run(para, text: str, size: int = 11, color: str = None) -> None:
    run = para.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def normal_run(para, text: str, size: int = 10) -> None:
    run = para.add_run(text)
    run.font.size = Pt(size)


def section_heading(doc: Document, title: str, color: str = "1E3A5F") -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    bold_run(p, title.upper(), size=11, color=color)
    add_horizontal_rule(doc, color=color)


def bullet(doc: Document, text: str, size: int = 10) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(text)
    run.font.size = Pt(size)


# ── Resume 1 — Frank Nguyen ───────────────────────────────────────────────────
# Layout: two-column sidebar table (left = contact+skills, right = experience)

def make_frank_nguyen() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)

    # Name banner
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_p.add_run("FRANK NGUYEN")
    name_run.bold = True
    name_run.font.size = Pt(20)
    name_run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)

    tagline_p = doc.add_paragraph()
    tagline_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tagline_p.add_run("Senior Python Engineer  •  Payments & Infrastructure").font.size = Pt(10)

    doc.add_paragraph()

    # Two-column table
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.columns[0].width = Inches(2.2)
    tbl.columns[1].width = Inches(4.5)

    left = tbl.cell(0, 0)
    right = tbl.cell(0, 1)
    set_cell_bg(left, "EFF6FF")

    # LEFT SIDEBAR
    lp = left.paragraphs[0]
    bold_run(lp, "CONTACT", size=9, color="1E3A5F")

    def lline(text):
        p = left.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        p.add_run(text).font.size = Pt(9)

    lline("frank.nguyen@email.com")
    lline("github.com/fnguyen")
    lline("Austin, TX")

    lp2 = left.add_paragraph()
    lp2.paragraph_format.space_before = Pt(8)
    bold_run(lp2, "SKILLS", size=9, color="1E3A5F")

    for skill in [
        "Python (expert)", "asyncio / FastAPI", "PostgreSQL", "Redis",
        "Kafka", "Docker / Kubernetes", "AWS (ECS, RDS, SQS)", "gRPC",
        "GitHub Actions", "PCI-DSS", "Stripe / Plaid",
    ]:
        lline(f"• {skill}")

    lp3 = left.add_paragraph()
    lp3.paragraph_format.space_before = Pt(8)
    bold_run(lp3, "EDUCATION", size=9, color="1E3A5F")
    lline("B.S. Computer Science")
    lline("UT Austin, 2015")

    # RIGHT MAIN CONTENT
    rp = right.paragraphs[0]
    rp.paragraph_format.left_indent = Inches(0.15)
    bold_run(rp, "PROFESSIONAL EXPERIENCE", size=10, color="1E3A5F")

    def rblock(title, period, bullets):
        tp = right.add_paragraph()
        tp.paragraph_format.left_indent = Inches(0.15)
        tp.paragraph_format.space_before = Pt(8)
        tp.paragraph_format.space_after = Pt(1)
        bold_run(tp, title, size=10)
        tp.add_run(f"   {period}").font.size = Pt(9)
        for b in bullets:
            bp = right.add_paragraph()
            bp.paragraph_format.left_indent = Inches(0.3)
            bp.paragraph_format.space_after = Pt(1)
            bp.add_run(f"• {b}").font.size = Pt(9)

    rblock("Staff Engineer – PayStream Inc.", "2020 – Present", [
        "Designed event-driven payment orchestration layer handling 6M transactions/day using FastAPI + Kafka",
        "Owned Stripe and Plaid integrations; reduced failed payment rate by 28%",
        "Led PostgreSQL sharding project, cutting P99 query latency from 410 ms to 55 ms",
        "Drove PCI-DSS SAQ-D recertification; authored remediation runbooks",
        "Mentored 5 engineers; established async Python standards across 3 squads",
    ])
    rblock("Senior Python Developer – ClearPay", "2018 – 2020", [
        "Built gRPC microservices for ACH clearing; processed $300 M/month",
        "Migrated monolith to Kubernetes on EKS; reduced deployment time by 65%",
        "Introduced pytest + factory_boy; raised coverage from 40% to 92%",
    ])
    rblock("Python Developer – DataBridge Co.", "2015 – 2018", [
        "Developed REST APIs consumed by 30+ internal analytics dashboards",
        "Maintained Celery + RabbitMQ job queues for async reporting pipelines",
    ])

    doc.save(OUT_DIR / "frank_nguyen.docx")
    print("  [ok] frank_nguyen.docx")


# ── Resume 2 — Grace Kim ──────────────────────────────────────────────────────
# Layout: classic single-column, thick blue ruled section headers

def make_grace_kim() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # Header
    name_p = doc.add_paragraph()
    name_run = name_p.add_run("Grace Kim")
    name_run.bold = True
    name_run.font.size = Pt(22)
    name_run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    contact_p = doc.add_paragraph()
    contact_p.add_run("grace.kim@email.com  |  linkedin.com/in/gracekim  |  Seattle, WA").font.size = Pt(10)

    add_horizontal_rule(doc, color="0F172A")

    summary_p = doc.add_paragraph()
    summary_p.add_run(
        "Senior Python engineer with 7 years of experience in fintech and payments. "
        "Expert in building high-availability microservices, payment API integrations, "
        "and distributed systems. Track record of reducing latency, improving reliability, "
        "and mentoring growing engineering teams."
    ).font.size = Pt(10)

    section_heading(doc, "Experience", color="0F172A")

    def job(title, company, period, bullets):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        bold_run(p, f"{title}", size=11)
        p.add_run(f"  —  {company}  |  {period}").font.size = Pt(10)
        for b in bullets:
            bullet(doc, b)
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    job("Lead Python Engineer", "NovaPay Technologies", "2021 – Present", [
        "Architected real-time payment routing engine in FastAPI handling 8M events/day across 12 microservices",
        "Integrated Stripe, Plaid, and ACH networks; led technical design for same-day settlement feature",
        "Optimised PostgreSQL query plans; reduced P99 latency from 380 ms to 42 ms",
        "Owned PCI-DSS Level 1 compliance programme; coordinated QSA audit across 4 teams",
        "Grew and mentored team from 3 to 9 engineers; conducted 200+ code reviews per quarter",
        "Maintained 96% test coverage; introduced property-based testing with Hypothesis",
    ])
    job("Senior Software Engineer", "QuickFunds Ltd.", "2018 – 2021", [
        "Built gRPC-based loan origination service processing $200 M/month in disbursements",
        "Migrated legacy Flask app to FastAPI on Kubernetes (GKE); improved deploy frequency 4×",
        "Implemented Kafka-based fraud detection pipeline reducing chargebacks by 22%",
        "Led on-call rotation; reduced MTTR from 60 min to 12 min via runbook automation",
    ])
    job("Python Developer", "InnoSoft Agency", "2017 – 2018", [
        "Delivered REST APIs and Django back-ends for 8 client projects",
        "Introduced Docker-based dev environments; cut onboarding time from 2 days to 2 hours",
    ])

    section_heading(doc, "Skills", color="0F172A")
    skills = [
        ("Languages", "Python (expert), Go (proficient), SQL, TypeScript (basic)"),
        ("Frameworks", "FastAPI, asyncio, SQLAlchemy, Pydantic, pytest, Hypothesis"),
        ("Infrastructure", "AWS (ECS, RDS, SQS, Lambda), GCP (GKE), Docker, Kubernetes, Terraform"),
        ("Databases", "PostgreSQL, Redis, DynamoDB, BigQuery"),
        ("Other", "Kafka, gRPC, GitHub Actions, PCI-DSS, Stripe, Plaid, Datadog"),
    ]
    for label, value in skills:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        bold_run(p, f"{label}: ", size=10)
        normal_run(p, value)

    section_heading(doc, "Education", color="0F172A")
    p = doc.add_paragraph()
    bold_run(p, "B.S. Computer Science", size=10)
    normal_run(p, "  —  University of Washington, 2017")

    doc.save(OUT_DIR / "grace_kim.docx")
    print("  [ok] grace_kim.docx")


# ── Resume 3 — Henry Patel ────────────────────────────────────────────────────
# Layout: skills grid table at top, then experience bullets

def make_henry_patel() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    # Name + contact row table
    hdr = doc.add_table(rows=1, cols=2)
    hdr.columns[0].width = Inches(3.5)
    hdr.columns[1].width = Inches(3.2)
    set_cell_bg(hdr.cell(0, 0), "1E3A8A")
    set_cell_bg(hdr.cell(0, 1), "1E3A8A")

    lp = hdr.cell(0, 0).paragraphs[0]
    lp.paragraph_format.left_indent = Inches(0.1)
    nr = lp.add_run("Henry Patel")
    nr.bold = True
    nr.font.size = Pt(18)
    nr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    rp = hdr.cell(0, 1).paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    contact_run = rp.add_run("henry.patel@email.com\ngithub.com/hpatel  |  Chicago, IL")
    contact_run.font.size = Pt(9)
    contact_run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    doc.add_paragraph()

    # Summary
    sp = doc.add_paragraph()
    sp.add_run(
        "Payments-focused Python engineer with 6 years of experience. "
        "Specialises in high-throughput microservices, async Python, and cloud-native infrastructure. "
        "Strong collaborator and technical mentor comfortable owning systems end-to-end."
    ).font.size = Pt(10)

    # Skills grid
    section_heading(doc, "Core Skills", color="1E3A8A")
    skills_data = [
        ["Python / asyncio", "FastAPI / Pydantic", "PostgreSQL"],
        ["Docker / Kubernetes", "AWS (ECS, RDS, SQS)", "Kafka / RabbitMQ"],
        ["gRPC / REST APIs", "GitHub Actions CI/CD", "PCI-DSS Compliance"],
        ["Stripe / Plaid APIs", "Redis / DynamoDB", "pytest / coverage"],
    ]
    grid = doc.add_table(rows=len(skills_data), cols=3)
    grid.style = "Table Grid"
    for r, row in enumerate(skills_data):
        for c, cell_text in enumerate(row):
            cell = grid.cell(r, c)
            cell.text = cell_text
            cell.paragraphs[0].runs[0].font.size = Pt(9)
            if r % 2 == 0:
                set_cell_bg(cell, "EFF6FF")

    # Experience
    section_heading(doc, "Experience", color="1E3A8A")

    def job(title, company, period, bullets):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        bold_run(p, title, size=11)
        normal_run(p, f"  ·  {company}  ·  {period}")
        for b in bullets:
            bullet(doc, b)

    job("Senior Python Engineer", "FinEdge Payments", "2021 – Present", [
        "Built FastAPI microservices for payment orchestration; serves 5M transactions/day",
        "Integrated Stripe and Plaid; automated reconciliation saving 20 engineering hours/week",
        "Designed PostgreSQL schema with table partitioning for 3-year transaction history",
        "Implemented Kafka consumers for real-time fraud alerting; cut false-positive rate by 35%",
        "Mentored 3 junior engineers; introduced ADR (Architecture Decision Record) practice",
        "Maintained 93% test coverage; led shift-left security review process",
    ])
    job("Python Developer", "LogiPay Inc.", "2019 – 2021", [
        "Developed async REST APIs for ACH payment initiation and status tracking",
        "Containerised services with Docker; deployed to AWS ECS via GitHub Actions pipelines",
        "Participated in PCI-DSS gap assessment and remediation for SAQ-A certification",
    ])
    job("Junior Python Developer", "Bright Systems", "2018 – 2019", [
        "Maintained Django REST Framework APIs for e-commerce clients",
        "Wrote unit and integration tests; improved coverage from 35% to 78%",
    ])

    section_heading(doc, "Education", color="1E3A8A")
    p = doc.add_paragraph()
    bold_run(p, "B.S. Computer Engineering", size=10)
    normal_run(p, "  ·  University of Illinois Urbana-Champaign  ·  2018")

    doc.save(OUT_DIR / "henry_patel.docx")
    print("  [ok] henry_patel.docx")


# ── Resume 4 — Isabella Ross ─────────────────────────────────────────────────
# Layout: compact two-column experience table (company/period left, details right)

def make_isabella_ross() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    # Header
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Isabella Ross")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run("isabella.ross@email.com  ·  github.com/iross  ·  Boston, MA").font.size = Pt(10)

    add_horizontal_rule(doc, color="7C3AED")

    # Summary
    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp.add_run(
        "Mid-level Python developer with 4 years of experience in backend APIs, "
        "async services, and cloud deployments. Growing toward a senior role in fintech."
    ).font.size = Pt(10)

    # Skills bar
    section_heading(doc, "Technical Skills", color="7C3AED")
    skills_p = doc.add_paragraph()
    skills_p.add_run(
        "Python  ·  FastAPI  ·  Django  ·  asyncio  ·  PostgreSQL  ·  Redis  ·  "
        "Docker  ·  AWS (ECS, SQS, RDS)  ·  GitHub Actions  ·  pytest  ·  Stripe  ·  SQLAlchemy"
    ).font.size = Pt(10)

    # Experience as table
    section_heading(doc, "Experience", color="7C3AED")

    exp_data = [
        (
            "Python Backend Developer\nTechPulse Corp\n2022 – Present",
            [
                "Built FastAPI microservices for internal analytics platform serving 15k DAU",
                "Wrote async SQS consumers for event ingestion pipelines",
                "Improved PostgreSQL query performance; reduced report generation time by 55%",
                "Integrated Stripe billing for SaaS subscription management",
                "Established GitHub Actions CI/CD; raised test coverage from 50% to 88%",
            ],
        ),
        (
            "Software Developer\nRetailEdge Solutions\n2021 – 2022",
            [
                "Developed Django REST Framework APIs for inventory and order management",
                "Containerised services with Docker; managed staging and prod on AWS ECS",
                "Participated in sprint planning and code reviews as tech lead delegate",
            ],
        ),
        (
            "Junior Developer\nWebSpark Studio\n2020 – 2021",
            [
                "Built Flask back-ends and Python automation scripts for agency clients",
                "Introduced pytest to two legacy projects; onboarded two junior developers",
            ],
        ),
    ]

    tbl = doc.add_table(rows=len(exp_data), cols=2)
    tbl.style = "Table Grid"
    tbl.columns[0].width = Inches(1.8)
    tbl.columns[1].width = Inches(4.7)

    for i, (meta, bullets) in enumerate(exp_data):
        left_cell = tbl.cell(i, 0)
        right_cell = tbl.cell(i, 1)
        set_cell_bg(left_cell, "F5F3FF")
        left_cell.text = meta
        left_cell.paragraphs[0].runs[0].font.size = Pt(9)
        left_cell.paragraphs[0].runs[0].bold = True

        right_cell.paragraphs[0].clear()
        for b in bullets:
            bp = right_cell.add_paragraph(f"• {b}")
            bp.paragraph_format.space_after = Pt(2)
            bp.runs[0].font.size = Pt(9)

    section_heading(doc, "Education", color="7C3AED")
    ep = doc.add_paragraph()
    bold_run(ep, "B.S. Information Systems", size=10)
    normal_run(ep, "  ·  Northeastern University  ·  2020")

    doc.save(OUT_DIR / "isabella_ross.docx")
    print("  [ok] isabella_ross.docx")


# ── Resume 5 — James Okafor ──────────────────────────────────────────────────
# Layout: shaded full-width header block, clean sections, no tables

def make_james_okafor() -> None:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(0)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

    # Full-width shaded header via table
    hdr_tbl = doc.add_table(rows=2, cols=1)
    hdr_tbl.columns[0].width = Inches(6.7)
    set_cell_bg(hdr_tbl.cell(0, 0), "0F172A")
    set_cell_bg(hdr_tbl.cell(1, 0), "1E3A5F")

    name_cell = hdr_tbl.cell(0, 0)
    name_p = name_cell.paragraphs[0]
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_p.paragraph_format.space_before = Pt(12)
    name_p.paragraph_format.space_after = Pt(4)
    nr = name_p.add_run("JAMES OKAFOR")
    nr.bold = True
    nr.font.size = Pt(22)
    nr.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    sub_cell = hdr_tbl.cell(1, 0)
    sub_p = sub_cell.paragraphs[0]
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_before = Pt(4)
    sub_p.paragraph_format.space_after = Pt(10)
    sr = sub_p.add_run(
        "james.okafor@email.com  ·  github.com/jokafor  ·  Denver, CO  ·  linkedin.com/in/jokafor"
    )
    sr.font.size = Pt(10)
    sr.font.color.rgb = RGBColor(0xBF, 0xDB, 0xFF)

    doc.add_paragraph()

    # Summary
    sp = doc.add_paragraph()
    sp.add_run(
        "Junior Python developer with 2 years of experience building REST APIs and data pipelines. "
        "Background in data engineering and analytics with growing backend development skills. "
        "Eager to deepen expertise in microservices architecture and cloud-native Python."
    ).font.size = Pt(10)

    section_heading(doc, "Experience", color="0F172A")

    def job(title, company, period, bullets):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        bold_run(p, title, size=11)
        normal_run(p, f"  |  {company}  |  {period}")
        for b in bullets:
            bullet(doc, b)

    job("Junior Data Engineer", "InsightCo Analytics", "2023 – Present", [
        "Built Python ETL pipelines ingesting 10 GB/day from third-party REST APIs into Snowflake",
        "Developed FastAPI endpoints exposing aggregated metrics to a React dashboard",
        "Wrote pytest suites for data quality validation; maintained 78% coverage",
        "Managed deployments on AWS Lambda and ECS with Docker containers",
    ])
    job("Data Analyst / Python Scripter", "RetailMetrics Ltd.", "2022 – 2023", [
        "Automated Google Analytics and Salesforce reporting with Python scripts, saving 10 hrs/week",
        "Built PostgreSQL queries and views for executive dashboards in Metabase",
        "Collaborated with senior engineers to scope API integration requirements",
    ])

    section_heading(doc, "Skills", color="0F172A")
    for line in [
        "Languages:       Python, SQL, JavaScript (basic)",
        "Frameworks:      FastAPI, Flask, pandas, SQLAlchemy, pytest",
        "Infrastructure:  AWS (Lambda, ECS, S3, RDS), Docker, GitHub Actions",
        "Databases:       PostgreSQL, MySQL, Snowflake, Redis (basic)",
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.add_run(line).font.size = Pt(10)

    section_heading(doc, "Education", color="0F172A")
    ep = doc.add_paragraph()
    bold_run(ep, "B.S. Information Technology", size=10)
    normal_run(ep, "  ·  University of Denver  ·  2022")

    doc.save(OUT_DIR / "james_okafor.docx")
    print("  [ok] james_okafor.docx")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating sample .docx resumes...")
    make_frank_nguyen()
    make_grace_kim()
    make_henry_patel()
    make_isabella_ross()
    make_james_okafor()
    print(f"\nDone — 5 resumes written to {OUT_DIR}/")
