"""
HireAI Demo — Streamlit portfolio showcasing the full AI hiring toolkit.

Run locally:
    cd demo
    streamlit run app.py

Deploy:
    Streamlit Community Cloud → point to demo/app.py
    Railway / Render         → streamlit run demo/app.py --server.port $PORT
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ── Path setup — import existing portfolio modules from parent dir ─────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "jd-analyzer"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="HireAI — AI-Powered Hiring",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"]    { background: #f1f5f9; }
[data-testid="stHeader"]              { background: transparent; }
[data-testid="stMainBlockContainer"]  { padding-top: 1.5rem; }

/* ── Hero ─────────────────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 55%, #7c3aed 100%);
    color: white; border-radius: 18px; padding: 52px 48px; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.hero::after {
    content: ''; position: absolute; top: -80px; right: -80px;
    width: 320px; height: 320px; border-radius: 50%;
    background: rgba(255,255,255,.05); pointer-events: none;
}
.hero h1 {
    font-size: 3.4rem; font-weight: 800; margin: 0 0 12px;
    letter-spacing: -2px; line-height: 1.05;
}
.hero .tagline { font-size: 1.05rem; opacity: .85; margin: 0 0 22px; line-height: 1.65; }
.hero .pill {
    display: inline-block; background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.28); border-radius: 99px;
    padding: 4px 13px; font-size: .78rem; margin-right: 7px; margin-bottom: 5px;
}
.hero-stat {
    background: rgba(255,255,255,.12); border-radius: 12px;
    padding: 16px; text-align: center;
}
.hero-stat .num { font-size: 1.9rem; font-weight: 800; line-height: 1; }
.hero-stat .lbl { font-size: .73rem; opacity: .78; margin-top: 4px; }

/* ── Feature cards ────────────────────────────────────────────────── */
.feature-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 24px; height: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
    transition: box-shadow .15s, transform .15s;
}
.feature-card:hover {
    box-shadow: 0 8px 24px rgba(79,70,229,.12);
    transform: translateY(-2px);
}
.feature-card .fc-icon  { font-size: 1.75rem; margin-bottom: 12px; }
.feature-card .fc-title { font-size: 1rem; font-weight: 700; margin-bottom: 7px; color: #1e293b; }
.feature-card .fc-desc  { font-size: .84rem; color: #64748b; line-height: 1.65; }

/* ── ROI ──────────────────────────────────────────────────────────── */
.roi-result-box {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white; border-radius: 14px; padding: 28px 22px; text-align: center;
    box-shadow: 0 4px 16px rgba(79,70,229,.25);
}
.roi-result-box .big-num { font-size: 2.8rem; font-weight: 800; letter-spacing: -1px; }
.roi-result-box .sub     { font-size: .85rem; opacity: .82; margin-top: 6px; }

.roi-breakdown {
    width: 100%; border-collapse: collapse;
    border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;
}
.roi-breakdown thead th {
    padding: 10px 14px; font-size: .74rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .05em;
    border-bottom: 2px solid #e2e8f0;
}
.roi-breakdown th.col-left   { background: #f8fafc; color: #94a3b8; text-align: left; }
.roi-breakdown th.col-manual { background: #fff1f2; color: #be123c; text-align: right; }
.roi-breakdown th.col-ai     { background: #f0fdf4; color: #15803d; text-align: right; }
.roi-breakdown td {
    padding: 10px 14px; font-size: .88rem; color: #374151;
    border-bottom: 1px solid #f1f5f9; background: white;
}
.roi-breakdown td.col-manual {
    background: #fff8f8; color: #b91c1c; text-align: right;
}
.roi-breakdown td.col-ai {
    background: #f8fff9; color: #15803d; font-weight: 600; text-align: right;
}
.roi-breakdown tr:last-child td { border-bottom: none; font-weight: 700; font-size: .92rem; }
.roi-note {
    font-size: .75rem; color: #94a3b8; margin-top: 7px; font-style: italic;
    padding-left: 4px;
}

/* ── Steps ────────────────────────────────────────────────────────── */
.step-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 13px;
    padding: 22px 16px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.step-num {
    background: #4f46e5; color: white; border-radius: 50%;
    width: 38px; height: 38px; line-height: 38px;
    font-weight: 800; font-size: 1rem; margin: 0 auto 11px;
}
.step-title  { font-weight: 700; font-size: .92rem; margin-bottom: 6px; color: #1e293b; }
.step-detail { font-size: .8rem; color: #64748b; line-height: 1.55; }

/* ── Candidate cards ──────────────────────────────────────────────── */
.cand-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.bar-bg   { background: #e5e7eb; border-radius: 4px; height: 6px; margin-top: 5px; }
.bar-fill { height: 6px; border-radius: 4px; }
.tier-chip {
    display: inline-block; padding: 2px 9px; border-radius: 99px;
    font-size: .72rem; font-weight: 600;
}

/* ── Interview cards ──────────────────────────────────────────────── */
.q-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 20px 24px; margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.q-card h4 {
    color: #4f46e5; font-size: .75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em; margin: 0 0 12px;
}
.q-item       { margin-bottom: 13px; }
.q-item .q    { font-size: .95rem; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.q-item .rat  { font-size: .82rem; color: #64748b; }

/* ── JD Analyzer ──────────────────────────────────────────────────── */
.dim-row {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.section-lbl {
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: #94a3b8; margin-bottom: 10px;
}

/* ── Hiring Memos ─────────────────────────────────────────────────── */
.compare-card {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    color: white; border-radius: 16px; padding: 28px; margin-bottom: 24px;
}
.compare-card h3 {
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; opacity: .65; margin: 0 0 10px;
}
.hire-rec-box {
    background: rgba(255,255,255,.12); border-radius: 10px;
    padding: 16px 20px; font-size: .92rem; line-height: 1.75;
    margin: 0 0 20px;
}
.compare-row {
    background: rgba(255,255,255,.08); border-radius: 10px;
    padding: 14px 18px; margin-bottom: 8px;
    display: grid; grid-template-columns: 150px 1fr 1fr; gap: 16px; align-items: start;
}
.compare-row .cr-name { font-weight: 700; font-size: .9rem; }
.compare-row .cr-lbl  { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; opacity: .55; margin-bottom: 3px; }
.compare-row .cr-val  { font-size: .84rem; opacity: .9; line-height: 1.55; }
.compare-seq {
    background: rgba(255,255,255,.08); border-radius: 10px;
    padding: 14px 18px; font-size: .85rem; line-height: 1.65; opacity: .88;
    margin-top: 4px;
}

.memo-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 16px;
    padding: 28px; margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.memo-header {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 20px; padding-bottom: 16px;
    border-bottom: 1px solid #f1f5f9;
}
.memo-header .mh-rank { font-size: 1.5rem; font-weight: 800; color: #94a3b8; min-width: 28px; }
.memo-header .mh-name { font-size: 1.1rem; font-weight: 800; color: #1e293b; }
.memo-header .mh-score { font-size: .82rem; color: #64748b; }
.rec-badge {
    display: inline-flex; align-items: center;
    padding: 4px 12px; border-radius: 99px;
    font-size: .75rem; font-weight: 700; letter-spacing: .03em; margin-left: auto;
}
.memo-brief {
    font-size: .9rem; color: #374151; line-height: 1.8;
    background: #f8fafc; border-left: 3px solid #4f46e5;
    padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;
}
.memo-brief p { margin: 0 0 14px; }
.memo-brief p:last-child { margin: 0; }
.list-item {
    display: flex; align-items: flex-start; gap: 8px;
    font-size: .875rem; color: #374151; line-height: 1.55; margin-bottom: 9px;
}
.list-dot-green { color: #16a34a; font-size: 1rem; margin-top: 1px; flex-shrink: 0; }
.list-dot-amber { color: #d97706; font-size: 1rem; margin-top: 1px; flex-shrink: 0; }
.red-flag-card {
    background: #fff5f5; border: 1px solid #fecaca; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px;
}
.red-flag-card .rf-title { font-size: .78rem; font-weight: 700; color: #dc2626; margin-bottom: 4px; }
.red-flag-card .rf-detail { font-size: .84rem; color: #7f1d1d; line-height: 1.55; }
.salary-box {
    background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
    padding: 14px 18px; font-size: .875rem; color: #0c4a6e; line-height: 1.6;
}
.salary-box .sb-lbl { font-size: .68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: #0284c7; margin-bottom: 4px; }
.key-q-box {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
    padding: 14px 18px; font-size: .875rem; color: #78350f;
    font-style: italic; line-height: 1.65;
}
.key-q-box .kq-lbl { font-size: .68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: #d97706; font-style: normal; margin-bottom: 4px; }
.email-box {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 16px 20px; font-size: .83rem; color: #374151;
    white-space: pre-wrap; font-family: inherit; line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)


# ── Shared helpers ────────────────────────────────────────────────────────────

def api_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


@st.cache_resource
def get_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def tier_info(score: int) -> tuple[str, str, str]:
    if score >= 75:
        return "Advance", "#16a34a", "#dcfce7"
    if score >= 50:
        return "Consider", "#d97706", "#fef3c7"
    return "Pass", "#6b7280", "#f3f4f6"


def bar_color(score: int) -> str:
    if score >= 75: return "#16a34a"
    if score >= 50: return "#d97706"
    return "#6b7280"


@st.cache_data
def load_sample_results():
    csv_path = ROOT / "results.csv"
    if not csv_path.exists():
        return []
    from dashboard import load_results
    return load_results(csv_path)


@st.cache_data
def load_sample_jd() -> str:
    p = ROOT / "sample_job.txt"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


@st.cache_data
def load_sample_memos() -> dict:
    import json
    p = ROOT / "sample_memos.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@st.cache_data
def list_resume_files() -> list[Path]:
    d = ROOT / "sample_resumes"
    return sorted(d.glob("*")) if d.exists() else []


# ── Tab: Home ─────────────────────────────────────────────────────────────────

def tab_home():
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;
                  flex-wrap:wrap;gap:28px">
        <div style="flex:1;min-width:260px">
          <h1>HireAI</h1>
          <p class="tagline">AI-powered hiring tools built for small and mid-size businesses.<br>
             Screen faster. Interview smarter. Write better job postings.</p>
          <div>
            <span class="pill">✓ No sign-up required</span>
            <span class="pill">✓ PDF, Word &amp; text</span>
            <span class="pill">✓ Results in 60 seconds</span>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;min-width:230px">
          <div class="hero-stat"><div class="num">60s</div><div class="lbl">to screen 50 resumes</div></div>
          <div class="hero-stat"><div class="num">80%</div><div class="lbl">less screening time</div></div>
          <div class="hero-stat"><div class="num">4</div><div class="lbl">tools, one platform</div></div>
          <div class="hero-stat"><div class="num">$0</div><div class="lbl">to run this demo</div></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("📋", "#4f46e5", "Resume Screener",
         "Score and rank every applicant against your job description in under 60 seconds. Stop reading 50 resumes manually."),
        ("💬", "#7c3aed", "Interview Questions",
         "Generate tailored interview questions from each candidate's actual resume — not a generic template."),
        ("📊", "#2563eb", "Scoring Dashboard",
         "Side-by-side candidate comparison with color-coded tiers. Shareable HTML report for your hiring team."),
        ("🔍", "#0891b2", "JD Analyzer",
         "Grade your job posting on bias, clarity, and appeal — then get a rewritten version ready to post today."),
    ]
    for col, (icon, accent, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(f"""
            <div class="feature-card" style="border-top:4px solid {accent}">
              <div class="fc-icon">{icon}</div>
              <div class="fc-title">{title}</div>
              <div class="fc-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ROI Calculator ────────────────────────────────────────────────────────
    st.markdown("### 💰 ROI Calculator")
    st.caption("Adjust the sliders to match your hiring volume — the table below shows exactly how the savings are calculated.")

    col_sliders, col_result = st.columns([3, 2])
    with col_sliders:
        hires = st.slider("Annual hires", 1, 150, 25, key="roi_hires")
        apps  = st.slider("Average applicants per role", 10, 300, 60, key="roi_apps")
        rate  = st.slider("HR hourly rate ($)", 18, 80, 28, key="roi_rate")

    # Calculation
    mins_manual   = 15           # minutes a person spends reading one resume
    mins_ai       = 3            # minutes reviewing AI-ranked results per resume
    total_resumes = hires * apps
    hours_manual  = round(total_resumes * mins_manual / 60, 1)
    hours_ai      = round(total_resumes * mins_ai / 60, 1)
    hours_saved   = round(hours_manual - hours_ai, 1)
    cost_manual   = int(hours_manual * rate)
    cost_ai       = int(hours_ai * rate)
    dollars_saved = cost_manual - cost_ai

    with col_result:
        st.markdown(f"""
        <div class="roi-result-box">
          <div style="font-size:.72rem;opacity:.72;text-transform:uppercase;
                      letter-spacing:.07em;margin-bottom:8px">Estimated Annual Savings</div>
          <div class="big-num">${dollars_saved:,}</div>
          <div class="sub">{hours_saved:,.0f} hours returned to your team each year</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Calculation breakdown ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**How we calculate this:**")
    st.markdown(f"""
    <table class="roi-breakdown">
      <thead>
        <tr>
          <th class="col-left"></th>
          <th class="col-manual">❌ Without HireAI</th>
          <th class="col-ai">✅ With HireAI</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            Total resumes to screen
            <div style="font-size:.75rem;color:#94a3b8;margin-top:2px">
              {hires} hires × {apps} applicants per role
            </div>
          </td>
          <td class="col-manual">{total_resumes:,} resumes</td>
          <td class="col-ai">{total_resumes:,} resumes</td>
        </tr>
        <tr>
          <td>Time spent per resume</td>
          <td class="col-manual">~{mins_manual} min reading each one</td>
          <td class="col-ai">~{mins_ai} min reviewing rankings ★</td>
        </tr>
        <tr>
          <td>Total screening hours</td>
          <td class="col-manual">{hours_manual:,} hours</td>
          <td class="col-ai">{hours_ai:,} hours</td>
        </tr>
        <tr>
          <td>HR cost at ${rate}/hr</td>
          <td class="col-manual">${cost_manual:,}</td>
          <td class="col-ai">${cost_ai:,}</td>
        </tr>
        <tr>
          <td>Annual savings</td>
          <td class="col-manual">—</td>
          <td class="col-ai">${dollars_saved:,} &nbsp;/&nbsp; {hours_saved:,.0f} hrs</td>
        </tr>
      </tbody>
    </table>
    <div class="roi-note">
      ★ With HireAI, the AI reads and scores every resume automatically.
      You only spend time reviewing the top-ranked candidates and their explanations
      — roughly 3 minutes of review instead of 15 minutes of reading.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("### How it works")
    s1, s2, s3, s4 = st.columns(4)
    for col, num, step, detail in zip(
        [s1, s2, s3, s4], ["1", "2", "3", "4"],
        ["Paste your JD", "Add resumes", "Get ranked results", "Interview smarter"],
        [
            "Upload the job description you're hiring for — paste it in or type it out.",
            "Add resume files in any format: PDF, Word, or plain text. Any number.",
            "Claude scores every applicant 0–100 with a plain-English explanation of each score.",
            "Get tailored interview questions built from each candidate's actual resume.",
        ],
    ):
        with col:
            st.markdown(f"""
            <div class="step-card">
              <div class="step-num">{num}</div>
              <div class="step-title">{step}</div>
              <div class="step-detail">{detail}</div>
            </div>
            """, unsafe_allow_html=True)

    if not api_available():
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("**Demo mode:** pre-loaded sample data is shown in each tab. Set `ANTHROPIC_API_KEY` to run live AI analysis.")


# ── Tab: Resume Screener ──────────────────────────────────────────────────────

def tab_screener():
    st.markdown("## 📋 Resume Screener")
    st.caption("Score and rank applicants against your job description.")

    col_jd, col_resumes = st.columns([1, 1])
    with col_jd:
        jd_text = st.text_area("Job Description", value=load_sample_jd(), height=260,
                               key="screener_jd")
    with col_resumes:
        resume_files = list_resume_files()
        st.markdown(f"**{len(resume_files)} resumes loaded** from `sample_resumes/`")
        for rf in resume_files:
            st.markdown(f"- {rf.stem.replace('_', ' ').title()}")

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        run_live = st.button(
            "Screen Resumes" if api_available() else "Screen Resumes (API key required)",
            type="primary",
            disabled=not api_available(),
            key="run_screener",
        )

    if run_live and api_available():
        from screener import score_resume, load_resume
        client = get_client()
        prog = st.progress(0, text="Starting…")
        live_results = []
        for i, rf in enumerate(resume_files):
            name = rf.stem.replace("_", " ").title()
            prog.progress((i + 1) / len(resume_files), text=f"Screening {name}…")
            try:
                text   = load_resume(rf)
                scored = score_resume(client, jd_text, text, name)
                live_results.append({
                    "rank": 0, "name": name,
                    "score": scored["score"], "explanation": scored["explanation"],
                    "file": str(rf),
                })
            except Exception as exc:
                live_results.append({
                    "rank": 0, "name": name, "score": -1,
                    "explanation": str(exc), "file": str(rf),
                })
        live_results.sort(key=lambda r: r["score"], reverse=True)
        for i, r in enumerate(live_results, 1):
            r["rank"] = i
        st.session_state["live_results"] = live_results
        prog.empty()

    results = st.session_state.get("live_results") or load_sample_results()

    if not results:
        st.info("No results found. Click 'Screen Resumes' to run live screening.")
        return

    if "live_results" not in st.session_state:
        st.caption("Showing pre-loaded sample results. Set `ANTHROPIC_API_KEY` and click the button to run live.")

    st.markdown("---")
    advancing  = sum(1 for r in results if r["score"] >= 75)
    consider   = sum(1 for r in results if 50 <= r["score"] < 75)
    valid      = [r["score"] for r in results if r["score"] >= 0]
    avg        = round(sum(valid) / len(valid)) if valid else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Screened", len(results))
    m2.metric("Advance",        advancing)
    m3.metric("Consider",       consider)
    m4.metric("Avg Score",      f"{avg}/100")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-lbl">All Candidates — Ranked by Fit Score</div>',
                unsafe_allow_html=True)

    for r in results:
        s     = r["score"]
        label, t_col, t_bg = tier_info(s)
        bc    = bar_color(s)
        blurb = r["explanation"][:210] + "…" if len(r["explanation"]) > 210 else r["explanation"]
        st.markdown(f"""
        <div class="cand-card">
          <div style="display:flex;align-items:flex-start;gap:16px">
            <div style="min-width:52px;text-align:center">
              <div style="font-size:1.4rem;font-weight:800;color:{bc}">{s}</div>
              <div style="font-size:.7rem;color:#94a3b8">/100</div>
              <div class="bar-bg">
                <div class="bar-fill" style="width:{max(0,min(100,s))}%;background:{bc}"></div>
              </div>
            </div>
            <div style="flex:1">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
                <span style="font-weight:700;font-size:1rem">#{r['rank']} {r['name']}</span>
                <span class="tier-chip" style="color:{t_col};background:{t_bg}">{label}</span>
              </div>
              <div style="font-size:.875rem;color:#475569;line-height:1.6">{blurb}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


# ── Tab: Interview Questions ──────────────────────────────────────────────────

def tab_interview():
    st.markdown("## 💬 Interview Questions")
    st.caption("Tailored interview questions built from the candidate's actual resume.")

    resume_files = {
        rf.stem.replace("_", " ").title(): rf
        for rf in list_resume_files()
    }
    results   = load_sample_results()
    ranked    = [r["name"] for r in results if r["name"] in resume_files]
    name_list = ranked or list(resume_files.keys())

    col_left, col_right = st.columns([1, 2])

    with col_left:
        candidate = st.selectbox("Candidate", name_list, key="iq_candidate")
        jd_text   = st.text_area("Job Description", value=load_sample_jd(),
                                 height=180, key="iq_jd")

        if st.button("Generate Questions", type="primary",
                     disabled=not api_available(), key="run_iq"):
            from interview_questions import generate_questions, load_text_file
            client = get_client()
            with st.spinner(f"Generating questions for {candidate}…"):
                resume_text = load_text_file(resume_files[candidate])
                data = generate_questions(client, jd_text, resume_text, candidate)
            st.session_state["iq_data"]      = data
            st.session_state["iq_for"]       = candidate

        if not api_available():
            st.caption("Set `ANTHROPIC_API_KEY` to generate live questions.")

        # Show candidate score if available
        match = next((r for r in results if r["name"] == candidate), None)
        if match and match["score"] >= 0:
            s = match["score"]
            label, t_col, t_bg = tier_info(s)
            st.markdown(f"""
            <div style="margin-top:16px;background:white;border:1px solid #e2e8f0;
                        border-radius:10px;padding:14px 16px">
              <div style="font-size:.72rem;color:#94a3b8;text-transform:uppercase;
                          letter-spacing:.05em;margin-bottom:6px">Screening Score</div>
              <div style="font-size:1.6rem;font-weight:800;color:{bar_color(s)}">{s}/100</div>
              <span class="tier-chip" style="color:{t_col};background:{t_bg}">{label}</span>
              <div style="font-size:.8rem;color:#64748b;margin-top:8px;line-height:1.5">
                {match['explanation'][:160]}…
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        data = st.session_state.get("iq_data")
        name = st.session_state.get("iq_for", "")

        if data and name == candidate:
            st.markdown(f"**Interview Guide — {candidate}**")
            st.caption(f"Role: {data['role_title']}")
            for area in data["competency_areas"]:
                questions_html = "".join(
                    f"""<div class="q-item">
                         <div class="q">{i+1}. {q['question']}</div>
                         <div class="rat">&#8594; {q['rationale']}</div>
                       </div>"""
                    for i, q in enumerate(area["questions"])
                )
                st.markdown(f"""
                <div class="q-card">
                  <h4>{area['area']}</h4>
                  {questions_html}
                </div>
                """, unsafe_allow_html=True)

            # Download as text
            lines = [f"INTERVIEW GUIDE — {candidate}", f"Role: {data['role_title']}", ""]
            for area in data["competency_areas"]:
                lines.append(f"[{area['area'].upper()}]")
                for i, q in enumerate(area["questions"], 1):
                    lines.append(f"  {i}. {q['question']}")
                    lines.append(f"     Rationale: {q['rationale']}")
                lines.append("")
            st.download_button(
                "Download Interview Guide",
                data="\n".join(lines).encode("utf-8"),
                file_name=f"interview_{candidate.lower().replace(' ', '_')}.txt",
                mime="text/plain",
            )
        else:
            # Pre-loaded example
            q_path = ROOT / "questions_alice_chen.txt"
            if q_path.exists() and (not name or name != candidate):
                st.caption("Showing pre-loaded example for Alice Chen. Select a candidate and click 'Generate Questions' for live output.")
                st.text(q_path.read_text(encoding="utf-8"))
            else:
                st.info("Select a candidate and click 'Generate Questions'.")


# ── Tab: Scoring Dashboard ────────────────────────────────────────────────────

def tab_dashboard():
    st.markdown("## 📊 Scoring Dashboard")
    st.caption("Shareable HTML comparison report for your hiring team.")

    results = load_sample_results()
    if not results:
        st.warning("No results found. Run the Resume Screener first.")
        return

    jd_title = "Open Role"
    jd_path  = ROOT / "sample_job.txt"
    if jd_path.exists():
        for line in jd_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                jd_title = line.strip()
                break

    from dashboard import generate_html
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                     mode="w", encoding="utf-8") as f:
        tmp = Path(f.name)
    generate_html(results, jd_title, tmp)
    html_content = tmp.read_text(encoding="utf-8")
    tmp.unlink(missing_ok=True)

    st.download_button(
        "⬇ Download HTML Report",
        data=html_content.encode("utf-8"),
        file_name="candidate_dashboard.html",
        mime="text/html",
    )

    st.markdown("---")
    components.html(html_content, height=700, scrolling=True)


# ── Tab: JD Analyzer ─────────────────────────────────────────────────────────

def tab_jd_analyzer():
    st.markdown("## 🔍 JD Analyzer")
    st.caption("Grade your job posting on bias, clarity, inclusivity, and appeal — then get a rewritten version.")

    jd_text = st.text_area("Paste your job description", value=load_sample_jd(),
                           height=260, key="jda_text")

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        run = st.button(
            "Analyze JD" if api_available() else "Analyze JD (API key required)",
            type="primary",
            disabled=not api_available(),
            key="run_jda",
        )

    if run and api_available():
        from analyzer import analyze_jd
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        with st.spinner("Analyzing with Claude Opus…"):
            analysis = analyze_jd(client, jd_text)
        st.session_state["jda_result"] = analysis

    if not api_available():
        st.info("Set `ANTHROPIC_API_KEY` to run the analyzer.")
        return

    a = st.session_state.get("jda_result")
    if not a:
        return

    dims       = ["bias", "clarity", "inclusivity", "appeal"]
    dim_labels = {"bias": "Bias", "clarity": "Clarity",
                  "inclusivity": "Inclusivity", "appeal": "Candidate Appeal"}
    grade      = a.get("overall_grade", "?")
    grade_color = {
        "A": "#16a34a", "B": "#2563eb", "C": "#d97706",
        "D": "#dc2626", "F": "#9f1239",
    }.get(grade, "#6b7280")

    st.markdown("---")

    g_col, s_col = st.columns([1, 3])
    with g_col:
        st.markdown(f"""
        <div style="background:{grade_color};color:white;border-radius:14px;
                    text-align:center;padding:22px 0;font-size:3.5rem;font-weight:800">
          {grade}
        </div>
        <div style="text-align:center;font-size:.75rem;color:#64748b;margin-top:6px">
          Overall Grade
        </div>
        """, unsafe_allow_html=True)
    with s_col:
        avg_s = sum(a[d]["score"] for d in dims) / len(dims)
        st.markdown(f"**{a.get('overall_summary', '')}**")
        st.caption(f"Average score: {avg_s:.1f} / 10")
        if a.get("top_priorities"):
            st.markdown("**Top priorities to fix:**")
            for p in a["top_priorities"]:
                st.markdown(f"- {p}")

    st.markdown("#### Dimension Scores")
    for dim in dims:
        d     = a[dim]
        score = d["score"]
        color = "#16a34a" if score >= 8 else "#d97706" if score >= 5 else "#dc2626"
        pct   = score * 10
        st.markdown(f"""
        <div class="dim-row">
          <div style="font-weight:800;font-size:1.4rem;color:{color};min-width:34px">{score}</div>
          <div style="flex:1;min-width:100px">
            <div style="font-weight:600;font-size:.9rem;margin-bottom:3px">{dim_labels[dim]}</div>
            <div class="bar-bg">
              <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
            </div>
          </div>
          <div style="font-size:.85rem;color:#64748b;flex:2">{d['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Issues & Suggestions")
    for dim in dims:
        d = a[dim]
        if not d.get("issues") and not d.get("suggestions"):
            continue
        with st.expander(f"{dim_labels[dim]}"):
            if d.get("issues"):
                st.markdown("**Issues found**")
                for issue in d["issues"]:
                    st.markdown(f"- {issue}")
            if d.get("suggestions"):
                st.markdown("**Suggestions**")
                for sug in d["suggestions"]:
                    st.markdown(f"- {sug}")
            if d.get("rewrites"):
                st.markdown("**Rewrites**")
                for rw in d["rewrites"]:
                    rc1, rc2 = st.columns(2)
                    rc1.error(f"**Before:** {rw.get('original', '')}")
                    rc2.success(f"**After:** {rw.get('replacement', '')}")

    if a.get("rewritten_jd"):
        st.markdown("#### Suggested Rewrite")
        st.success(a["rewritten_jd"])
        st.download_button(
            "⬇ Download Rewritten JD",
            data=a["rewritten_jd"].encode("utf-8"),
            file_name="improved_job_description.txt",
            mime="text/plain",
        )


# ── Tab: Hiring Memos ─────────────────────────────────────────────────────────

def tab_hiring_memos():
    import html as _html

    def esc(s: str) -> str:
        return _html.escape(str(s))

    def brief_html(text: str) -> str:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]
        return "".join(f"<p>{esc(p)}</p>" for p in paragraphs)

    REC_COLORS = {
        "Strong Advance": ("#dcfce7", "#16a34a"),
        "Advance":        ("#dbeafe", "#1d4ed8"),
        "Consider":       ("#fef3c7", "#d97706"),
        "Pass":           ("#f3f4f6", "#6b7280"),
    }

    st.markdown("## 🗂️ Hiring Memos")
    st.caption(
        "Per-candidate hiring briefs written by a senior recruiter — "
        "strengths, red flags, salary signals, and a head-to-head comparison ready for your leadership meeting."
    )

    results = st.session_state.get("live_results") or load_sample_results()
    if not results:
        st.info("Run the Resume Screener first to generate candidate results.")
        return

    sample_data = load_sample_memos()

    if api_available():
        with st.expander("Generate Live Memos", expanded=False):
            top_n = st.selectbox("Candidates to include", [3, 5, 10], key="memo_top_n",
                                 help="Generates memos for the top N candidates by score")
            if st.button("Generate Hiring Memos", type="primary", key="run_memos"):
                from hiring_memo import generate_candidate_memo, generate_comparative_analysis
                from screener import load_resume
                client = get_client()
                jd_text = load_sample_jd()

                sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)[:top_n]
                prog = st.progress(0, text="Starting…")
                memos: dict = {}
                comp_candidates = []

                for i, r in enumerate(sorted_results):
                    prog.progress((i + 0.5) / (top_n + 1), text=f"Writing memo for {r['name']}…")
                    try:
                        resume_text = load_resume(Path(r["file"]))
                        memo = generate_candidate_memo(
                            client, jd_text, resume_text,
                            r["name"], r["score"], r["explanation"]
                        )
                        memos[r["name"]] = memo
                        comp_candidates.append({
                            "name": r["name"], "score": r["score"],
                            "explanation": r["explanation"], "resume_text": resume_text,
                        })
                    except Exception as exc:
                        st.warning(f"Could not generate memo for {r['name']}: {exc}")

                prog.progress((top_n) / (top_n + 1), text="Writing comparative analysis…")
                try:
                    comparative = generate_comparative_analysis(client, jd_text, comp_candidates[:3])
                    st.session_state["comparative_data"] = comparative
                except Exception as exc:
                    st.warning(f"Comparative analysis failed: {exc}")

                prog.progress(1.0)
                prog.empty()
                st.session_state["memos_data"] = memos
                st.rerun()
    else:
        st.caption("Showing pre-loaded sample memos. Set `ANTHROPIC_API_KEY` to generate live memos.")

    memos_data     = st.session_state.get("memos_data") or sample_data.get("memos", {})
    comparative    = st.session_state.get("comparative_data") or sample_data.get("comparative")

    if not memos_data:
        st.info("No memo data available. Set `ANTHROPIC_API_KEY` and click Generate.")
        return

    # ── Comparative Analysis ──────────────────────────────────────────────────
    if comparative:
        comp_rows_html = "".join(
            f"""<div class="compare-row">
                  <div class="cr-name">{esc(c['name'])}</div>
                  <div><div class="cr-lbl">Unique Value</div>
                       <div class="cr-val">{esc(c['unique_value'])}</div></div>
                  <div><div class="cr-lbl">Biggest Risk</div>
                       <div class="cr-val">{esc(c['biggest_risk'])}</div></div>
                </div>"""
            for c in comparative.get("comparisons", [])
        )
        st.markdown(f"""
        <div class="compare-card">
          <h3>Comparative Analysis — Top Candidates</h3>
          <div style="font-size:.88rem;opacity:.82;line-height:1.65;margin-bottom:16px">
            {esc(comparative.get('executive_summary', ''))}
          </div>
          <h3>Hire Recommendation</h3>
          <div class="hire-rec-box">{esc(comparative.get('hire_recommendation', ''))}</div>
          <h3>Head-to-Head</h3>
          {comp_rows_html}
          <div style="margin-top:14px">
            <h3>Interview Sequence</h3>
            <div class="compare-seq">{esc(comparative.get('interview_sequence', ''))}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Per-Candidate Memos ───────────────────────────────────────────────────
    sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)

    for rank, r in enumerate(sorted_results, 1):
        name = r["name"]
        if name not in memos_data:
            continue

        memo  = memos_data[name]
        score = r["score"]
        rec   = memo.get("recommendation", "Consider")
        bg, fg = REC_COLORS.get(rec, ("#f3f4f6", "#6b7280"))
        _, s_col, _ = tier_info(score)
        bc = bar_color(score)

        strengths = memo.get("strengths", [])
        concerns  = memo.get("concerns", [])
        red_flags = memo.get("red_flags", [])

        strengths_html = "".join(
            f'<div class="list-item"><span class="list-dot-green">●</span>{esc(s)}</div>'
            for s in strengths
        )
        concerns_html = "".join(
            f'<div class="list-item"><span class="list-dot-amber">●</span>{esc(c)}</div>'
            for c in concerns
        ) if concerns else '<div style="font-size:.84rem;color:#94a3b8;font-style:italic">None identified</div>'

        red_flags_html = "".join(
            f"""<div class="red-flag-card">
                  <div class="rf-title">⚠ {esc(f['flag'])}</div>
                  <div class="rf-detail">{esc(f['detail'])}</div>
                </div>"""
            for f in red_flags
        )

        st.markdown(f"""
        <div class="memo-card">
          <div class="memo-header">
            <div class="mh-rank">#{rank}</div>
            <div>
              <div class="mh-name">{esc(name)}</div>
              <div class="mh-score">{score}/100</div>
            </div>
            <span class="rec-badge" style="background:{bg};color:{fg}">{esc(rec)}</span>
          </div>
          <div class="memo-brief">{brief_html(memo.get('hiring_brief', ''))}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
            <div>
              <div class="section-lbl">Strengths</div>
              {strengths_html}
            </div>
            <div>
              <div class="section-lbl">Concerns</div>
              {concerns_html}
            </div>
          </div>
          {'<div class="section-lbl" style="color:#dc2626">Red Flags</div>' + red_flags_html if red_flags else ''}
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:4px">
            <div>
              <div class="salary-box">
                <div class="sb-lbl">Salary Signal</div>
                {esc(memo.get('salary_signal', ''))}
              </div>
            </div>
            <div>
              <div class="key-q-box">
                <div class="kq-lbl">Key Question to Ask</div>
                {esc(memo.get('key_question', ''))}
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Email Drafts — {name}"):
            e1, e2 = st.columns(2)
            with e1:
                st.markdown("**Interview Invite**")
                st.markdown(f'<div class="email-box">{esc(memo.get("interview_invite", ""))}</div>',
                            unsafe_allow_html=True)
                st.download_button(
                    "Copy Invite",
                    data=memo.get("interview_invite", "").encode("utf-8"),
                    file_name=f"invite_{name.lower().replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_invite_{rank}",
                )
            with e2:
                st.markdown("**Rejection Email**")
                st.markdown(f'<div class="email-box">{esc(memo.get("rejection_email", ""))}</div>',
                            unsafe_allow_html=True)
                st.download_button(
                    "Copy Rejection",
                    data=memo.get("rejection_email", "").encode("utf-8"),
                    file_name=f"rejection_{name.lower().replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_reject_{rank}",
                )


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    tabs = st.tabs([
        "🏠 Home",
        "📋 Resume Screener",
        "💬 Interview Questions",
        "📊 Scoring Dashboard",
        "🔍 JD Analyzer",
        "🗂️ Hiring Memos",
    ])
    with tabs[0]: tab_home()
    with tabs[1]: tab_screener()
    with tabs[2]: tab_interview()
    with tabs[3]: tab_dashboard()
    with tabs[4]: tab_jd_analyzer()
    with tabs[5]: tab_hiring_memos()


main()
