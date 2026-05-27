#!/usr/bin/env python3
"""
Interview Question Generator — uses Claude to produce tailored interview questions
from a job description and a candidate's resume.

Usage:
    python interview_questions.py                              # uses defaults
    python interview_questions.py --job myjob.txt --resume alice_chen.txt
    python interview_questions.py --job myjob.txt --resume resume.pdf --output questions.txt
"""

import argparse
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


# ── File loading (shared with screener.py) ────────────────────────────────────

def load_text_file(path: Path) -> str:
    """Return text content of a PDF, DOCX, or plain-text file."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        if not PDF_SUPPORT:
            raise RuntimeError(f"Cannot read '{path}': install pypdf  →  pip install pypdf")
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError(f"PDF '{path}' appears to contain no extractable text.")
        return text

    if suffix == ".docx":
        if not DOCX_SUPPORT:
            raise RuntimeError(f"Cannot read '{path}': install python-docx  →  pip install python-docx")
        doc = DocxDocument(str(path))
        parts: list[str] = []
        for block in doc.element.body:
            tag = block.tag.split("}")[-1]
            if tag == "p":
                from docx.oxml.ns import qn
                text = "".join(node.text or "" for node in block.iter() if node.tag == qn("w:t"))
                if text.strip():
                    parts.append(text)
            elif tag == "tbl":
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


# ── Question generation ───────────────────────────────────────────────────────

QUESTIONS_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "role_title": {
                "type": "string",
                "description": "Job title extracted from the job description",
            },
            "competency_areas": {
                "type": "array",
                "description": "Interview questions grouped by competency area",
                "items": {
                    "type": "object",
                    "properties": {
                        "area": {
                            "type": "string",
                            "description": "Competency area name (e.g. Technical Skills, Leadership)",
                        },
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The interview question to ask",
                                    },
                                    "rationale": {
                                        "type": "string",
                                        "description": "One sentence explaining why this question targets this specific candidate",
                                    },
                                },
                                "required": ["question", "rationale"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["area", "questions"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["role_title", "competency_areas"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = (
    "You are a senior hiring manager and expert interviewer. "
    "Given a job description and a candidate's resume, generate tailored interview questions "
    "that probe both the candidate's strengths and potential gaps relative to the role. "
    "Organize questions into 4–5 competency areas relevant to the position. "
    "Each area should have 2–3 questions. "
    "Questions must be specific to what you observe in the resume — not generic. "
    "For each question include a one-sentence rationale explaining why it targets this candidate. "
    "Return structured JSON."
)


def generate_questions(
    client: anthropic.Anthropic,
    job_description: str,
    resume_text: str,
    candidate_name: str,
) -> dict[str, Any]:
    """Call Claude to generate interview questions for one candidate."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
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
                    {
                        "type": "text",
                        "text": f"JOB DESCRIPTION:\n\n{job_description}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"CANDIDATE: {candidate_name}\n\n"
                            f"RESUME:\n\n{resume_text}\n\n"
                            "Generate tailored interview questions for this candidate."
                        ),
                    },
                ],
            }
        ],
        output_config={"format": QUESTIONS_SCHEMA},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ── Output ────────────────────────────────────────────────────────────────────

def print_questions(candidate_name: str, data: dict[str, Any]) -> None:
    width = 64
    print()
    print("=" * width)
    print(f"  INTERVIEW GUIDE — {candidate_name.upper()}")
    print(f"  Role: {data['role_title']}")
    print("=" * width)

    for area in data["competency_areas"]:
        print(f"\n  [{area['area'].upper()}]")
        for i, q in enumerate(area["questions"], 1):
            print(f"\n  {i}. {q['question']}")
            print(f"     > {q['rationale']}")

    print()


def save_txt(candidate_name: str, data: dict[str, Any], output: Path) -> None:
    lines = [
        f"INTERVIEW GUIDE — {candidate_name}",
        f"Role: {data['role_title']}",
        "",
    ]
    for area in data["competency_areas"]:
        lines.append(f"[{area['area'].upper()}]")
        for i, q in enumerate(area["questions"], 1):
            lines.append(f"  {i}. {q['question']}")
            lines.append(f"     Rationale: {q['rationale']}")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")


def save_json(data: dict[str, Any], output: Path) -> None:
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate tailored interview questions from a job description and resume"
    )
    parser.add_argument(
        "--job",
        type=Path,
        default=Path("sample_job.txt"),
        help="Path to job description file  (default: sample_job.txt)",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=Path("sample_resumes/alice_chen.txt"),
        help="Path to a single resume file  (default: sample_resumes/alice_chen.txt)",
    )
    parser.add_argument(
        "--candidate",
        type=str,
        default=None,
        help="Candidate name override  (default: derived from filename)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (.txt or .json)  (default: questions_<candidate>.txt)",
    )
    args = parser.parse_args()

    # ── Validate inputs ───────────────────────────────────────────────────────
    if not args.job.exists():
        print(f"Error: job description not found: {args.job}", file=sys.stderr)
        sys.exit(1)
    if not args.resume.exists():
        print(f"Error: resume file not found: {args.resume}", file=sys.stderr)
        sys.exit(1)

    job_description = args.job.read_text(encoding="utf-8").strip()
    resume_text = load_text_file(args.resume)

    candidate_name = args.candidate or args.resume.stem.replace("_", " ").title()

    output_path = args.output
    if output_path is None:
        slug = args.resume.stem.lower()
        output_path = Path(f"questions_{slug}.txt")

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

    # ── Generate questions ────────────────────────────────────────────────────
    print(f"Job description : {args.job}")
    print(f"Candidate       : {candidate_name}  ({args.resume})")
    print("Generating questions ...", end=" ", flush=True)

    try:
        data = generate_questions(client, job_description, resume_text, candidate_name)
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)

    print("done")

    # ── Display and save ──────────────────────────────────────────────────────
    print_questions(candidate_name, data)

    if output_path.suffix.lower() == ".json":
        save_json(data, output_path)
    else:
        save_txt(candidate_name, data, output_path)

    print(f"Questions saved to: {output_path}")


if __name__ == "__main__":
    main()
