import sys
from pathlib import Path

import requests
import streamlit as st


ROOT_GLOBAL = Path(__file__).resolve().parent.parent
if str(ROOT_GLOBAL) not in sys.path:
    sys.path.insert(0, str(ROOT_GLOBAL))

st.set_page_config(
    page_title="Rochondra Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global theme
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-base:      #0E0E12;
    --bg-surface:   #16161E;
    --bg-raised:    #1E1E2A;
    --border:       #2A2A3A;
    --text-primary: #E8E8F0;
    --text-muted:   #6E6E8A;
    --accent-violet:#B490FF;
    --accent-mint:  #7DF9C2;
    --accent-rose:  #FF6B9D;
    --accent-ice:   #90C8FF;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
}

h1 { font-size: 1.6rem !important; }
h2 {
    font-size: 1.1rem !important;
    color: var(--text-muted) !important;
    font-weight: 400 !important;
}

.step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.step-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent-violet);
    border: 1px solid var(--accent-violet);
    padding: 2px 7px;
    border-radius: 3px;
    letter-spacing: 0.05em;
    opacity: 0.8;
}
.step-title {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
}

[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"] {
    background-color: transparent !important;
    border: 1px solid var(--accent-violet) !important;
    color: var(--accent-violet) !important;
    border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="baseButton-primary"]:hover,
[data-testid="baseButton-secondary"]:hover {
    background-color: var(--accent-violet) !important;
    color: var(--bg-base) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}

[data-testid="stExpander"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}

[data-testid="stMetric"] {
    background-color: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 12px !important;
}
[data-testid="stMetricValue"] {
    color: var(--accent-violet) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

hr { border-color: var(--border) !important; margin: 32px 0 !important; }

.session-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent-mint);
    background-color: rgba(125, 249, 194, 0.08);
    border: 1px solid rgba(125, 249, 194, 0.25);
    padding: 4px 10px;
    border-radius: 3px;
    display: inline-block;
    margin-bottom: 16px;
}

.sentiment-positive { color: var(--accent-mint) !important; }
.sentiment-negative { color: var(--accent-rose) !important; }
.sentiment-neutral  { color: var(--accent-ice)  !important; }

.score-block {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-muted);
    background-color: var(--bg-raised);
    border: 1px solid var(--border);
    padding: 8px 12px;
    border-radius: 4px;
    margin-top: 4px;
}

.toc-line { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; line-height: 1.8; padding: 2px 0; }
.toc-line-h1 { color: var(--accent-violet); }
.toc-line-h2 { color: var(--text-primary); padding-left: 16px; }
.toc-line-h3 { color: var(--text-muted); padding-left: 32px; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Global session state
# ---------------------------------------------------------------------------

if "http_session" not in st.session_state:
    st.session_state["http_session"] = requests.Session()

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

whitepaper_page = st.Page("pages/whitepaper_ui.py", title="Whitepaper Analyst", icon="📄")
# tokenomics_page = st.Page("pages/tokenomics_ui.py", title="Tokenomics Metrics", icon="📊")

pg = st.navigation([whitepaper_page])
pg.run()