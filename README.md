# Resume Screener

An AI-powered resume screening tool that uses [Claude](https://www.anthropic.com/claude) to score and rank candidate resumes against a job description. Built as a portfolio project demonstrating practical Claude API usage with prompt caching and structured outputs.

## Features

- **Multi-format support** — reads `.txt`, `.pdf`, and `.docx` resumes (including complex layouts with tables and columns)
- **Structured scoring** — Claude returns a numeric fit score (0–100) and a concise written explanation for each candidate
- **Prompt caching** — the job description is cached across API calls, reducing cost and latency on batches
- **Ranked output** — candidates are sorted by score and printed to the terminal
- **CSV export** — results are saved to a spreadsheet for sharing or further analysis

## Demo

```
Job description : sample_job.txt
Resumes found   : 5

[1/5] Screening Alice Chen ...    score 98/100
[2/5] Screening Eve Johnson ...   score 88/100
[3/5] Screening Carol White ...   score 62/100
[4/5] Screening David Kim ...     score  8/100
[5/5] Screening Bob Martinez ...  score  2/100

============================================================
 RANKED CANDIDATES
============================================================

  #1  Alice Chen
       Score : 98/100
       Alice is an exceptional match — 8 years of Python, direct payments domain
       experience (Stripe, Plaid, ACH), PCI-DSS certification, Kafka, and gRPC.
       ...
```

## How It Works

1. The job description and system prompt are sent to Claude with `cache_control` markers so they are cached on the first call and reused on every subsequent one.
2. Each resume is appended as the only non-cached part of the prompt.
3. Claude returns a structured JSON response (enforced via `output_config`) with a numeric `score` and a plain-English `explanation`.
4. Results are sorted by score and written to `results.csv`.

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com)

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/resume-screener.git
cd resume-screener

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# then edit .env and paste your key
```

> **Note:** `.env` is listed in `.gitignore` and will never be committed to version control.

## Configuration

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Screen a directory of resumes

```bash
python screener.py
# uses sample_job.txt and the sample_resumes/ directory by default
```

### Specify custom paths

```bash
python screener.py --job path/to/job.txt --resumes path/to/resumes/
```

### Screen a single resume

```bash
python screener.py --job path/to/job.txt --resumes path/to/candidate.pdf
```

### Change the output file

```bash
python screener.py --output my_results.csv
```

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `--job` | `sample_job.txt` | Path to the job description (`.txt`) |
| `--resumes` | `sample_resumes/` | Resume file or directory of resumes |
| `--output` | `results.csv` | Output CSV file path |

## Supported File Formats

| Format | Notes |
|--------|-------|
| `.txt` | Plain text |
| `.pdf` | Text-based PDFs (requires `pypdf`) |
| `.docx` | Word documents including tables and multi-column layouts (requires `python-docx`) |

## Sample Data

The repo includes ready-to-use sample data for testing:

| File | Description |
|------|-------------|
| `sample_job.txt` | Senior Python Developer role at a fictional fintech company |
| `sample_resumes/*.txt` | 5 plain-text resumes with varying qualification levels |
| `sample_resumes/*.docx` | 5 Word resumes with distinct layouts (sidebar tables, grids, shaded headers) |

Generate the `.docx` samples yourself:

```bash
python create_docx_resumes.py
```

## Project Structure

```
resume-screener/
├── screener.py               # Main script
├── create_docx_resumes.py    # Generator for sample .docx resumes
├── sample_job.txt            # Example job description
├── sample_resumes/           # Sample resumes (.txt and .docx)
├── requirements.txt
├── .env                      # API key — never committed
├── .env.example              # Safe template to commit
└── .gitignore
```

## Tech Stack

- **[Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)** — Claude API client
- **[pypdf](https://pypdf.readthedocs.io/)** — PDF text extraction
- **[python-docx](https://python-docx.readthedocs.io/)** — Word document parsing
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — `.env` file loading

## Claude API Concepts Demonstrated

- **Prompt caching** — `cache_control: {type: "ephemeral"}` on the system prompt and job description reduces API cost by up to 90% on repeated calls
- **Structured outputs** — `output_config` with a JSON schema guarantees machine-readable scores every time
- **Streaming-safe design** — `max_tokens` kept modest (512) for classification tasks; easily extended

## License

MIT
