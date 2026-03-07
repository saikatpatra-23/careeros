"""
Shared CSS for CareerOS.
Modern warm-neutral SaaS surface tuned for Streamlit.
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Source+Sans+3:wght@400;600;700&display=swap');

:root {
    --bg: #060b16;
    --bg-soft: #0b1324;
    --surface: rgba(14,20,36,0.90);
    --surface-strong: rgba(19,27,46,0.96);
    --surface-dark: #0c1324;
    --line: rgba(148,163,184,0.20);
    --line-strong: rgba(148,163,184,0.30);
    --text: #e6edf7;
    --muted: #a7b4c8;
    --accent: #4f8ef7;
    --accent-soft: rgba(79,142,247,0.18);
    --accent-2: #2db8a0;
    --success: #2db86d;
    --warning: #f0b24d;
    --shadow: 0 24px 50px rgba(0,0,0,0.38);
    --radius-xl: 28px;
    --radius-lg: 20px;
    --radius-md: 14px;
}

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif !important;
    color: var(--text);
}
body, .stApp {
    background:
        radial-gradient(circle at top left, rgba(79,142,247,0.20), transparent 30%),
        radial-gradient(circle at top right, rgba(45,184,160,0.14), transparent 26%),
        linear-gradient(180deg, #050a14 0%, #091224 48%, #0b1327 100%);
}
#MainMenu, footer { visibility: hidden; }

h1, h2, h3, h4, .pg-name, .co-hero-title, .co-section-title {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.03em;
}

section.main > div {
    padding-top: 1.4rem;
}

.block-container {
    max-width: 1180px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #182028 0%, #1e2832 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] * {
    color: #eef3f6 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    border-radius: 14px;
    margin-bottom: 4px;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.08) !important;
}

.pg-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}
.pg-icon {
    width: 40px;
    height: 40px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: rgba(79,142,247,0.18);
    box-shadow: var(--shadow);
    font-size: 1.1rem;
}
.pg-name { font-size: 1.35rem; font-weight: 700; color: var(--text); }
.pg-sub  { font-size: 0.95rem; color: var(--muted); }

.co-hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, rgba(18,26,44,0.96), rgba(12,19,34,0.96));
    border: 1px solid rgba(148,163,184,0.20);
    border-radius: var(--radius-xl);
    padding: 26px 28px;
    box-shadow: var(--shadow);
    margin-bottom: 20px;
}
.co-hero::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    border-radius: 999px;
    right: -80px;
    top: -80px;
    background: radial-gradient(circle, rgba(79,142,247,0.25), transparent 70%);
}
.co-hero-badge {
    display: inline-flex;
    gap: 8px;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.co-hero-title {
    font-size: 2.15rem;
    line-height: 1;
    margin: 16px 0 10px 0;
    color: var(--text);
}
.co-hero-copy {
    max-width: 760px;
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.65;
}
.co-inline-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}
.co-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 12px;
    border-radius: 999px;
    background: rgba(148,163,184,0.14);
    border: 1px solid rgba(148,163,184,0.24);
    color: var(--text);
    font-size: 0.9rem;
}

.co-section-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin: 14px 0 10px 0;
    color: var(--text);
}
.co-section-kicker {
    color: var(--muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    margin-bottom: 8px;
}

.co-card, [data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: var(--radius-lg);
    padding: 18px 20px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(10px);
}
.co-card.tight { padding: 14px 16px; }
.co-card h4, .co-card h5 { margin: 0 0 8px 0; }
.co-card p, .co-muted { color: var(--muted); }

.co-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(148,163,184,0.16);
    color: var(--muted);
    border: 1px solid rgba(24,32,40,0.08);
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 700;
    padding: 5px 10px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.co-badge.done { background: rgba(31,143,99,0.10); color: var(--success); border-color: rgba(31,143,99,0.18); }
.co-badge.soon { background: rgba(183,121,31,0.10); color: var(--warning); border-color: rgba(183,121,31,0.18); }
.co-badge.live { background: var(--accent-soft); color: var(--accent); border-color: rgba(239,108,47,0.18); }

.co-checklist {
    display: grid;
    gap: 8px;
}
.co-check {
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(148,163,184,0.12);
    border: 1px solid rgba(148,163,184,0.18);
    font-size: 0.92rem;
}

.co-info, .co-tip, div[data-testid="stAlert"] {
    border-radius: 14px !important;
}
.co-info {
    background: rgba(45,184,160,0.16);
    border-left: 3px solid var(--accent-2);
    color: #b9f3e8;
    padding: 12px 14px;
    line-height: 1.6;
}
.co-tip {
    background: rgba(79,142,247,0.16);
    border-left: 3px solid var(--accent);
    color: #c9dcff;
    padding: 12px 14px;
    line-height: 1.6;
}

.co-upload-shell {
    border: 1.5px dashed rgba(148,163,184,0.36);
    border-radius: 22px;
    background: linear-gradient(180deg, rgba(14,20,36,0.86), rgba(14,20,36,0.74));
    padding: 18px;
}

[data-testid="stFileUploaderDropzone"] {
    padding: 18px !important;
    min-height: 110px !important;
    background: transparent !important;
    border: 0 !important;
}

[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #ef6c2f, #ff915c) !important;
    color: white !important;
    border: 0 !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    box-shadow: 0 12px 24px rgba(239,108,47,0.20) !important;
}
[data-testid="baseButton-secondary"] {
    background: rgba(148,163,184,0.12) !important;
    color: var(--text) !important;
    border: 1px solid rgba(148,163,184,0.26) !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
}
[data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
    min-height: 2.85rem !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="baseButton-primary"]:hover, [data-testid="baseButton-secondary"]:hover {
    transform: translateY(-1px);
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    border-radius: 14px !important;
    border: 1px solid rgba(148,163,184,0.30) !important;
    background: rgba(10,16,30,0.92) !important;
    color: var(--text) !important;
}
.stTextArea textarea {
    min-height: 120px;
}
.stTextArea textarea:disabled {
    background: rgba(11,18,33,0.95) !important;
    color: var(--text) !important;
    opacity: 1 !important;
    line-height: 1.65 !important;
}

[data-testid="stTabs"] [data-testid="stTabList"] {
    gap: 8px;
}
[data-testid="stTabs"] [data-testid="stTab"] {
    border-radius: 999px !important;
    padding: 10px 16px !important;
    background: rgba(148,163,184,0.10) !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(239,108,47,0.10) !important;
    color: var(--accent) !important;
    border-color: rgba(239,108,47,0.18) !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(148,163,184,0.20) !important;
    border-radius: 18px !important;
    overflow: hidden !important;
    background: rgba(13,20,36,0.90) !important;
}

hr { border-color: rgba(148,163,184,0.24) !important; margin: 18px 0 !important; }

@media (max-width: 768px) {
    .co-hero { padding: 22px 18px; }
    .co-hero-title { font-size: 1.75rem; }
    .pg-title { align-items: flex-start; }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
