"""
CareerOS global stylesheet — matches careeros-resume.lovable.app design system exactly.
Dark SaaS shell: near-black bg, surface cards, blue primary, Inter font.
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ═══════════════════════════════════════════════
   COLOR TOKENS  (lovable.app exact values)
   ─────────────────────────────────────────────
   bg:      rgb(18,19,23)   = #121317
   surface: rgb(27,28,34)   = #1b1c22
   line:    rgb(41,43,50)   = #292b32
   primary: rgb(53,98,233)  = #3562e9
   text:    rgb(240,242,245)= #f0f2f5
   muted:   rgb(126,138,154)= #7e8a9a
═══════════════════════════════════════════════ */
:root {
    --bg:          #121317;
    --bg-2:        #16171d;
    --surface:     #1b1c22;
    --surface-2:   #1f2028;
    --line:        #292b32;
    --line-2:      #2e3038;
    --text:        #f0f2f5;
    --muted:       #7e8a9a;
    --primary:     #3562e9;
    --primary-h:   #2d56d4;
    --primary-dim: rgba(53,98,233,0.15);
    --primary-bdr: rgba(53,98,233,0.35);
    --good:        #22c55e;
    --good-dim:    rgba(34,197,94,0.15);
    --warn:        #f59e0b;
    --warn-dim:    rgba(245,158,11,0.12);
    --bad:         #ef4444;
    --r:           12px;
    --r-sm:        10px;
    --shadow:      rgba(0,0,0,0.3) 0px 1px 3px 0px, rgba(0,0,0,0.3) 0px 1px 2px -1px;
}

/* ─── BASE ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--text);
}
body, .stApp {
    background: var(--bg) !important;
}
#MainMenu, footer { visibility: hidden; }

.block-container {
    max-width: 1220px;
    padding-top: 1.1rem;
    padding-bottom: 2.4rem;
}

/* ─── SIDEBAR ───────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg) !important;
    border-right: 1px solid var(--line) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background: var(--bg) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--muted) !important;
}
/* Hide default streamlit auto-nav */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none !important;
}
/* icon/emoji elements from page_link */
section[data-testid="stSidebar"] [data-testid="stIconEmoji"],
section[data-testid="stSidebar"] [data-testid="stPageLinkIcon"] {
    display: none !important;
}

/* Nav links — both selector variants */
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
    border-radius: var(--r-sm) !important;
    padding: 10px 12px !important;
    margin-bottom: 2px !important;
    border: 1px solid transparent !important;
    color: var(--muted) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    transition: background 0.12s ease, color 0.12s ease;
    text-decoration: none !important;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover,
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
    background: var(--surface) !important;
    border-color: var(--line) !important;
    color: var(--text) !important;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"],
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: var(--primary-dim) !important;
    border-color: var(--primary-bdr) !important;
    color: #a8c0ff !important;
}

/* SVG icon pseudoelement */
section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]::before,
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]::before {
    content: "";
    width: 16px; height: 16px; min-width: 16px;
    display: inline-block;
    background-size: 16px; background-repeat: no-repeat; background-position: center;
}
section[data-testid="stSidebar"] a[href*="app.py"]::before,
section[data-testid="stSidebar"] a[href$="/app"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' width='7' height='7' rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' rx='1'/></svg>");
}
section[data-testid="stSidebar"] a[href*="0_Setup"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 5 15.4a1.65 1.65 0 0 0-1.51-1H3.4a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 5 8.9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9.32 4h.36A1.65 1.65 0 0 0 11 2.49V2.4a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 16.51 4h.36a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 21 8.6v.36A1.65 1.65 0 0 0 22.51 10h.09a2 2 0 1 1 0 4h-.09A1.65 1.65 0 0 0 21 15.51z'/></svg>");
}
section[data-testid="stSidebar"] a[href*="1_Resume_Builder"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/></svg>");
}
section[data-testid="stSidebar"] a[href*="2_Profile_Optimizer"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M20 21a8 8 0 0 0-16 0'/><circle cx='12' cy='7' r='4'/><polyline points='16 11 18 13 22 9'/></svg>");
}
section[data-testid="stSidebar"] a[href*="3_Role_Clarity"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'/><polygon points='16 8 14 14 8 16 10 10 16 8'/></svg>");
}
section[data-testid="stSidebar"] a[href*="4_ATS_Checker"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='3 7 3 3 7 3'/><polyline points='17 3 21 3 21 7'/><polyline points='21 17 21 21 17 21'/><polyline points='7 21 3 21 3 17'/><circle cx='12' cy='12' r='3'/></svg>");
}
section[data-testid="stSidebar"] a[href*="5_Smart_Apply"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 13a8 8 0 0 1 8-8h2'/><path d='M14 3l7 7-4 1-2 4-7-7z'/><path d='M5 21a3 3 0 0 1 0-6h1'/></svg>");
}
section[data-testid="stSidebar"] a[href*="6_Cover_Letter"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='5' width='18' height='14' rx='2'/><polyline points='3 7 12 13 21 7'/></svg>");
}
section[data-testid="stSidebar"] a[href*="8_Run_History"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='1 4 1 10 7 10'/><path d='M3.5 15a9 9 0 1 0 .4-8'/><polyline points='12 7 12 12 15 15'/></svg>");
}
section[data-testid="stSidebar"] a[href*="7_Admin_Analytics"]::before {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237e8a9a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/></svg>");
}

/* ─── TOPBAR (custom HTML element) ─────────── */
.co-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 18px;
    border: 1px solid var(--line);
    border-radius: var(--r);
    background: var(--surface);
    margin-bottom: 20px;
    box-shadow: var(--shadow);
}
.co-topbar-title {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: var(--text);
}
.co-topbar-user {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: var(--muted);
    font-size: 0.88rem;
}
.co-avatar {
    width: 32px; height: 32px;
    border-radius: 999px;
    background: rgba(53,98,233,0.2);
    color: #a8c0ff;
    font-weight: 700;
    font-size: 0.8rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

/* ─── PAGE TITLE ────────────────────────────── */
.pg-title { margin: 0 0 20px 0; }
.pg-name {
    font-size: 1.875rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.01em;
    line-height: 1.2;
}
.pg-sub {
    margin-top: 4px;
    color: var(--muted);
    font-size: 0.875rem;
    line-height: 1.5;
}

/* ─── STAT CARDS (dashboard 3×2) ────────────── */
.lov-stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 14px;
}
.lov-stat {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 20px;
    box-shadow: var(--shadow);
}
.lov-stat-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}
.lov-stat-label {
    color: var(--muted);
    font-size: 0.8rem;
    font-weight: 500;
}
.lov-stat-icon {
    font-size: 1rem;
    opacity: 0.7;
}
.lov-stat-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.1;
}
.lov-stat-value.good { color: var(--good); }
.lov-stat-value.primary { color: #a8c0ff; }

/* ─── SECTION CARDS ─────────────────────────── */
.lov-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 24px;
    box-shadow: var(--shadow);
    margin-bottom: 14px;
}
.lov-card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 16px;
}

/* ─── PROGRESS BARS ─────────────────────────── */
.lov-progress { margin-bottom: 14px; }
.lov-progress:last-child { margin-bottom: 0; }
.lov-progress-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.82rem;
    margin-bottom: 7px;
}
.lov-progress-label { color: var(--muted); }
.lov-progress-val { color: var(--text); font-weight: 500; }
.lov-progress-track {
    width: 100%;
    height: 6px;
    background: var(--surface-2);
    border-radius: 999px;
    overflow: hidden;
}
.lov-progress-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 999px;
    transition: width 0.3s ease;
}

/* ─── QUICK ACTIONS ─────────────────────────── */
.lov-qa-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}
.lov-qa-btn {
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 16px 12px;
    text-align: center;
    cursor: pointer;
    color: var(--text);
    font-weight: 600;
    font-size: 0.85rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    min-height: 80px;
    justify-content: center;
    transition: background 0.15s, border-color 0.15s;
}
.lov-qa-btn:hover {
    background: var(--surface);
    border-color: var(--line-2);
}
.lov-qa-icon { font-size: 1.3rem; opacity: 0.85; }

/* ─── SHARED COMPONENT CLASSES ──────────────── */
.co-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 20px 24px;
    box-shadow: var(--shadow);
    margin-bottom: 14px;
}
.co-muted { color: var(--muted); }

.co-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--primary-dim);
    color: #a8c0ff;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 10px;
}
.co-badge.live   { background: var(--good-dim); color: #86efac; }
.co-badge.warn   { background: var(--warn-dim); color: #fcd34d; }
.co-badge.done   { background: var(--primary-dim); color: #93c5fd; }
.co-badge.soon   { background: rgba(245,158,11,0.12); color: #fde68a; }

.co-info {
    padding: 11px 13px;
    border-radius: var(--r-sm);
    background: rgba(53,98,233,0.1);
    border: 1px solid rgba(53,98,233,0.3);
    color: #a8c0ff;
    font-size: 0.875rem;
    line-height: 1.5;
}
.co-tip {
    margin-top: 10px;
    padding: 11px 13px;
    border-radius: var(--r-sm);
    background: var(--warn-dim);
    border: 1px solid rgba(245,158,11,0.3);
    color: #fcd34d;
    font-size: 0.875rem;
    line-height: 1.5;
}
.co-hero {
    border: 1px solid var(--line);
    border-radius: var(--r);
    background: var(--surface);
    padding: 28px 28px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
}
.co-hero-badge {
    display: inline-flex;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #a8c0ff;
    background: var(--primary-dim);
}
.co-hero-title {
    margin-top: 10px;
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.25;
    color: var(--text);
}
.co-hero-copy {
    margin-top: 8px;
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.65;
}
.co-inline-stats {
    margin-top: 12px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.co-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    background: var(--surface-2);
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 500;
}
.co-empty-state {
    border: 1px dashed var(--line-2);
    border-radius: var(--r);
    padding: 24px;
    text-align: center;
    color: var(--muted);
    background: var(--bg-2);
}
.co-upload-shell {
    border: 1px dashed var(--line-2);
    border-radius: var(--r);
    padding: 16px 18px;
    background: var(--bg-2);
}

/* section headings used across pages */
.co-panel-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
}
.co-section-kicker {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 600;
}

/* Progress (shared, older pages) */
.co-progress-row { margin-top: 14px; }
.co-progress-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    margin-bottom: 7px;
}
.co-progress-track {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: var(--surface-2);
    overflow: hidden;
}
.co-progress-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 999px;
}

/* External job cards (Smart Apply) */
.ext-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
}
.score-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.8rem;
}
.score-green  { background: rgba(34,197,94,0.15);  color: #86efac; }
.score-amber  { background: rgba(245,158,11,0.15); color: #fcd34d; }
.score-orange { background: rgba(239,68,68,0.12);  color: #fca5a5; }

/* ─── STREAMLIT NATIVE OVERRIDES ────────────── */
[data-testid="baseButton-primary"] {
    background: var(--primary) !important;
    border: 0 !important;
    color: #fff !important;
    border-radius: var(--r-sm) !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-primary"]:hover {
    background: var(--primary-h) !important;
}
[data-testid="baseButton-secondary"] {
    background: var(--bg) !important;
    border: 1px solid var(--line) !important;
    color: var(--text) !important;
    border-radius: var(--r-sm) !important;
    font-weight: 500 !important;
}
[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"] {
    min-height: 2.4rem !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background: var(--bg) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--r-sm) !important;
    color: var(--text) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder { color: var(--muted) !important; }

[data-testid="stTabs"] [data-testid="stTabList"] { gap: 6px; }
[data-testid="stTabs"] [data-testid="stTab"] {
    border-radius: var(--r-sm) !important;
    padding: 8px 16px !important;
    border: 1px solid var(--line) !important;
    background: var(--bg) !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--primary-dim) !important;
    border-color: var(--primary-bdr) !important;
    color: #a8c0ff !important;
}

/* Streamlit container borders */
[data-testid="stVerticalBlock"] > [data-testid="element-container"] > div[style*="border"] {
    border-color: var(--line) !important;
    border-radius: var(--r) !important;
    background: var(--surface) !important;
}

/* Chat (Resume Builder) */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--r) !important;
}

/* Alerts/infos */
[data-testid="stAlert"] {
    border-radius: var(--r-sm) !important;
}

hr { border-color: var(--line) !important; opacity: 1 !important; }

/* ─── LEGACY CLASSES (used by existing pages) ── */
.co-section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
    margin: 2px 0 14px 0;
    line-height: 1.3;
}
.co-grid-2 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 14px;
}
.co-metric {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r);
    padding: 20px 24px;
    box-shadow: var(--shadow);
}
.co-metric-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 8px; }
.co-metric-value { font-size: 2rem; font-weight: 700; color: var(--text); line-height: 1; }
.co-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.co-action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 80px;
    border: 1px solid var(--line);
    border-radius: var(--r);
    background: var(--bg-2);
    color: var(--text);
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.15s;
}
.co-action-btn:hover { background: var(--surface); }
.co-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 999px;
    background: var(--surface-2);
    border: 1px solid var(--line);
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 500;
}
.co-checklist { display: grid; gap: 8px; margin-top: 8px; }
.co-check {
    padding: 10px 12px;
    border-radius: var(--r-sm);
    background: var(--bg-2);
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: 0.875rem;
}
.co-section-kicker {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 600;
}

/* ─── RESPONSIVE ────────────────────────────── */
@media (max-width: 900px) {
    .pg-name { font-size: 1.5rem; }
    .lov-stats-grid { grid-template-columns: repeat(2, 1fr); }
    .lov-qa-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
    .lov-stats-grid { grid-template-columns: 1fr; }
    .lov-qa-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
