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
[data-testid="stAppViewContainer"] { background: #f8fafc; }
[data-testid="stHeader"]           { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }

.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #6d28d9 100%);
    color: white; border-radius: 16px; padding: 48px 44px; margin-bottom: 28px;
}
.hero h1 { font-size: 3rem; font-weight: 800; margin: 0 0 10px; letter-spacing: -1px; }
.hero p  { font-size: 1.1rem; opacity: .88; margin: 0; line-height: 1.6; }

.feature-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 22px; height: 100%;
}
.feature-card .icon { font-size: 1.6rem; margin-bottom: 10px; }
.feature-card h3    { font-size: 1rem; font-weight: 700; margin: 0 0 6px; color: #1e293b; }
.feature-card p     { font-size: .85rem; color: #64748b; margin: 0; line-height: 1.6; }

.roi-box {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 12px; padding: 24px 28px;
}

.cand-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 10px;
}
.bar-bg   { background: #e5e7eb; border-radius: 4px; height: 6px; margin-top: 5px; }
.bar-fill { height: 6px; border-radius: 4px; }
.tier-chip {
    display: inline-block; padding: 2px 9px; border-radius: 99px;
    font-size: .72rem; font-weight: 600;
}

.q-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 20px 24px; margin-bottom: 14px;
}
.q-card h4 {
    color: #4f46e5; font-size: .75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em; margin: 0 0 10px;
}
.q-item        { margin-bottom: 12px; }
.q-item .q     { font-size: .95rem; font-weight: 600; color: #1e293b; margin-bottom: 3px; }
.q-item .rat   { font-size: .82rem; color: #64748b; }

.dim-row {
    background: white; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px; display: flex; align-items: center; gap: 14px;
}
.section-lbl {
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; color: #94a3b8; margin-bottom: 10px;
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
def list_resume_files() -> list[Path]:
    d = ROOT / "sample_resumes"
    return sorted(d.glob("*")) if d.exists() else []


# ── Tab: Home ─────────────────────────────────────────────────────────────────

def tab_home():
    st.markdown("""
    <div class="hero">
      <h1>HireAI</h1>
      <p>AI-powered hiring tools built for small and mid-size businesses.<br>
         Screen faster. Interview smarter. Write better job postings.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in zip(
        [c1, c2, c3, c4],
        ["📋", "💬", "📊", "🔍"],
        ["Resume Screener", "Interview Questions", "Scoring Dashboard", "JD Analyzer"],
        [
            "Score and rank every applicant against your job description in under 60 seconds. Stop reading 50 resumes manually.",
            "Generate tailored interview questions from each candidate's actual resume — not a generic template.",
            "Side-by-side candidate comparison with color-coded tiers. Exportable HTML report for your hiring team.",
            "Grade your job posting on bias, clarity, inclusivity, and appeal — then get a rewritten version ready to post.",
        ],
    ):
        with col:
            st.markdown(f"""
            <div class="feature-card">
              <div class="icon">{icon}</div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ROI Calculator ────────────────────────────────────────────────────────
    st.markdown("### 💰 ROI Calculator")
    st.caption("See how much time and money HireAI saves your team each year.")

    col_sliders, col_result = st.columns([2, 1])
    with col_sliders:
        hires = st.slider("Annual hires", 1, 150, 25)
        apps  = st.slider("Average applicants per role", 10, 300, 60)
        rate  = st.slider("HR hourly rate ($)", 18, 80, 28)

    total_resumes  = hires * apps
    hours_manual   = total_resumes * 0.25      # ~15 min per resume
    hours_with_ai  = total_resumes * 0.05      # ~3 min reviewing ranked list
    hours_saved    = hours_manual - hours_with_ai
    dollars_saved  = int(hours_saved * rate)

    with col_result:
        st.markdown(f"""
        <div class="roi-box">
          <div style="font-size:.72rem;color:#64748b;text-transform:uppercase;
                      letter-spacing:.05em;margin-bottom:10px">Your Annual Numbers</div>
          <div style="font-size:.95rem;margin-bottom:5px">📄 <b>{total_resumes:,}</b> resumes to screen</div>
          <div style="font-size:.95rem;margin-bottom:5px">⏱ <b>{hours_manual:.0f} hrs</b> spent manually</div>
          <div style="font-size:.95rem;margin-bottom:14px">⚡ <b>{hours_with_ai:.0f} hrs</b> with HireAI</div>
          <div style="font-size:1.8rem;font-weight:800;color:#4f46e5">${dollars_saved:,}/yr saved</div>
          <div style="font-size:.78rem;color:#64748b;margin-top:3px">{hours_saved:.0f} hours back to your team</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("### How it works")
    s1, s2, s3, s4 = st.columns(4)
    for col, num, step, detail in zip(
        [s1, s2, s3, s4],
        ["1", "2", "3", "4"],
        ["Upload your JD", "Add resumes", "Get ranked results", "Interview top candidates"],
        [
            "Paste or upload the job description you're hiring for.",
            "Drop in PDF, Word, or text resume files — any format.",
            "Claude scores every candidate 0–100. Ranked list in seconds.",
            "Open tailored interview questions for each candidate you advance.",
        ],
    ):
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:16px 8px">
              <div style="background:#4f46e5;color:white;border-radius:50%;width:36px;height:36px;
                          line-height:36px;font-weight:800;font-size:1.1rem;
                          margin:0 auto 10px">{num}</div>
              <div style="font-weight:700;font-size:.9rem;margin-bottom:5px">{step}</div>
              <div style="font-size:.8rem;color:#64748b;line-height:1.5">{detail}</div>
            </div>
            """, unsafe_allow_html=True)

    if not api_available():
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("**Demo mode:** sample data is pre-loaded in each tab. Set `ANTHROPIC_API_KEY` in your environment to run live AI analysis.")


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


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    tabs = st.tabs([
        "🏠 Home",
        "📋 Resume Screener",
        "💬 Interview Questions",
        "📊 Scoring Dashboard",
        "🔍 JD Analyzer",
    ])
    with tabs[0]: tab_home()
    with tabs[1]: tab_screener()
    with tabs[2]: tab_interview()
    with tabs[3]: tab_dashboard()
    with tabs[4]: tab_jd_analyzer()


main()
