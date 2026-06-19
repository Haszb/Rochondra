import requests
import streamlit as st

from core_shared.config import API_URL


API_WHITEPAPER_URL = f"{API_URL}/whitepaper"
http: requests.Session = st.session_state["http_session"]


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Rochondra")
    st.markdown(
        "<span style='color:#6E6E8A;font-size:0.78rem;'>Whitepaper Analysis Pipeline</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    doc_uuid = st.session_state.get("doc_uuid")
    project = st.session_state.get("current_project", "—")

    if doc_uuid:
        st.markdown(
            f"<div class='session-badge'>● {doc_uuid[:8]}…</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='color:#6E6E8A;font-size:0.8rem;'>Project</span><br>"
            f"<span style='font-size:0.9rem;'>{project}</span>",
            unsafe_allow_html=True,
        )
        st.divider()

        steps = {
            "01 — Extract":   "markdown_content" in st.session_state,
            "02 — Structure": "metrics" in st.session_state,
            "03 — TOC":       "toc" in st.session_state,
            "04 — Semantic":  "analyses" in st.session_state,
        }
        for label, done in steps.items():
            icon = "✦" if done else "·"
            color = "#7DF9C2" if done else "#6E6E8A"
            st.markdown(
                f"<span style='font-family:JetBrains Mono;font-size:0.78rem;color:{color};'>"
                f"{icon} {label}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<span style='color:#6E6E8A;font-size:0.82rem;'>"
            "No document in session.<br>Upload a PDF to begin.</span>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Section 01 — PDF Extraction
# ---------------------------------------------------------------------------

st.markdown(
    "<div class='step-header'>"
    "<span class='step-number'>01</span>"
    "<span class='step-title'>PDF Extraction</span>"
    "</div>",
    unsafe_allow_html=True,
)

col_l, col_r = st.columns([2, 1])
with col_l:
    uploaded_file = st.file_uploader("PDF file", type=["pdf"], label_visibility="collapsed")
with col_r:
    project_name = st.text_input("Project name", placeholder="optional")

col_a, col_b = st.columns(2)
with col_a:
    extract_images = st.toggle("Analyse images", value=True)
with col_b:
    save_markdown = st.toggle("Persist Markdown", value=True)

if uploaded_file and st.button("Run extraction", use_container_width=True):
    with st.spinner("Extracting…"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        data = {
            "extract_images": str(extract_images).lower(),
            "save_markdown": str(save_markdown).lower(),
            "project_name": project_name,
        }
        try:
            response = http.post(f"{API_WHITEPAPER_URL}/extract", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                st.session_state["doc_uuid"] = result.get("doc_uuid")
                st.session_state["current_project"] = project_name or uploaded_file.name
                st.session_state["markdown_content"] = result.get("markdown_content", "")
                st.success("Extraction complete.")
            else:
                st.error(f"Server error {response.status_code} — {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI server unreachable. Make sure it is running on port 8000.")

if "markdown_content" in st.session_state:
    st.text_area("Markdown output", st.session_state["markdown_content"], height=360)


# ---------------------------------------------------------------------------
# Section 02 — Structural Analysis
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "<div class='step-header'>"
    "<span class='step-number'>02</span>"
    "<span class='step-title'>Structural Analysis</span>"
    "</div>",
    unsafe_allow_html=True,
)

include_images_stats = st.toggle("Include image stats", value=False)

if st.button(
    "Run structural analysis",
    disabled=not st.session_state.get("doc_uuid"),
    use_container_width=True,
):
    with st.spinner("Analysing…"):
        try:
            response = http.post(
                f"{API_WHITEPAPER_URL}/structural_analysis",
                data={"include_images_stats": str(include_images_stats).lower()},
            )
            if response.status_code == 200:
                result = response.json()
                st.session_state["metrics"] = result.get("metrics", {})
                st.success("Structural analysis complete.")
            else:
                st.error(f"Server error {response.status_code} — {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI server unreachable.")

if "metrics" in st.session_state:
    metrics = st.session_state["metrics"]
    cols = st.columns(4)
    display = [
        ("Words", metrics.get("word_count", "—")),
        ("Sentences", metrics.get("sentence_count", "—")),
        ("Gunning Fog", metrics.get("gunning_fog_index", "—")),
        ("Flesch", metrics.get("flesch_reading_ease", "—")),
    ]
    for col, (label, val) in zip(cols, display):
        col.metric(label, val)

    with st.expander("Full metrics"):
        st.json(metrics)


# ---------------------------------------------------------------------------
# Section 03 — Table of Contents
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "<div class='step-header'>"
    "<span class='step-number'>03</span>"
    "<span class='step-title'>Table of Contents</span>"
    "</div>",
    unsafe_allow_html=True,
)

if st.button(
    "Extract TOC",
    disabled=not st.session_state.get("doc_uuid"),
    use_container_width=True,
):
    with st.spinner("Extracting TOC…"):
        try:
            response = http.post(f"{API_WHITEPAPER_URL}/toc_extraction")
            if response.status_code == 200:
                result = response.json()
                st.session_state["toc"] = result.get("toc_content", "")
                st.success("TOC extracted.")
            else:
                st.error(f"Server error {response.status_code} — {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI server unreachable.")

if "toc" in st.session_state:
    toc_html = ""
    for line in st.session_state["toc"].splitlines():
        stripped = line.lstrip()
        depth = len(line) - len(stripped)
        css_class = (
            "toc-line-h1" if depth == 0
            else ("toc-line-h2" if depth <= 4 else "toc-line-h3")
        )
        toc_html += f"<div class='toc-line {css_class}'>{stripped}</div>"
    st.markdown(
        f"<div style='padding:16px;background:#16161E;border:1px solid #2A2A3A;border-radius:4px;'>"
        f"{toc_html}</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Section 04 — Semantic Analysis
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "<div class='step-header'>"
    "<span class='step-number'>04</span>"
    "<span class='step-title'>Semantic Analysis</span>"
    "</div>",
    unsafe_allow_html=True,
)

if st.button(
    "Run semantic analysis",
    disabled=not st.session_state.get("doc_uuid"),
    use_container_width=True,
):
    with st.spinner("Running sentiment + summarization — this may take a minute…"):
        try:
            response = http.post(f"{API_WHITEPAPER_URL}/sentiment_analysis")
            if response.status_code == 200:
                result = response.json()
                st.session_state["analyses"] = result.get("analyses", {})
                st.success("Semantic analysis complete.")
            else:
                st.error(f"Server error {response.status_code} — {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("FastAPI server unreachable.")

if "analyses" in st.session_state:
    analyses = st.session_state["analyses"]
    if not analyses:
        st.info("No sections were analysed.")
    else:
        for section_title, analysis in analyses.items():
            sentiment = analysis.get("sentiment", "neutral")
            icon = {
                "positive": ":large_green_circle:",
                "negative": ":red_circle:",
                "neutral": ":white_circle:"
            }.get(sentiment, ":grey_question:")

            with st.expander(f"{icon}  {section_title}", expanded=False):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Words", analysis.get("word_count", 0))
                    st.markdown(
                        f"<span class='sentiment-{sentiment}' style='font-size:0.9rem;font-weight:500;'>"
                        f"{sentiment.capitalize()}</span>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        "<span style='color:#6E6E8A;font-size:0.78rem;'>SCORES</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='score-block'>{analysis.get('score', '')}</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    "<span style='color:#6E6E8A;font-size:0.78rem;margin-top:12px;display:block;'>"
                    "SUMMARY</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<p style='font-size:0.88rem;line-height:1.6;color:#E8E8F0;'>"
                    f"{analysis.get('resume', '')}</p>",
                    unsafe_allow_html=True,
                )