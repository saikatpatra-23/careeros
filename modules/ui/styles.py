"""
Shared UI stylesheet for CareerOS.
Dark, high-contrast SaaS shell inspired by modern productivity apps.
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --bg: #090b12;
    --bg-2: #0d111b;
    --surface: #161b27;
    --surface-2: #1b2130;
    --line: #2b3345;
    --text: #f1f5ff;
    --muted: #9aa8c3;
    --blue: #3c6df0;
    --blue-2: #2a57d9;
    --good: #22c55e;
    --warn: #f59e0b;
    --bad: #ef4444;
    --radius-xl: 22px;
    --radius-lg: 16px;
    --radius-md: 12px;
    --shadow: 0 18px 35px rgba(0,0,0,0.35);
}

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif !important;
    color: var(--text);
}
body, .stApp {
    background:
        radial-gradient(circle at 86% 12%, rgba(60,109,240,0.22), transparent 26%),
        linear-gradient(180deg, #06080f 0%, #090d17 100%);
}
#MainMenu, footer { visibility: hidden; }

.block-container {
    max-width: 1220px;
    padding-top: 1.1rem;
    padding-bottom: 2.4rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0d14 0%, #0d111b 100%) !important;
    border-right: 1px solid #1f2636 !important;
}
section[data-testid="stSidebar"] * { color: #d9e2f3 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    margin-bottom: 6px;
    border-radius: 16px;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
    border: 1px solid transparent;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: #151c2b !important;
    border-color: #243049;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #102043 !important;
    border-color: #1f3f8f;
    color: #dbe7ff !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="api_ingest"] {
    display: none !important;
}

.co-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 18px;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: rgba(17,22,34,0.9);
    margin-bottom: 16px;
}
.co-topbar-title {
    font-size: 1.02rem;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.co-topbar-user {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: var(--muted);
    font-size: 0.92rem;
}
.co-avatar {
    width: 34px;
    height: 34px;
    border-radius: 999px;
    background: #1c2a47;
    color: #c3d4ff;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.pg-title { margin: 8px 0 18px 0; }
.pg-name {
    font-size: 3rem;
    line-height: 1;
    font-weight: 800;
    letter-spacing: -0.02em;
}
.pg-sub {
    margin-top: 8px;
    color: var(--muted);
    font-size: 1.05rem;
}

.co-grid-2 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}
.co-metric {
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: linear-gradient(180deg, #171d2b 0%, #141a27 100%);
    padding: 22px 24px;
    box-shadow: var(--shadow);
}
.co-metric-label { color: var(--muted); font-size: 0.95rem; margin-bottom: 12px; }
.co-metric-value { font-size: 2.8rem; line-height: 1; font-weight: 800; }

.co-card {
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: linear-gradient(180deg, #171d2b 0%, #141a27 100%);
    padding: 22px 24px;
    box-shadow: var(--shadow);
}
.co-card h3 {
    margin: 0 0 8px 0;
    font-size: 1.95rem;
    font-weight: 800;
}
.co-muted { color: var(--muted); }

.co-progress-row { margin-top: 14px; }
.co-progress-head {
    display: flex;
    justify-content: space-between;
    font-size: 1.02rem;
    margin-bottom: 8px;
}
.co-progress-track {
    width: 100%;
    height: 12px;
    border-radius: 999px;
    background: #242c3e;
    overflow: hidden;
}
.co-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--blue), #4d79f6);
}

.co-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.co-action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 82px;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: #111725;
    color: #dce7ff;
    font-weight: 700;
}

.co-panel-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    font-size: 2rem;
    font-weight: 800;
}
.co-chip {
    display: inline-flex;
    align-items: center;
    padding: 7px 10px;
    border-radius: 999px;
    background: #20283a;
    color: #d4def5;
    font-size: 0.88rem;
}

[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--blue), var(--blue-2)) !important;
    border: 0 !important;
    color: #f5f8ff !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
[data-testid="baseButton-secondary"] {
    background: #131a28 !important;
    border: 1px solid var(--line) !important;
    color: #dbe5fb !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
[data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
    min-height: 2.8rem !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background: #0f1522 !important;
    border: 1px solid #2b3345 !important;
    border-radius: 12px !important;
    color: #e9efff !important;
}

[data-testid="stTabs"] [data-testid="stTabList"] { gap: 8px; }
[data-testid="stTabs"] [data-testid="stTab"] {
    border-radius: 12px !important;
    padding: 10px 16px !important;
    border: 1px solid var(--line) !important;
    background: #151b2a !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #101f45 !important;
    border-color: #2b56c2 !important;
    color: #e2ebff !important;
}

hr { border-color: #232c3f !important; }

@media (max-width: 900px) {
    .pg-name { font-size: 2.2rem; }
    .co-grid-2, .co-actions { grid-template-columns: 1fr; }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
