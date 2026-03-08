"""
Shared UI stylesheet for CareerOS.
Dark, high-contrast SaaS shell inspired by modern productivity apps.
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #121420;
    --bg-2: #151826;
    --surface: #1b1f2f;
    --surface-2: #1f2434;
    --line: #2b3040;
    --text: #edf1fb;
    --muted: #8f9ab0;
    --blue: #3d63f5;
    --blue-2: #3156d4;
    --good: #22c55e;
    --warn: #f59e0b;
    --bad: #ef4444;
    --radius-xl: 18px;
    --radius-lg: 12px;
    --radius-md: 10px;
    --shadow: 0 1px 3px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.25);
}

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--text);
}
body, .stApp {
    background:
        radial-gradient(circle at 86% 12%, rgba(61,99,245,0.16), transparent 26%),
        linear-gradient(180deg, #0d1018 0%, #0c0f17 100%);
}
#MainMenu, footer { visibility: hidden; }

.block-container {
    max-width: 1220px;
    padding-top: 1.1rem;
    padding-bottom: 2.4rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1018 0%, #0b0e15 100%) !important;
    border-right: 1px solid #232938 !important;
}
section[data-testid="stSidebar"] * { color: #cfd8ed !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    margin-bottom: 6px;
    border-radius: 16px;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
    padding-left: 12px !important;
    border: 1px solid transparent;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: #181d2a !important;
    border-color: #2a3248;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #141f3e !important;
    border-color: #294bbb;
    color: #e3ebff !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="api_ingest"] {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a::before {
    width: 18px;
    text-align: center;
    opacity: 0.95;
    font-size: 0.95rem;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="app"]::before,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="/app"]::before {
    content: "⌂";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="0_Setup"]::before {
    content: "⚙";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="1_Resume_Builder"]::before {
    content: "◫";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="2_Profile_Optimizer"]::before {
    content: "◉";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="3_Role_Clarity"]::before {
    content: "✦";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="4_ATS_Checker"]::before {
    content: "◎";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="5_Smart_Apply"]::before {
    content: "➤";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="6_Cover_Letter"]::before {
    content: "✉";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="7_Admin_Analytics"]::before {
    content: "⚑";
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="8_Run_History"]::before {
    content: "◷";
}

/* Sidebar icons override with Unicode escapes (prevents encoding issues) */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href$="app"]::before,
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="/app"]::before { content: "\\2302" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="0_Setup"]::before { content: "\\2699" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="1_Resume_Builder"]::before { content: "\\25EB" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="2_Profile_Optimizer"]::before { content: "\\25C9" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="3_Role_Clarity"]::before { content: "\\2726" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="4_ATS_Checker"]::before { content: "\\25CE" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="5_Smart_Apply"]::before { content: "\\27A4" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="6_Cover_Letter"]::before { content: "\\2709" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="7_Admin_Analytics"]::before { content: "\\2691" !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="8_Run_History"]::before { content: "\\25F7" !important; }

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
    background: linear-gradient(145deg, #1b1f2f 0%, #161a28 100%);
    padding: 22px 24px;
    box-shadow: var(--shadow);
}
.co-hero {
    border: 1px solid var(--line);
    border-radius: var(--radius-xl);
    background: linear-gradient(125deg, rgba(22,27,39,0.95), rgba(14,20,32,0.95));
    padding: 22px 24px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
}
.co-hero-badge {
    display: inline-flex;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #d8e4ff;
    background: #17274a;
    border: 1px solid #29478f;
}
.co-hero-title {
    margin-top: 10px;
    font-size: 1.75rem;
    line-height: 1.2;
    font-weight: 800;
}
.co-hero-copy {
    margin-top: 8px;
    color: var(--muted);
    font-size: 0.98rem;
    line-height: 1.7;
}
.co-inline-stats {
    margin-top: 12px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.co-section-kicker {
    color: #8ca3d8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 4px;
}
.co-section-title {
    margin: 5px 0 14px 0;
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.2;
}
.co-badge {
    display: inline-flex;
    align-items: center;
    padding: 5px 10px;
    border-radius: 999px;
    background: #273149;
    color: #d5e1fa;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
}
.co-badge.live { background: #103b30; color: #96f0c2; }
.co-badge.done { background: #152f5f; color: #bcd2ff; }
.co-badge.soon { background: #3b2b12; color: #f8d392; }
.co-checklist {
    margin-top: 8px;
    display: grid;
    gap: 8px;
}
.co-check {
    padding: 10px 12px;
    border-radius: 10px;
    background: #101726;
    border: 1px solid #263147;
    color: #c9d6f4;
    font-size: 0.9rem;
}
.co-info {
    padding: 11px 13px;
    border-radius: 10px;
    background: rgba(60,109,240,0.14);
    border: 1px solid rgba(60,109,240,0.4);
    color: #bdd0ff;
    font-size: 0.88rem;
}
.co-tip {
    margin-top: 10px;
    padding: 11px 13px;
    border-radius: 10px;
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.35);
    color: #ffd89d;
    font-size: 0.86rem;
}
.co-upload-shell {
    border: 1px dashed #2f3b56;
    border-radius: var(--radius-lg);
    padding: 16px 18px;
    background: #111827;
}
.co-empty-state {
    border: 1px dashed #2f3b56;
    border-radius: var(--radius-lg);
    padding: 18px 20px;
    text-align: center;
    color: var(--muted);
    background: #111827;
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
    background: #171b29 !important;
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
