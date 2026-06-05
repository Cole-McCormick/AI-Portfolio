#!/usr/bin/env python3
"""
Hiring Memo Generator — produces per-candidate hiring briefs and a
comparative analysis across the top candidates.

Usage:
    python hiring_memo.py                           # top 3 from results.csv
    python hiring_memo.py --top 5                   # top 5 candidates
    python hiring_memo.py --job myjob.txt --results results.csv
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


SYSTEM_PROMPT = (
    "You are a senior technical recruiter with 15 years of experience placing engineering talent. "
    "Write direct, actionable hiring briefs that help busy hiring managers make fast, confident decisions. "
    "Be honest about weaknesses. Focus only on what matters for the specific role. "
    "Never use filler phrases. Every sentence should give the hiring manager something useful to act on."
)

MEMO_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "hiring_brief": {
                "type": "string",
                "description": (
                    "3 paragraphs separated by newlines. "
                    "P1: who this person is and exactly why their background matters for THIS role — "
                    "be specific about their domain experience and technical match. "
                    "P2: the real concerns, stated plainly. "
                    "P3: clear recommendation and suggested next step."
                ),
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3–5 specific, concrete strengths directly relevant to this role. Not generic praise.",
            },
            "concerns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1–3 honest concerns. Empty array if truly none.",
            },
            "red_flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "flag": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                    "required": ["flag", "detail"],
                    "additionalProperties": False,
                },
                "description": (
                    "Pattern-based red flags only: unexplained employment gaps, rapid job hopping "
                    "(3+ jobs in 3 years), vague bullets with no metrics, title inflation, "
                    "scope inconsistencies. Empty array if none."
                ),
            },
            "salary_signal": {
                "type": "string",
                "description": (
                    "Estimated salary expectation based on titles, company sizes, tenure, and trajectory. "
                    "Give a specific range like '$105–125k'. Note any mismatch with the posted range."
                ),
            },
            "key_question": {
                "type": "string",
                "description": (
                    "The single most important question to ask in the first interview — "
                    "specific to this candidate's background and a real unknown for this role."
                ),
            },
            "recommendation": {
                "type": "string",
                "enum": ["Strong Advance", "Advance", "Consider", "Pass"],
            },
            "rejection_email": {
                "type": "string",
                "description": (
                    "Short, personalized, professional rejection email. "
                    "Reference one specific thing from their background. Warm but clear. "
                    "No generic templates. Sign off with '[Your name]'."
                ),
            },
            "interview_invite": {
                "type": "string",
                "description": (
                    "Short, enthusiastic interview invite. Reference why this candidate's background stood out. "
                    "Include placeholder '[SCHEDULING LINK]'. Sign off with '[Your name]'."
                ),
            },
        },
        "required": [
            "hiring_brief", "strengths", "concerns", "red_flags",
            "salary_signal", "key_question", "recommendation",
            "rejection_email", "interview_invite",
        ],
        "additionalProperties": False,
    },
}

COMPARATIVE_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "executive_summary": {
                "type": "string",
                "description": (
                    "2–3 sentences summarizing the overall candidate pool quality. "
                    "Written for a leadership meeting — calibrate expectations honestly."
                ),
            },
            "hire_recommendation": {
                "type": "string",
                "description": (
                    "One clear paragraph: who you would hire and exactly why. "
                    "If it's close, name the tiebreaker explicitly. "
                    "If there's a clear winner, state it plainly."
                ),
            },
            "comparisons": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "unique_value": {
                            "type": "string",
                            "description": "What this candidate brings that the others don't.",
                        },
                        "biggest_risk": {
                            "type": "string",
                            "description": "The one thing that could make this hire go wrong.",
                        },
                    },
                    "required": ["name", "unique_value", "biggest_risk"],
                    "additionalProperties": False,
                },
            },
            "interview_sequence": {
                "type": "string",
                "description": "Recommended order to interview these candidates and why. 2–3 sentences.",
            },
        },
        "required": ["executive_summary", "hire_recommendation", "comparisons", "interview_sequence"],
        "additionalProperties": False,
    },
}


def generate_candidate_memo(
    client: anthropic.Anthropic,
    job_description: str,
    resume_text: str,
    candidate_name: str,
    screen_score: int,
    screen_explanation: str,
) -> dict[str, Any]:
    """Generate a complete hiring memo for one candidate."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
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
                            f"CANDIDATE: {candidate_name}\n"
                            f"SCREENING SCORE: {screen_score}/100\n"
                            f"SCREENER SUMMARY: {screen_explanation}\n\n"
                            f"RESUME:\n\n{resume_text}\n\n"
                            "Generate a complete hiring memo for this candidate."
                        ),
                    },
                ],
            }
        ],
        output_config={"format": MEMO_SCHEMA},
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def generate_comparative_analysis(
    client: anthropic.Anthropic,
    job_description: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare top candidates head-to-head and produce a hiring recommendation.

    Each entry in `candidates` must have: name, score, explanation, resume_text.
    """
    blocks = "\n\n".join(
        f"--- {c['name']} (Score: {c['score']}/100) ---\n"
        f"Screener summary: {c['explanation']}\n\n"
        f"Resume:\n{c['resume_text']}"
        for c in candidates
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
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
                            f"Compare these top candidates head-to-head for the role above:\n\n"
                            f"{blocks}\n\n"
                            "Produce a comparative analysis memo with a clear hiring recommendation."
                        ),
                    },
                ],
            }
        ],
        output_config={"format": COMPARATIVE_SCHEMA},
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import csv
    from screener import load_resume, collect_resume_files

    parser = argparse.ArgumentParser(description="Generate hiring memos from screener results")
    parser.add_argument("--job",     type=Path, default=Path("sample_job.txt"))
    parser.add_argument("--results", type=Path, default=Path("results.csv"))
    parser.add_argument("--resumes", type=Path, default=Path("sample_resumes"))
    parser.add_argument("--top",     type=int,  default=3, help="Number of top candidates")
    parser.add_argument("--output",  type=Path, default=Path("memos.json"))
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    job_description = args.job.read_text(encoding="utf-8").strip()

    with open(args.results, newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["score"] or 0), reverse=True)

    top_rows = rows[:args.top]
    resume_dir = args.resumes

    all_memos: dict[str, Any] = {}
    comp_candidates = []

    for i, row in enumerate(top_rows, 1):
        name = row["name"]
        score = int(row["score"] or 0)
        explanation = row["explanation"]
        print(f"[{i}/{len(top_rows)}] Generating memo for {name}...", end=" ", flush=True)

        file_path = Path(row["file"]) if row.get("file") else None
        if file_path and file_path.exists():
            resume_text = load_resume(file_path)
        else:
            candidates = collect_resume_files(resume_dir)
            match = next((p for p in candidates if name.lower().replace(" ", "_") in p.stem.lower()), None)
            if not match:
                print("SKIP (resume not found)")
                continue
            resume_text = load_resume(match)

        memo = generate_candidate_memo(client, job_description, resume_text, name, score, explanation)
        all_memos[name] = memo
        comp_candidates.append({"name": name, "score": score, "explanation": explanation, "resume_text": resume_text})
        print(memo["recommendation"])

    print("\nGenerating comparative analysis...", end=" ", flush=True)
    comparative = generate_comparative_analysis(client, job_description, comp_candidates[:3])
    print("done")

    output = {"comparative": comparative, "memos": all_memos}
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nMemos saved to: {args.output}")


if __name__ == "__main__":
    main()
