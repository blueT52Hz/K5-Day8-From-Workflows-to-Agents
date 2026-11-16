"""Projector-first theme for the Streamlit demo.

Light warm background, near-black ink, one accent; green/red/amber only for
pass/fail/warning. Large type so the back row can read amounts. Geist loads from
Google Fonts when online and falls back to Segoe UI offline.
"""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap");
:root {
  --lx-bg: #FAF8F4; --lx-surface: #FFFFFF; --lx-ink: #14161A; --lx-muted: #4E535C;
  --lx-line: #E2DDD3; --lx-accent: #1F4FD8; --lx-accent-soft: #E6ECFB;
  --lx-ok: #11704F; --lx-ok-soft: #E1F2EA; --lx-bad: #B8231A; --lx-bad-soft: #FBE6E3;
  --lx-warn: #8F5400; --lx-warn-soft: #FCEFD8; --lx-info: #1F4FD8; --lx-info-soft: #E6ECFB;
  --lx-idle: #4E535C; --lx-idle-soft: #EEEBE5;
  --lx-font: "Geist", "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif;
  --lx-mono: "Geist Mono", "Cascadia Mono", Consolas, monospace;
}
html, body, .stApp, [class*="st-"] { font-family: var(--lx-font); }
/* The rule above also hits Streamlit's ligature icons (expander arrow, sidebar toggle):
   without their icon font they render as raw text like "keyboard_arrow_down". */
[data-testid="stIconMaterial"], span[class*="material-symbols"], [data-testid="stExpanderToggleIcon"] {
  font-family: "Material Symbols Rounded" !important; }
[data-testid="stExpander"] summary { align-items: center; }
.stApp { background: var(--lx-bg); color: var(--lx-ink); }
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1480px; padding-top: 1.6rem; padding-bottom: 4rem; }
.stApp p, .stApp li, .stApp label { font-size: 1.15rem; }
code, pre { font-family: var(--lx-mono) !important; }

button[data-baseweb="tab"] p { font-size: 1.25rem; font-weight: 600; }
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--lx-accent); }
[data-testid="stMetricValue"] { font-size: 2.3rem; font-weight: 700; letter-spacing: -0.02em; }
[data-testid="stMetricLabel"] p { font-size: 1.05rem; color: var(--lx-muted); }
.stButton > button { font-size: 1.1rem; font-weight: 600; border-radius: 12px; padding: 0.6rem 1.1rem; }
.stButton > button[kind="primary"] { background: var(--lx-ink); color: #FFFFFF; border: 1px solid var(--lx-ink); }
.stButton > button[kind="primary"]:hover { background: var(--lx-accent); border-color: var(--lx-accent); }

.lx-hero { padding: 0.4rem 0 1.4rem; border-bottom: 1px solid var(--lx-line); margin-bottom: 1.2rem; }
.lx-hero h1 { font-size: clamp(2.2rem, 3.4vw, 3.4rem); line-height: 1.06; letter-spacing: -0.035em;
  font-weight: 700; max-width: 72rem; margin: 0; color: var(--lx-ink); }
.lx-hero p { font-size: 1.25rem; color: var(--lx-muted); margin: 0.6rem 0 0; }

.lx-section { margin: 1.6rem 0 0.7rem; }
.lx-section h3 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; color: var(--lx-ink); }
.lx-section p { font-size: 1.1rem; color: var(--lx-muted); margin: 0.25rem 0 0; }

.lx-card { background: var(--lx-surface); border: 1px solid var(--lx-line); border-radius: 18px;
  padding: 1.2rem 1.4rem; margin-bottom: 0.9rem; }
.lx-card h4 { font-size: 1.35rem; margin: 0 0 0.5rem; letter-spacing: -0.01em; }
.lx-card .lx-kv { display: flex; justify-content: space-between; gap: 1rem; font-size: 1.1rem;
  padding: 0.3rem 0; border-bottom: 1px dashed var(--lx-line); }
.lx-card .lx-kv:last-child { border-bottom: 0; }
.lx-card .lx-kv span:first-child { color: var(--lx-muted); }
.lx-card .lx-kv span:last-child { font-weight: 600; text-align: right; }
.lx-ticket { font-size: 1.3rem; line-height: 1.45; border-left: 4px solid var(--lx-accent);
  padding: 0.4rem 0 0.4rem 1rem; margin: 0.6rem 0; }

.lx-badge { display: inline-block; padding: 0.22rem 0.75rem; border-radius: 999px; font-weight: 600;
  font-size: 1.02rem; border: 1px solid transparent; }
.lx-ok { color: var(--lx-ok); background: var(--lx-ok-soft); border-color: var(--lx-ok); }
.lx-bad { color: var(--lx-bad); background: var(--lx-bad-soft); border-color: var(--lx-bad); }
.lx-warn { color: var(--lx-warn); background: var(--lx-warn-soft); border-color: var(--lx-warn); }
.lx-info { color: var(--lx-info); background: var(--lx-info-soft); border-color: var(--lx-info); }
.lx-idle { color: var(--lx-idle); background: var(--lx-idle-soft); border-color: var(--lx-line); }

.lx-banner { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; padding: 1rem 1.3rem;
  border-radius: 16px; background: var(--lx-surface); border: 1px solid var(--lx-line); margin: 0.8rem 0; }
.lx-banner strong { font-size: 1.5rem; letter-spacing: -0.01em; }

.lx-table { width: 100%; border-collapse: collapse; background: var(--lx-surface); border-radius: 14px;
  overflow: hidden; border: 1px solid var(--lx-line); font-size: 1.1rem; }
.lx-table th { text-align: left; font-weight: 600; color: var(--lx-muted); background: var(--lx-idle-soft);
  padding: 0.65rem 0.9rem; }
.lx-table td { padding: 0.6rem 0.9rem; border-top: 1px solid var(--lx-line); vertical-align: top; }
.lx-table td.lx-num { text-align: right; font-variant-numeric: tabular-nums; }

.lx-timeline { list-style: none; padding: 0; margin: 0.4rem 0; }
.lx-step { display: grid; grid-template-columns: 2.4rem 11rem 1fr; gap: 0.8rem; align-items: start;
  padding: 0.6rem 0.8rem; border-left: 4px solid var(--lx-line); background: var(--lx-surface);
  margin-bottom: 0.4rem; border-radius: 0 12px 12px 0; }
.lx-step-no { font-weight: 700; color: var(--lx-muted); }
.lx-step-kind { font-weight: 700; font-size: 1.1rem; }
.lx-step code { white-space: pre-wrap; word-break: break-word; font-size: 0.95rem; background: transparent; }
.lx-step-bad { border-left-color: var(--lx-bad); background: var(--lx-bad-soft); }
.lx-step-warn { border-left-color: var(--lx-warn); background: var(--lx-warn-soft); }
.lx-step-info { border-left-color: var(--lx-info); }

.lx-chain { font-family: var(--lx-mono); font-size: 0.98rem; line-height: 1.9; }
.lx-chain span { padding: 0.1rem 0.45rem; border-radius: 6px; background: var(--lx-idle-soft); }
.lx-chain span.lx-hot { background: var(--lx-bad-soft); color: var(--lx-bad); font-weight: 600; }

.lx-placeholder { border: 2px dashed var(--lx-line); border-radius: 18px; padding: 1.4rem 1.6rem;
  background: repeating-linear-gradient(135deg, #FFFFFF 0 14px, #F6F3EE 14px 28px); }
.lx-placeholder h4 { font-size: 1.3rem; margin: 0 0 0.3rem; }
.lx-placeholder p { color: var(--lx-muted); margin: 0 0 0.5rem; }
.lx-placeholder code { font-size: 0.95rem; }

/* Sidebar + chat page */
[data-testid="stSidebar"] { background: var(--lx-surface); border-right: 1px solid var(--lx-line); }
.lx-brand { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.4rem; }
.lx-side-claim { background: var(--lx-bg); border: 1px solid var(--lx-line); border-radius: 12px;
  padding: 0.6rem 0.8rem; margin: 0.4rem 0 0.8rem; }
.lx-side-claim div { display: flex; justify-content: space-between; gap: 0.6rem; padding: 0.2rem 0; font-size: 1rem; }
.lx-side-claim span { color: var(--lx-muted); }
.lx-chat-head { border-bottom: 1px solid var(--lx-line); padding-bottom: 0.8rem; margin-bottom: 1rem; }
.lx-chat-head h2 { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
.lx-chat-head p { color: var(--lx-muted); margin: 0.3rem 0 0; }
.lx-muted { color: var(--lx-muted); }
[data-testid="stChatMessage"] { background: var(--lx-surface); border: 1px solid var(--lx-line);
  border-radius: 16px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }

.lx-calls { list-style: none; padding: 0; margin: 0.2rem 0; }
.lx-call { display: grid; grid-template-columns: 2rem 10.5rem 1fr auto; gap: 0.7rem; align-items: start;
  padding: 0.45rem 0.7rem; margin-bottom: 0.3rem; border-radius: 0 10px 10px 0;
  border-left: 4px solid var(--lx-line); background: var(--lx-bg); font-size: 1rem; }
.lx-call-no { font-weight: 700; color: var(--lx-muted); }
.lx-call-kind { font-weight: 600; white-space: nowrap; }
.lx-call-body strong { margin-right: 0.5rem; }
.lx-call-body code { white-space: pre-wrap; word-break: break-word; font-size: 0.9rem; background: transparent; }
.lx-call-cost { font-family: var(--lx-mono); font-size: 0.9rem; color: var(--lx-muted); white-space: nowrap; }
.lx-call-tool { border-left-color: var(--lx-accent); }
.lx-call-model { border-left-color: #7A3FD1; background: #F3EDFC; }
.lx-call-host { border-left-color: var(--lx-ok); background: var(--lx-ok-soft); }
.lx-call-trace { border-left-color: var(--lx-line); }
.lx-call-hot { border-left-color: var(--lx-bad); background: var(--lx-bad-soft); }

.lx-metrics { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 0.5rem; margin: 0.8rem 0 0.5rem; }
.lx-metric { background: var(--lx-bg); border: 1px solid var(--lx-line); border-radius: 12px; padding: 0.5rem 0.7rem; }
.lx-metric span { display: block; font-size: 0.9rem; color: var(--lx-muted); }
.lx-metric strong { font-size: 1.15rem; font-variant-numeric: tabular-nums; }
.lx-expect { display: flex; flex-wrap: wrap; align-items: center; gap: 0.8rem; font-size: 1rem; margin-bottom: 0.4rem; }
@media (max-width: 900px) { .lx-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lx-call { grid-template-columns: 1.6rem 1fr; } }

.lx-heat td.lx-cell { width: 2.2rem; height: 2.2rem; padding: 0; text-align: center; font-size: 0.9rem; }
.lx-cell-pass { background: var(--lx-ok-soft); color: var(--lx-ok); }
.lx-cell-fail { background: var(--lx-bad); color: #FFFFFF; font-weight: 700; }
.lx-cell-none { background: var(--lx-idle-soft); color: var(--lx-idle); }
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
