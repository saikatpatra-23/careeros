# -*- coding: utf-8 -*-
"""
Shared CSS for CareerOS — dark theme, modern SaaS look.
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }

/* ── Page title — replaces big gradient banners ───────────────────────── */
.pg-title {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.pg-icon { font-size: 1.25rem; line-height: 1; }
.pg-name { font-size: 1.1rem; font-weight: 700; color: #E2E8F0; }
.pg-sub  { font-size: 0.8rem; color: #6B7280; }

/* ── Cards ────────────────────────────────────────────────────────────── */
.co-card {
    background: #1A1D27;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid rgba(255,255,255,0.07);
    height: 100%;
    transition: border-color 0.18s, box-shadow 0.18s;
}
.co-card:hover {
    border-color: rgba(79,142,247,0.28);
    box-shadow: 0 4px 22px rgba(0,0,0,0.35);
}

/* ── Badges ───────────────────────────────────────────────────────────── */
.co-badge {
    display: inline-block;
    background: rgba(79,142,247,0.12);
    color: #4F8EF7;
    border: 1px solid rgba(79,142,247,0.22);
    border-radius: 6px;
    font-size: 0.67rem;
    font-weight: 700;
    padding: 2px 8px;
    margin-bottom: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.co-badge.done   { background: rgba(16,185,129,0.1);  color: #10B981; border-color: rgba(16,185,129,0.22); }
.co-badge.locked { background: rgba(255,255,255,0.04); color: #6B7280;  border-color: rgba(255,255,255,0.08); }
.co-badge.soon   { background: rgba(245,158,11,0.1);  color: #F59E0B; border-color: rgba(245,158,11,0.22); }

/* ── Progress bar ─────────────────────────────────────────────────────── */
.co-prog-wrap {
    background: rgba(255,255,255,0.07);
    border-radius: 100px;
    height: 3px;
    margin: 14px 0 4px 0;
    overflow: hidden;
}
.co-prog-fill {
    height: 3px;
    border-radius: 100px;
    background: linear-gradient(90deg, #4F8EF7, #818CF8);
}

/* ── Tip / info strips ────────────────────────────────────────────────── */
.co-tip {
    background: rgba(245,158,11,0.07);
    border-left: 3px solid #F59E0B;
    border-radius: 0 8px 8px 0;
    padding: 11px 15px;
    font-size: 0.85rem;
    color: #C49A20;
    line-height: 1.6;
}
.co-info {
    background: rgba(79,142,247,0.07);
    border-left: 3px solid #4F8EF7;
    border-radius: 0 8px 8px 0;
    padding: 11px 15px;
    font-size: 0.85rem;
    color: #93B4F8;
    line-height: 1.55;
    margin: 8px 0;
}

/* ── Compact file uploader ────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    padding: 10px 14px !important;
    min-height: 52px !important;
    background: rgba(79,142,247,0.05) !important;
    border: 1.5px dashed rgba(79,142,247,0.28) !important;
    border-radius: 8px !important;
    transition: border-color 0.15s, background 0.15s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(79,142,247,0.55) !important;
    background: rgba(79,142,247,0.09) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    font-size: 0.82rem !important;
    color: #9CA3AF !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > small {
    font-size: 0.72rem !important;
    color: #6B7280 !important;
}

/* ── Buttons ──────────────────────────────────────────────────────────── */
[data-testid="baseButton-primary"],
[data-testid="baseButton-secondary"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: opacity 0.15s !important;
}

/* ── Disabled text areas (copy-paste content) ────────────────────────── */
.stTextArea textarea:disabled {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    color: #C9D1D9 !important;
    font-size: 0.875rem !important;
    line-height: 1.65 !important;
    cursor: text !important;
    border-radius: 8px !important;
    opacity: 1 !important;
    resize: vertical !important;
}

/* ── Dividers ─────────────────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 14px 0 !important; }

/* ── Sidebar ──────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}

/* ── Expanders ────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #1A1D27 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-testid="stTab"] {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
}

/* ── Metric ───────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #1A1D27;
    border-radius: 10px;
    padding: 14px 18px;
    border: 1px solid rgba(255,255,255,0.07);
}

/* ── ATS param row — mobile stack ────────────────────────────────────── */
@media (max-width: 768px) {
    .param-row { flex-direction: column !important; gap: 5px !important; }
    .param-label { width: 100% !important; }
    .param-bar-wrap { width: 100% !important; }
    .param-comment { width: 100% !important; text-align: left !important; font-size: 0.8rem !important; }
    .milestone-bar { overflow-x: auto; }
    .milestone { font-size: 0.64rem !important; }
    section[data-testid="stSidebar"] { min-width: 180px !important; }
}
</style>
"""


def inject_global_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
