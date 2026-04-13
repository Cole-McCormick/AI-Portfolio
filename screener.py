#!/usr/bin/env python3
"""
Resume Screener — uses Claude to score and rank resumes against a job description.

Usage:
    python screener.py                          # uses defaults
    python screener.py --job myjob.txt --resumes ./resumes/
    python screener.py --job myjob.txt --resumes resume.pdf --output out.csv
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

try:
    from pypdf import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document as DocxDocument
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False


# ── Resume loading ────────────────────────────────────────────────────────────

def load_resume(path: Path) -> str:
    """Return text content of a resume (PDF, DOCX, or plain text)."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        if not PDF_SUPPORT:
            raise RuntimeError(
                f"Cannot read '{path}': install pypdf  →  pip install pypdf"
            )
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError(f"PDF '{path}' appears to contain no extractable text.")
        return text

    if suffix == ".docx":
        if not DOCX_SUPPORT:
            raise RuntimeError(
                f"Cannot read '{path}': install python-docx  →  pip install python-docx"
            )
        doc = DocxDocument(str(path))
        parts: list[str] = []
        for block in doc.element.body:
            tag = block.tag.split("}")[-1]
            if tag == "p":
                # Regular paragraph
                from docx.oxml.ns import qn
                text = "".join(node.text or "" for node in block.iter() if node.tag == qn("w:t"))
                if text.strip():
                    parts.append(text)
            elif tag == "tbl":
                # Table — extract each cell's text
                for row in block.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                    cells = []
                    for cell in row.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                        cell_text = "".join(
                            node.text or ""
                            for node in cell.iter()
                            if node.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
                        )
                        if cell_text.strip():
                            cells.append(cell_text.strip())
                    if cells:
                        parts.append(" | ".join(cells))
        text = "\n".join(parts).strip()
        if not text:
            raise ValueError(f"DOCX '{path}' appears to contain no extractable text.")
        return text

    return path.read_text(encoding="utf-8").strip()


def collect_resume_files(path: Path) -> list[Path]:
    """Return all .txt / .pdf files under a path (file or directory)."""
    if path.is_file():
        return [path]
    if path.is_dir():
        files = sorted(
            p for p in path.iterdir()
            if p.is_file() and p.suffix.lower() in (".txt", ".pdf", ".docx")
        )
        return files
    raise FileNotFoundError(f"Resume path not found: {path}")


# ── Scoring ───────────────────────────────────────────────────────────────────

SCORE_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "score": {
                "type": "integer",
                "description": "Fit score from 0 (no match) to 100 (perfect match)",
            },
            "explanation": {
                "type": "string",
                "description": "2–3 sentence explanation highlighting key strengths and gaps",
            },
        },
        "required": ["score", "explanation"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = (
    "You are an expert technical recruiter. "
    "Evaluate candidate resumes against job descriptions and return structured JSON scores. "
    "Base scores on skills match, years of relevant experience, domain fit, and seniority. "
    "Be honest: penalise clear skill gaps and reward strong alignment."
)


def score_resume(
    client: anthropic.Anthropic,
    job_description: str,
    resume_text: str,
    candidate_name: str,
) -> dict[str, Any]:
    """
    Call Claude to score one resume.

    Prompt caching is used for the system prompt and job description so that
    every resume after the first benefits from a cache hit on the stable prefix.
    """
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    # Cache the job description — identical across all resume calls
                    {
                        "type": "text",
                        "text": f"JOB DESCRIPTION:\n\n{job_description}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    # Vary only the resume per call (not cached)
                    {
                        "type": "text",
                        "text": (
                            f"CANDIDATE: {candidate_name}\n\n"
                            f"RESUME:\n\n{resume_text}\n\n"
                            "Return a JSON object with exactly two fields: "
                            '"score" (integer 0–100) and "explanation" (2–3 sentences).'
                        ),
                    },
                ],
            }
        ],
        output_config={"format": SCORE_SCHEMA},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ── Output ────────────────────────────────────────────────────────────────────

def print_results(results: list[dict[str, Any]]) -> None:
    width = 60
    print()
    print("=" * width)
    print(" RANKED CANDIDATES")
    print("=" * width)
    for rank, r in enumerate(results, 1):
        score_str = f"{r['score']}/100" if r["score"] >= 0 else "  N/A"
        print(f"\n  #{rank}  {r['name']}")
        print(f"       Score : {score_str}")
        print(f"       {r['explanation']}")
    print()


def save_csv(results: list[dict[str, Any]], output: Path) -> None:
    fieldnames = ["rank", "name", "score", "explanation", "file"]
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rank, r in enumerate(results, 1):
            writer.writerow(
                {
                    "rank": rank,
                    "name": r["name"],
                    "score": r["score"] if r["score"] >= 0 else "",
                    "explanation": r["explanation"],
                    "file": r["file"],
                }
            )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Screen resumes against a job description using Claude"
    )
    parser.add_argument(
        "--job",
        type=Path,
        default=Path("sample_job.txt"),
        help="Path to job description file  (default: sample_job.txt)",
    )
    parser.add_argument(
        "--resumes",
        type=Path,
        default=Path("sample_resumes"),
        help="Resume file or directory of resumes  (default: sample_resumes/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results.csv"),
        help="Output CSV file  (default: results.csv)",
    )
    args = parser.parse_args()

    # ── Load job description ──────────────────────────────────────────────────
    if not args.job.exists():
        print(f"Error: job description file not found: {args.job}", file=sys.stderr)
        sys.exit(1)
    job_description = args.job.read_text(encoding="utf-8").strip()
    print(f"Job description : {args.job}")

    # ── Collect resumes ───────────────────────────────────────────────────────
    try:
        resume_files = collect_resume_files(args.resumes)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not resume_files:
        print(f"Error: no .txt or .pdf files found in {args.resumes}", file=sys.stderr)
        sys.exit(1)

    print(f"Resumes found   : {len(resume_files)}")
    print()

    # ── Initialise Anthropic client ───────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY environment variable is not set.\n"
            "       Set it with:  export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    # ── Score each resume ─────────────────────────────────────────────────────
    results: list[dict[str, Any]] = []
    for idx, resume_path in enumerate(resume_files, 1):
        candidate_name = resume_path.stem.replace("_", " ").title()
        print(f"[{idx}/{len(resume_files)}] Screening {candidate_name} ...", end=" ", flush=True)

        try:
            resume_text = load_resume(resume_path)
            scored = score_resume(client, job_description, resume_text, candidate_name)
            results.append(
                {
                    "name": candidate_name,
                    "file": str(resume_path),
                    "score": scored["score"],
                    "explanation": scored["explanation"],
                }
            )
            print(f"score {scored['score']}/100")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR — {exc}", file=sys.stderr)
            results.append(
                {
                    "name": candidate_name,
                    "file": str(resume_path),
                    "score": -1,
                    "explanation": f"Error during scoring: {exc}",
                }
            )

    # ── Rank and display ──────────────────────────────────────────────────────
    results.sort(key=lambda r: r["score"], reverse=True)
    print_results(results)

    # ── Save CSV ──────────────────────────────────────────────────────────────
    save_csv(results, args.output)
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
