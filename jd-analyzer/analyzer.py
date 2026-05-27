"""
JD Analyzer — scores job descriptions on bias, clarity, inclusivity,
and candidate appeal, then exports a polished PDF report.

Usage:
    python analyzer.py
    python analyzer.py --output my_report.pdf

Requires: anthropic, reportlab, python-dotenv
    pip install anthropic reportlab python-dotenv
"""

import argparse
import json
import os
import textwrap
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load shared portfolio .env first; fall back to a local .env if present
_here = Path(__file__).parent
load_dotenv(_here.parent / ".env")          # Documents/ai-portfolio/.env  (primary)
load_dotenv(_here / ".env", override=False) # jd-analyzer/.env             (fallback, won't override)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sample_jds import ALL_JDS

# ─────────────────────────────────────────────────────────────
# Analysis prompt
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert HR consultant and DEI specialist with deep
expertise in job description analysis. You evaluate job postings objectively,
identifying patterns that attract or deter qualified candidates.

When scoring, use the full 1-10 range:
  1-3  = significant problems that will harm hiring outcomes
  4-6  = average — common issues, room for improvement
  7-9  = good — minor issues
  10   = exceptional — rare

Be specific, actionable, and honest. Praise what works; flag what doesn't."""

ANALYSIS_PROMPT = """Analyze the following job description across four dimensions.
Return ONLY valid JSON — no markdown fences, no preamble.

Dimensions:
  1. bias        — gendered/coded language, unnecessary requirements, exclusionary phrases
  2. clarity     — role expectations, responsibilities, and scope are easy to understand
  3. inclusivity — welcoming tone, accommodations, salary transparency, equitable requirements
  4. appeal      — would strong candidates be excited to apply?

For each dimension provide:
  - score      (integer 1-10)
  - summary    (1-2 sentence verdict, 50 words max)
  - issues     (list of 1-4 specific problems found; empty list if none)
  - suggestions (list of 1-4 concrete, actionable fixes; empty list if no issues)

Also provide:
  - overall_grade  (letter: A / B / C / D / F)
  - overall_summary (2-3 sentence overall assessment, 80 words max)
  - top_strengths   (list of up to 3 things done well)
  - top_priorities  (list of up to 3 highest-impact improvements)

JSON schema:
{
  "bias":        { "score": int, "summary": str, "issues": [str], "suggestions": [str] },
  "clarity":     { "score": int, "summary": str, "issues": [str], "suggestions": [str] },
  "inclusivity": { "score": int, "summary": str, "issues": [str], "suggestions": [str] },
  "appeal":      { "score": int, "summary": str, "issues": [str], "suggestions": [str] },
  "overall_grade": str,
  "overall_summary": str,
  "top_strengths":   [str],
  "top_priorities":  [str]
}

Job Description:
---
{jd_text}
---"""


# ─────────────────────────────────────────────────────────────
# Claude API call
# ─────────────────────────────────────────────────────────────

def analyze_jd(client: anthropic.Anthropic, jd_text: str, max_retries: int = 3) -> dict:
    """Call Claude and return parsed analysis dict. Retries on bad JSON."""
    prompt = ANALYSIS_PROMPT.replace("{jd_text}", jd_text)

    for attempt in range(1, max_retries + 1):
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            final = stream.get_final_message()

        text = next(
            block.text for block in final.content if block.type == "text"
        )

        # Try clean parse, then extract the JSON object, then retry
        for extractor in (
            lambda t: t.strip(),
            lambda t: t[t.find("{") : t.rfind("}") + 1],
        ):
            try:
                return json.loads(extractor(text))
            except (json.JSONDecodeError, ValueError):
                continue

        if attempt < max_retries:
            print(f"\r         Retrying (attempt {attempt + 1}/{max_retries})...", end="", flush=True)

    raise ValueError(f"Claude returned invalid JSON after {max_retries} attempts")


# ─────────────────────────────────────────────────────────────
# Score helpers
# ─────────────────────────────────────────────────────────────

GRADE_COLORS = {
    "A": colors.HexColor("#1a7f37"),
    "B": colors.HexColor("#0969da"),
    "C": colors.HexColor("#bf8700"),
    "D": colors.HexColor("#cf222e"),
    "F": colors.HexColor("#82071e"),
}

SCORE_COLORS = [
    (1, 3, colors.HexColor("#cf222e")),
    (4, 6, colors.HexColor("#bf8700")),
    (7, 8, colors.HexColor("#0969da")),
    (9, 10, colors.HexColor("#1a7f37")),
]

DIMENSION_ICONS = {
    "bias": "⚖",
    "clarity": "◎",
    "inclusivity": "♡",
    "appeal": "★",
}

DIMENSION_LABELS = {
    "bias": "Bias",
    "clarity": "Clarity",
    "inclusivity": "Inclusivity",
    "appeal": "Candidate Appeal",
}


def score_color(score: int) -> colors.HexColor:
    for lo, hi, c in SCORE_COLORS:
        if lo <= score <= hi:
            return c
    return colors.grey



def avg_score(analysis: dict) -> float:
    dims = ["bias", "clarity", "inclusivity", "appeal"]
    return sum(analysis[d]["score"] for d in dims) / len(dims)


# ─────────────────────────────────────────────────────────────
# PDF palette + layout constants
# ─────────────────────────────────────────────────────────────

BRAND_BLUE  = colors.HexColor("#0969da")
BRAND_DARK  = colors.HexColor("#1f2937")
BRAND_LIGHT = colors.HexColor("#f6f8fa")
BORDER_GREY = colors.HexColor("#d0d7de")

# Cover header dimensions (inches from top of page)
_COVER_DARK_H   = 2.8   # dark band
_COVER_STRIPE_H = 0.3   # blue accent stripe beneath it
_COVER_TOTAL_H  = _COVER_DARK_H + _COVER_STRIPE_H  # 3.1 in


# ─────────────────────────────────────────────────────────────
# Style registry
# ─────────────────────────────────────────────────────────────

def build_styles() -> dict:
    return {
        "jd_title": ParagraphStyle(
            "jd_title", fontSize=18, fontName="Helvetica-Bold",
            textColor=BRAND_DARK, spaceBefore=6, spaceAfter=4,
        ),
        "overall_summary": ParagraphStyle(
            "overall_summary", fontSize=10, fontName="Helvetica",
            textColor=BRAND_DARK, leading=15,
        ),
        "dim_summary": ParagraphStyle(
            "dim_summary", fontSize=9, fontName="Helvetica",
            textColor=BRAND_DARK, leading=13,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontSize=9, fontName="Helvetica",
            textColor=BRAND_DARK, leading=14, leftIndent=12,
        ),
        "small_label": ParagraphStyle(
            "small_label", fontSize=8, fontName="Helvetica-Bold",
            textColor=colors.HexColor("#6e7781"), spaceAfter=2,
        ),
        "toc_entry": ParagraphStyle(
            "toc_entry", fontSize=11, fontName="Helvetica",
            textColor=BRAND_DARK, leading=22,
        ),
    }


# ─────────────────────────────────────────────────────────────
# Low-level helpers
# ─────────────────────────────────────────────────────────────

def hr(width: float = 6.5) -> HRFlowable:
    return HRFlowable(width=width * inch, thickness=0.5, color=BORDER_GREY, spaceAfter=6)


def spacer(h: float = 0.15) -> Spacer:
    return Spacer(1, h * inch)


def graphical_bar(score: int, bar_width: float = 1.5) -> Table:
    """Graphical score bar: colored filled cell + grey empty cell."""
    total = bar_width * inch
    filled_w = total * score / 10.0
    empty_w  = total - filled_w
    if filled_w < 1:
        filled_w, empty_w = 1.0, total - 1.0
    elif empty_w < 1:
        filled_w, empty_w = total - 1.0, 1.0
    sc = score_color(score)
    tbl = Table([["", ""]], colWidths=[filled_w, empty_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), sc),
        ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#e2e8f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return tbl


def grade_badge(grade: str, font_size: int = 30, width: float = 1.0) -> Table:
    """Grade letter on a bold colored-background badge."""
    gc = GRADE_COLORS.get(grade, colors.grey)
    p = Paragraph(
        f'<font color="white" size="{font_size}"><b>{grade}</b></font>',
        ParagraphStyle("gb", alignment=TA_CENTER, leading=font_size + 4),
    )
    tbl = Table([[p]], colWidths=[width * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), gc),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def accent_header(text: str, accent_color=None) -> Table:
    """Bold section header with a left-side accent color bar."""
    if accent_color is None:
        accent_color = BRAND_BLUE
    p = Paragraph(
        f"<b>{text}</b>",
        ParagraphStyle("ah", fontSize=13, fontName="Helvetica-Bold",
                       textColor=BRAND_DARK, leading=16),
    )
    tbl = Table([["", p]], colWidths=[0.07 * inch, 6.43 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), accent_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (0, 0), 0),
        ("LEFTPADDING",   (1, 0), (1, 0), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    return tbl


def score_table_row(label: str, icon: str, score: int, summary: str, styles: dict) -> list:
    """One row for the dimension score table: score | label + graphical bar | summary."""
    sc = score_color(score)
    score_cell = Paragraph(
        f'<font color="{sc.hexval()}" size="22"><b>{score}</b></font>'
        f'<br/><font size="8" color="#6e7781">/10</font>',
        ParagraphStyle("sc", alignment=TA_CENTER, leading=26),
    )
    bar = graphical_bar(score, bar_width=1.65)
    label_inner = Table(
        [
            [Paragraph(f"<b>{label}</b>",
                       ParagraphStyle("lc", fontSize=11, fontName="Helvetica-Bold",
                                      textColor=BRAND_DARK, leading=14))],
            [bar],
        ],
        colWidths=[1.75 * inch],
    )
    label_inner.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return [score_cell, label_inner, Paragraph(summary, styles["dim_summary"])]


def bullet_list(items: list, prefix: str, color_hex: str, styles: dict) -> list:
    """Return Paragraph flowables for a labelled bullet list."""
    if not items:
        return []
    result = [Paragraph(prefix, styles["small_label"])]
    for item in items:
        result.append(
            Paragraph(
                f'<font color="{color_hex}">-</font> {item}',
                styles["bullet"],
            )
        )
    return result


# ─────────────────────────────────────────────────────────────
# Canvas callbacks (drawn directly, not as flowables)
# ─────────────────────────────────────────────────────────────

def _draw_cover(canvas, doc):
    """Full-bleed cover header + footer drawn directly on the canvas."""
    w, h = LETTER

    # Dark background band
    canvas.setFillColor(BRAND_DARK)
    canvas.rect(0, h - _COVER_DARK_H * inch, w, _COVER_DARK_H * inch, fill=1, stroke=0)

    # Blue accent stripe
    canvas.setFillColor(BRAND_BLUE)
    canvas.rect(0, h - _COVER_TOTAL_H * inch, w, _COVER_STRIPE_H * inch, fill=1, stroke=0)

    # Main title
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 42)
    canvas.drawCentredString(w / 2, h - 1.35 * inch, "JD ANALYZER")

    # Subtitle
    canvas.setFont("Helvetica", 14)
    canvas.setFillColor(colors.HexColor("#93c5fd"))
    canvas.drawCentredString(w / 2, h - 1.95 * inch, "Job Description Intelligence Report")

    # Decorative separator dots
    canvas.setFillColor(colors.HexColor("#374151"))
    for dx in (-0.35, 0.0, 0.35):
        canvas.circle(w / 2 + dx * inch, h - 2.38 * inch, 2.5, stroke=0, fill=1)

    # Date line
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.HexColor("#9ca3af"))
    canvas.drawCentredString(w / 2, h - 2.62 * inch, datetime.now().strftime("%B %d, %Y"))

    # Page footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6e7781"))
    canvas.drawCentredString(w / 2, 0.38 * inch, "JD Analyzer  |  Powered by Claude Opus 4.6")


def _draw_later_page(canvas, doc):
    """Thin branded header + page-number footer on every non-cover page."""
    w, h = LETTER

    # Top bar
    canvas.setFillColor(BRAND_BLUE)
    canvas.rect(0, h - 0.32 * inch, w, 0.32 * inch, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawString(inch, h - 0.20 * inch, "JD ANALYZER")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - inch, h - 0.20 * inch,
                           datetime.now().strftime("%B %d, %Y"))

    # Footer line + page number
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.4)
    canvas.line(inch, 0.55 * inch, w - inch, 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6e7781"))
    canvas.drawCentredString(w / 2, 0.33 * inch, f"Page {canvas.getPageNumber()}")


# ─────────────────────────────────────────────────────────────
# Cover page flowables
# ─────────────────────────────────────────────────────────────

def build_cover(results: list, styles: dict) -> list:
    elements = []

    # Skip past the full-bleed header band drawn by _draw_cover.
    # topMargin=0.75 in → first flowable at 0.75 in from top.
    # Band+stripe ends at 3.1 in from top → need (3.1 - 0.75) + 0.3 breathing room.
    elements.append(spacer(2.65))

    # Score Summary heading
    elements.append(
        Paragraph(
            "Score Summary",
            ParagraphStyle("ch", fontSize=15, fontName="Helvetica-Bold",
                           textColor=BRAND_DARK, spaceAfter=6),
        )
    )
    elements.append(spacer(0.08))

    # Scorecard table
    header = ["Job Description", "Grade", "Bias", "Clarity", "Incl.", "Appeal", "Avg"]
    rows = [header]
    for r in results:
        a = r["analysis"]
        rows.append([
            f"{r['label']}: {r['title'][:38]}",
            a["overall_grade"],
            str(a["bias"]["score"]),
            str(a["clarity"]["score"]),
            str(a["inclusivity"]["score"]),
            str(a["appeal"]["score"]),
            f"{avg_score(a):.1f}",
        ])

    col_widths = [2.5 * inch, 0.55 * inch] + [0.6 * inch] * 4 + [0.65 * inch]
    tbl = Table(rows, colWidths=col_widths)

    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ALIGN",         (1, 0), (-1,  0), "CENTER"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, BORDER_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for row_i, r in enumerate(results, start=1):
        a = r["analysis"]
        grade = a["overall_grade"]
        gc = GRADE_COLORS.get(grade, colors.grey)
        # Grade cell: colored background, white bold text
        ts += [
            ("BACKGROUND", (1, row_i), (1, row_i), gc),
            ("TEXTCOLOR",  (1, row_i), (1, row_i), colors.white),
            ("FONTNAME",   (1, row_i), (1, row_i), "Helvetica-Bold"),
            ("FONTSIZE",   (1, row_i), (1, row_i), 11),
        ]
        # Score cells: colored bold text
        for col_i, dim in enumerate(["bias", "clarity", "inclusivity", "appeal"], start=2):
            sc = score_color(a[dim]["score"])
            ts += [
                ("TEXTCOLOR", (col_i, row_i), (col_i, row_i), sc),
                ("FONTNAME",  (col_i, row_i), (col_i, row_i), "Helvetica-Bold"),
            ]

    tbl.setStyle(TableStyle(ts))
    elements.append(tbl)
    elements.append(spacer(0.5))

    # Table of Contents
    elements.append(accent_header("Contents"))
    elements.append(spacer(0.15))
    for i, r in enumerate(results, start=1):
        elements.append(
            Paragraph(
                f'<font color="#0969da"><b>{i}.</b></font>  '
                f'<b>{r["label"]} JD</b> \u2014 {r["title"]}',
                styles["toc_entry"],
            )
        )

    elements.append(PageBreak())
    return elements


# ─────────────────────────────────────────────────────────────
# Per-JD section flowables
# ─────────────────────────────────────────────────────────────

def build_jd_section(r: dict, styles: dict) -> list:
    elements = []
    a = r["analysis"]
    dims = ["bias", "clarity", "inclusivity", "appeal"]
    grade = a["overall_grade"]
    gc = GRADE_COLORS.get(grade, colors.grey)

    # ── Label badge + title ───────────────────────────────────
    label_badge = Table(
        [[Paragraph(f"  {r['label'].upper()} JD  ",
                    ParagraphStyle("lb", fontSize=9, fontName="Helvetica-Bold",
                                   textColor=colors.white))]],
        colWidths=[1.0 * inch],
    )
    label_badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(label_badge)
    elements.append(Paragraph(r["title"], styles["jd_title"]))
    elements.append(hr())

    # ── Grade badge + summary card ────────────────────────────
    avg = avg_score(a)
    badge = grade_badge(grade, font_size=30, width=1.0)
    meta_p = Paragraph(
        f'<font size="11"><b>Average score: {avg:.1f} / 10</b></font>'
        f'<br/><br/>{a["overall_summary"]}',
        ParagraphStyle("meta", fontSize=10, fontName="Helvetica",
                       textColor=BRAND_DARK, leading=15),
    )
    header_tbl = Table([[badge, meta_p]], colWidths=[1.1 * inch, 5.4 * inch])
    header_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (1, 0), (1,  0),  12),
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GREY),
    ]))
    elements.append(header_tbl)
    elements.append(spacer(0.25))

    # ── Strengths / Priorities two-column card ────────────────
    def icon_lines(items, icon_color, char):
        if not items:
            return '<font color="#6e7781"><i>None noted.</i></font>'
        return "<br/>".join(
            f'<font color="{icon_color}"><b>{char}</b></font>  {s}' for s in items
        )

    str_p = Paragraph(
        "<b>Top Strengths</b><br/>" + icon_lines(a.get("top_strengths", []), "#1a7f37", "+"),
        ParagraphStyle("sp", fontSize=9, fontName="Helvetica", textColor=BRAND_DARK,
                       leading=16, leftIndent=4),
    )
    pri_p = Paragraph(
        "<b>Top Priorities</b><br/>" + icon_lines(a.get("top_priorities", []), "#cf222e", "!"),
        ParagraphStyle("pp", fontSize=9, fontName="Helvetica", textColor=BRAND_DARK,
                       leading=16, leftIndent=4),
    )
    sp_tbl = Table([[str_p, pri_p]], colWidths=[3.2 * inch, 3.2 * inch])
    sp_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("LINEAFTER",     (0, 0), (0,  -1), 0.5, BORDER_GREY),
    ]))
    elements.append(sp_tbl)
    elements.append(spacer(0.3))

    # ── Dimension scores with graphical bars ──────────────────
    elements.append(accent_header("Dimension Scores"))
    elements.append(spacer(0.1))

    score_rows = [
        score_table_row(DIMENSION_LABELS[d], DIMENSION_ICONS[d],
                        a[d]["score"], a[d]["summary"], styles)
        for d in dims
    ]
    score_tbl = Table(score_rows, colWidths=[0.75 * inch, 2.05 * inch, 3.7 * inch])
    score_tbl.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",          (0, 0), (0,  -1), "CENTER"),
        ("TOPPADDING",     (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 9),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.4, BORDER_GREY),
    ]))
    elements.append(score_tbl)
    elements.append(spacer(0.3))

    # ── Issues & Suggestions, one KeepTogether card per dim ───
    elements.append(accent_header("Issues & Suggestions"))
    elements.append(spacer(0.15))

    for dim in dims:
        d = a[dim]
        sc = score_color(d["score"])

        dim_hdr = Table(
            [[
                Paragraph(
                    f'<font color="{sc.hexval()}" size="16"><b>{d["score"]}</b></font>'
                    f'<font size="8" color="#6e7781">/10</font>',
                    ParagraphStyle("dhs", alignment=TA_CENTER),
                ),
                Paragraph(
                    f'<b>{DIMENSION_LABELS[dim]}</b>',
                    ParagraphStyle("dhl", fontSize=11, fontName="Helvetica-Bold",
                                   textColor=BRAND_DARK),
                ),
            ]],
            colWidths=[0.75 * inch, 5.75 * inch],
        )
        dim_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BRAND_LIGHT),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (1, 0), (1,  0),  8),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ("LINEAFTER",     (0, 0), (0,  -1), 0.5, BORDER_GREY),
        ]))

        issues_fl = bullet_list(d.get("issues", []),      "ISSUES FOUND", "#cf222e", styles)
        sug_fl    = bullet_list(d.get("suggestions", []), "SUGGESTIONS",  "#0969da", styles)

        if not issues_fl and not sug_fl:
            body = [Paragraph(
                '<font color="#1a7f37">+ No significant issues found.</font>',
                ParagraphStyle("ok", fontSize=9, leftIndent=12, spaceAfter=4),
            )]
        else:
            body = issues_fl + sug_fl

        elements.append(KeepTogether([dim_hdr] + body + [spacer(0.1)]))

    elements.append(PageBreak())
    return elements


# ─────────────────────────────────────────────────────────────
# PDF assembly
# ─────────────────────────────────────────────────────────────

def build_pdf(results: list, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=LETTER,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="JD Analyzer Report",
        author="JD Analyzer",
    )

    styles = build_styles()
    story = []
    story.extend(build_cover(results, styles))
    for r in results:
        story.extend(build_jd_section(r, styles))

    doc.build(story, onFirstPage=_draw_cover, onLaterPages=_draw_later_page)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="JD Analyzer — score and report on job descriptions")
    parser.add_argument(
        "--output", "-o",
        default="jd_analysis_report.pdf",
        help="Path for the PDF report (default: jd_analysis_report.pdf)",
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        default=None,
        help="Path to a single JD text file to analyze (skips sample JDs)",
    )
    args = parser.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    if args.file:
        if not args.file.exists():
            print(f"Error: file not found: {args.file}", file=__import__("sys").stderr)
            raise SystemExit(1)
        jd_text = args.file.read_text(encoding="utf-8").strip()
        title = next((l.strip() for l in jd_text.splitlines() if l.strip()), str(args.file))
        jds_to_run = [{"label": "Custom", "title": title, "text": jd_text}]
    else:
        jds_to_run = ALL_JDS

    results = []
    total = len(jds_to_run)

    print(f"\n{'='*60}")
    print("  JD Analyzer — powered by Claude Opus 4.6")
    print(f"{'='*60}\n")

    for i, jd in enumerate(jds_to_run, 1):
        print(f"[{i}/{total}] Analyzing {jd['label']} JD: {jd['title']}")
        print("         Calling Claude...", end="", flush=True)

        analysis = analyze_jd(client, jd["text"])

        grade = analysis["overall_grade"]
        avg = avg_score(analysis)
        dims = ["bias", "clarity", "inclusivity", "appeal"]
        score_str = "  ".join(
            f"{d[:3].capitalize()}: {analysis[d]['score']}/10" for d in dims
        )
        print(f"\r         Grade: {grade}  |  Avg: {avg:.1f}  |  {score_str}")

        results.append({**jd, "analysis": analysis})

    print(f"\nBuilding PDF report -> {args.output}")
    build_pdf(results, args.output)

    size_kb = Path(args.output).stat().st_size // 1024
    print(f"Done! Report saved: {args.output} ({size_kb} KB)\n")

    # Print brief console summary
    print("-" * 60)
    print(f"{'JD':<35} {'Grade':>5}  {'Avg':>5}")
    print("-" * 60)
    for r in results:
        a = r["analysis"]
        print(f"{r['label'] + ': ' + r['title']:<35} {a['overall_grade']:>5}  {avg_score(a):>5.1f}")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
