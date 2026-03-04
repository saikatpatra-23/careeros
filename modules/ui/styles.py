# -*- coding: utf-8 -*-
"""
Shared CSS for CareerOS — mobile-first responsive design.
Import and call inject_global_css() at the top of each page.
"""
import streamlit as st


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Reset & Base ──────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Hide Streamlit branding on mobile too */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* ── Page header card (used in all sub-pages) ─────────────────────────── */
.page-header {
    border-radius: 14px;
    padding: 22px 26px;
    color: white;
    margin-bottom: 20px;
}
.page-header h2 { margin: 0 0 4px 0; font-size: 1.5rem; font-weight: 700; }
.page-header p  { margin: 0; opacity: 0.88; font-size: 0.9rem; }

/* ── Card component ───────────────────────────────────────────────────── */
.co-card {
    background: white;
    border-radius: 14px;
    padding: 20px 22px;
    border: 1.5px solid #E2E8F0;
    height: 100%;
}
.co-card:hover { box-shadow: 0 4px 18px rgba(27,79,156,0.08); }

/* ── Badge ────────────────────────────────────────────────────────────── */
.co-badge {
    display: inline-block;
    background: #EBF3FB;
    color: #1B4F9C;
    border-radius: 8px;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    margin-bottom: 8px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.co-badge.done   { background: #D1FAE5; color: #065F46; }
.co-badge.locked { background: #F3F4F6; color: #9CA3AF; }

/* ── Progress bar ─────────────────────────────────────────────────────── */
.co-prog-wrap {
    background: #E2E8F0;
    border-radius: 100px;
    height: 6px;
    margin: 14px 0 6px 0;
    overflow: hidden;
}
.co-prog-fill {
    height: 6px;
    border-radius: 100px;
    background: linear-gradient(90deg, #1B4F9C, #3B82F6);
}

/* ── Info / tip banner ────────────────────────────────────────────────── */
.co-tip {
    background: linear-gradient(135deg, #FFF7ED, #FEF3C7);
    border-radius: 12px;
    padding: 14px 18px;
    border-left: 4px solid #F59E0B;
    font-size: 0.875rem;
    color: #78350F;
    line-height: 1.6;
}
.co-info {
    background: #EBF3FB;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.875rem;
    color: #1B4F9C;
    border-left: 4px solid #1B4F9C;
    margin: 8px 0;
}

/* ── Upload zone styling ──────────────────────────────────────────────── */
.upload-zone {
    border: 2px dashed #CBD5E1;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    background: #F8FAFC;
    margin: 10px 0;
}

/* ── Mobile responsive ────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .page-header { padding: 16px 18px; }
    .page-header h2 { font-size: 1.25rem; }
    .page-header p  { font-size: 0.82rem; }

    .co-card { padding: 16px; }

    /* Hero section on dashboard */
    .hero { padding: 20px 18px !important; }
    .hero h1 { font-size: 1.55rem !important; }
    .hero p  { font-size: 0.9rem !important; }

    /* Stat pills wrap */
    .stat-row { gap: 6px !important; }
    .stat-pill { font-size: 0.72rem !important; padding: 3px 10px !important; }

    /* Milestone bar */
    .milestone-bar { padding: 10px 12px !important; overflow-x: auto; }
    .milestone { font-size: 0.65rem !important; }
    .milestone .dot { width: 24px !important; height: 24px !important; }

    /* ATS param row — stack vertically */
    .param-row { flex-direction: column !important; gap: 6px !important; }
    .param-label { width: 100% !important; }
    .param-bar-wrap { width: 100% !important; }
    .param-comment { width: 100% !important; text-align: left !important; }

    /* Ensure inputs are full-width */
    .stTextArea textarea { font-size: 0.9rem; }

    /* Reduce sidebar width */
    section[data-testid="stSidebar"] { min-width: 200px !important; }
}

@media (max-width: 480px) {
    .hero h1 { font-size: 1.3rem !important; }
    .co-badge { font-size: 0.65rem; }

    /* Stack the 4-column dashboard to 1-col */
    .step-title { font-size: 0.95rem !important; }
    .step-body  { font-size: 0.82rem !important; }
}
</style>
"""


def inject_global_css():
    """Inject shared CareerOS CSS. Call once at top of each page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
