#!/usr/bin/env python3
"""
Candidate Scoring Dashboard — reads screener results.csv and produces:
  • dashboard.html  — interactive comparison view (open in any browser)
  • dashboard.pdf   — printable stakeholder report

Usage:
    python dashboard.py
    python dashboard.py --csv results.csv --job sample_job.txt
    python dashboard.py --csv results.csv --output report --title "Software Engineer"
    python dashboard.py --open            # auto-opens HTML in your browser
"""

import argparse
import csv
import sys
import webbrowser
from datetime import date
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )
    from reportlab.lib.colors import HexColor
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


# ── Tier logic ────────────────────────────────────────────────────────────────

def get_tier(score: int) -> tuple[str, str, str]:
    """Return (label, text_color_hex, bg_color_hex) for a score."""
    if score >= 75:
        return ("Advance", "#16a34a", "#dcfce7")
    elif score >= 50:
        return ("Consider", "#d97706", "#fef3c7")
    else:
        return ("Pass", "#6b7280", "#f3f4f6")


def tier_bar_color(score: int) -> str:
    if score >= 75:
        return "#16a34a"
    elif score >= 50:
        return "#d97706"
    return "#6b7280"


# ── Data loading ──────────────────────────────────────────────────────────────

def load_results(csv_path: Path) -> list[dict[str, Any]]:
    results = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                score = int(row["score"]) if row.get("score", "").strip() else -1
            except ValueError:
                score = -1
            results.append({
                "rank":        int(row.get("rank", 0) or 0),
                "name":        row.get("name", "Unknown").strip(),
                "score":       score,
                "explanation": row.get("explanation", "").strip(),
                "file":        row.get("file", "").strip(),
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
    return results


def extract_job_title(job_path: Path) -> str:
    for line in job_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            return line
    return "Open Role"


def first_sentence(text: str, max_chars: int = 200) -> str:
    """Return the first complete sentence, capped at max_chars."""
    idx = text.find(". ")
    if 0 < idx < max_chars:
        return text[: idx + 1]
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


# ── HTML generation ───────────────────────────────────────────────────────────

_HTML_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8fafc; color: #1e293b; font-size: 14px; line-height: 1.5;
}
.topbar {
    background: #4f46e5; color: white; padding: 14px 32px;
    display: flex; align-items: center; gap: 12px;
}
.topbar .logo { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
.topbar .sep  { opacity: 0.4; }
.topbar .sub  { opacity: 0.85; font-size: 13px; }
.container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
.meta { color: #64748b; font-size: 12px; margin-bottom: 24px; }
.stats {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin-bottom: 32px;
}
.stat-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 20px;
}
.stat-card .label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;
    color: #94a3b8; margin-bottom: 6px;
}
.stat-card .value { font-size: 28px; font-weight: 700; color: #1e293b; }
.stat-card .sub   { font-size: 12px; color: #64748b; margin-top: 4px; }
.section-title {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: #94a3b8; margin-bottom: 12px;
}
table {
    width: 100%; border-collapse: collapse; background: white;
    border-radius: 10px; overflow: hidden;
    border: 1px solid #e2e8f0; margin-bottom: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
thead tr { background: #f8fafc; border-bottom: 2px solid #e2e8f0; }
th {
    text-align: left; padding: 11px 16px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; color: #94a3b8;
}
tbody tr { border-bottom: 1px solid #f1f5f9; transition: background .1s; }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: #f8fafc; }
td { padding: 14px 16px; vertical-align: top; }
.rank  { color: #94a3b8; font-size: 12px; font-weight: 600; width: 36px; }
.tname { font-weight: 600; font-size: 14px; min-width: 140px; }
.score-cell { width: 120px; }
.score-num  { font-size: 22px; font-weight: 700; margin-bottom: 5px; }
.bar-bg   { background: #e5e7eb; border-radius: 4px; height: 5px; width: 100%; }
.bar-fill { height: 5px; border-radius: 4px; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 99px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.03em; white-space: nowrap;
}
.explanation { color: #475569; font-size: 13px; line-height: 1.6; }
.footer {
    text-align: center; color: #94a3b8; font-size: 11px;
    padding: 20px 0 8px;
}
"""


def generate_html(results: list[dict], job_title: str, output_path: Path) -> None:
    today_str = date.today().strftime("%B %d, %Y")
    total      = len(results)
    advancing  = sum(1 for r in results if r["score"] >= 75)
    considering = sum(1 for r in results if 50 <= r["score"] < 75)
    valid      = [r["score"] for r in results if r["score"] >= 0]
    avg_score  = round(sum(valid) / len(valid)) if valid else 0
    top_name   = results[0]["name"] if results else "—"

    rows = ""
    for r in results:
        s = r["score"]
        bar  = tier_bar_color(s)
        label, t_col, t_bg = get_tier(s)
        snippet = r["explanation"]
        if len(snippet) > 230:
            snippet = snippet[:230].rsplit(" ", 1)[0] + "…"
        rows += f"""
    <tr>
      <td class="rank">#{r['rank']}</td>
      <td class="tname">{r['name']}</td>
      <td class="score-cell">
        <div class="score-num" style="color:{bar}">{s}</div>
        <div class="bar-bg"><div class="bar-fill" style="width:{max(0,min(100,s))}%;background:{bar}"></div></div>
      </td>
      <td><span class="badge" style="color:{t_col};background:{t_bg}">{label}</span></td>
      <td class="explanation">{snippet}</td>
    </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Candidate Report — {job_title}</title>
<style>{_HTML_CSS}</style>
</head>
<body>
<div class="topbar">
  <span class="logo">HireAI</span>
  <span class="sep">|</span>
  <span class="sub">Candidate Screening Report</span>
</div>
<div class="container">
  <div class="meta">{job_title}&nbsp;&nbsp;·&nbsp;&nbsp;{today_str}&nbsp;&nbsp;·&nbsp;&nbsp;{total} candidates screened</div>

  <div class="stats">
    <div class="stat-card">
      <div class="label">Total Screened</div>
      <div class="value">{total}</div>
    </div>
    <div class="stat-card">
      <div class="label">Advance to Interview</div>
      <div class="value" style="color:#16a34a">{advancing}</div>
    </div>
    <div class="stat-card">
      <div class="label">Under Consideration</div>
      <div class="value" style="color:#d97706">{considering}</div>
    </div>
    <div class="stat-card">
      <div class="label">Average Score</div>
      <div class="value">{avg_score}</div>
      <div class="sub">out of 100</div>
    </div>
  </div>

  <div class="section-title">All Candidates — Ranked by Fit Score</div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Candidate</th><th>Score</th><th>Status</th><th>Summary</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>

  <div class="footer">Generated by HireAI &nbsp;·&nbsp; {today_str}</div>
</div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")


# ── PDF generation ────────────────────────────────────────────────────────────

def generate_pdf(results: list[dict], job_title: str, output_path: Path) -> None:
    if not PDF_SUPPORT:
        print("  PDF skipped — install reportlab:  pip install reportlab")
        return

    today_str = date.today().strftime("%B %d, %Y")
    total      = len(results)
    advancing  = sum(1 for r in results if r["score"] >= 75)
    considering = sum(1 for r in results if 50 <= r["score"] < 75)
    valid      = [r["score"] for r in results if r["score"] >= 0]
    avg_score  = round(sum(valid) / len(valid)) if valid else 0

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    base_styles = getSampleStyleSheet()
    brand   = HexColor("#4f46e5")
    c_green = HexColor("#16a34a")
    c_amber = HexColor("#d97706")
    c_gray  = HexColor("#6b7280")
    c_light = HexColor("#f8fafc")
    c_border = HexColor("#e2e8f0")
    c_text  = HexColor("#1e293b")
    c_muted = HexColor("#64748b")

    style_title = ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=c_text,
        spaceAfter=4,
    )
    style_sub = ParagraphStyle(
        "ReportSub",
        fontName="Helvetica",
        fontSize=10,
        textColor=c_muted,
        spaceAfter=16,
    )
    style_note = ParagraphStyle(
        "CandNote",
        fontName="Helvetica",
        fontSize=8,
        textColor=HexColor("#475569"),
        leading=11,
    )
    style_name = ParagraphStyle(
        "CandName",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=c_text,
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("HireAI &mdash; Candidate Screening Report", style_title))
    story.append(Paragraph(f"{job_title}&nbsp;&nbsp;|&nbsp;&nbsp;{today_str}&nbsp;&nbsp;|&nbsp;&nbsp;{total} candidates screened", style_sub))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceAfter=16))

    # ── Summary stats table ───────────────────────────────────────────────────
    stat_style = ParagraphStyle("StatVal", fontName="Helvetica-Bold", fontSize=18, textColor=c_text, leading=22)
    stat_label = ParagraphStyle("StatLbl", fontName="Helvetica", fontSize=7, textColor=c_muted, leading=10, spaceBefore=2)

    stats_data = [
        [
            Paragraph(str(total),      stat_style), Paragraph(str(advancing),   stat_style),
            Paragraph(str(considering), stat_style), Paragraph(str(avg_score),   stat_style),
        ],
        [
            Paragraph("Total Screened", stat_label), Paragraph("Advance to Interview", stat_label),
            Paragraph("Under Consideration", stat_label), Paragraph("Average Score / 100", stat_label),
        ],
    ]
    stats_table = Table(stats_data, colWidths=[1.6 * inch] * 4, hAlign="LEFT")
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light),
        ("BOX",        (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR",  (1, 0), (1, 0), c_green),
        ("TEXTCOLOR",  (2, 0), (2, 0), c_amber),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))

    # ── Candidates table ──────────────────────────────────────────────────────
    header_style = ParagraphStyle("Hdr", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)

    header_row = [
        Paragraph("#",         header_style),
        Paragraph("Candidate", header_style),
        Paragraph("Score",     header_style),
        Paragraph("Status",    header_style),
        Paragraph("Key Notes", header_style),
    ]
    table_data = [header_row]

    for r in results:
        s = r["score"]
        tier_label, t_col, _ = get_tier(s)
        score_color = HexColor(t_col)

        score_style = ParagraphStyle(
            f"Score{r['rank']}",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=score_color,
            leading=16,
        )
        badge_style = ParagraphStyle(
            f"Badge{r['rank']}",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=score_color,
        )
        note = first_sentence(r["explanation"], max_chars=210)

        table_data.append([
            Paragraph(f"#{r['rank']}", ParagraphStyle("Rank", fontName="Helvetica", fontSize=9, textColor=c_muted)),
            Paragraph(r["name"],       style_name),
            Paragraph(str(s),          score_style),
            Paragraph(tier_label,      badge_style),
            Paragraph(note,            style_note),
        ])

    col_widths = [0.4 * inch, 1.35 * inch, 0.65 * inch, 0.8 * inch, 3.8 * inch]
    cand_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0), brand),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
        ("GRID",          (0, 0), (-1, -1), 0.4, c_border),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("ALIGN",         (2, 0), (2, -1), "CENTER"),
        ("ALIGN",         (3, 0), (3, -1), "CENTER"),
    ]
    cand_table.setStyle(TableStyle(ts))
    story.append(cand_table)

    # ── Footer via onFirstPage / onLaterPages ─────────────────────────────────
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(c_muted)
        canvas.drawString(0.75 * inch, 0.45 * inch, f"HireAI Candidate Report  ·  {today_str}")
        canvas.drawRightString(
            LETTER[0] - 0.75 * inch, 0.45 * inch,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an HTML dashboard and PDF report from screener results"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("results.csv"),
        help="Screener results CSV  (default: results.csv)",
    )
    parser.add_argument(
        "--job",
        type=Path,
        default=None,
        help="Job description file — used to extract the role title",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Role title override (skips parsing --job)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dashboard",
        help="Output file base name without extension  (default: dashboard)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the HTML report in the default browser after generating",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Skip PDF generation",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    results = load_results(args.csv)
    if not results:
        print("Error: no results found in CSV.", file=sys.stderr)
        sys.exit(1)

    if args.title:
        job_title = args.title
    elif args.job and args.job.exists():
        job_title = extract_job_title(args.job)
    else:
        job_title = "Open Role"

    html_path = Path(f"{args.output}.html")
    pdf_path  = Path(f"{args.output}.pdf")

    print(f"Loaded {len(results)} candidates from {args.csv}")
    print(f"Role: {job_title}")
    print()

    print(f"Generating HTML ... ", end="", flush=True)
    generate_html(results, job_title, html_path)
    print(f"done  ({html_path})")

    if not args.html_only:
        print(f"Generating PDF  ... ", end="", flush=True)
        generate_pdf(results, job_title, pdf_path)
        if PDF_SUPPORT:
            print(f"done  ({pdf_path})")

    # ── Console summary ───────────────────────────────────────────────────────
    advancing   = [r for r in results if r["score"] >= 75]
    considering = [r for r in results if 50 <= r["score"] < 75]
    passing     = [r for r in results if r["score"] < 50]

    width = 56
    print()
    print("=" * width)
    print(" SCREENING SUMMARY")
    print("=" * width)
    if advancing:
        print(f"\n  Advance ({len(advancing)})")
        for r in advancing:
            print(f"    #{r['rank']:>2}  {r['name']:<22}  {r['score']}/100")
    if considering:
        print(f"\n  Consider ({len(considering)})")
        for r in considering:
            print(f"    #{r['rank']:>2}  {r['name']:<22}  {r['score']}/100")
    if passing:
        print(f"\n  Pass ({len(passing)})")
        for r in passing:
            print(f"    #{r['rank']:>2}  {r['name']:<22}  {r['score']}/100")
    print()

    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
        print(f"Opened {html_path} in browser.")


if __name__ == "__main__":
    main()
