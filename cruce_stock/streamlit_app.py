"""
streamlit_app.py
Backoffice web — Farmacias & Perfumerías Global
Sistema de cruce de stock para pedidos ecommerce.
"""

from __future__ import annotations
import os
import pathlib
import tempfile
from datetime import datetime

import yaml
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Global — Gestión de Stock",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CONFIG_PATH = pathlib.Path(__file__).parent / "config.yaml"

# ── Paleta principal ────────────────────────────────────────
AZUL        = "#2563EB"   # blue-600
AZUL_OSCURO = "#1D4ED8"   # blue-700
AZUL_CLARO  = "#EFF6FF"   # blue-50
ROSA        = "#E11D48"   # rose-600
VERDE       = "#059669"   # emerald-600
AMARILLO    = "#D97706"   # amber-600
GRIS        = "#F8FAFC"   # slate-50
SLATE       = "#64748B"   # slate-500


# ════════════════════════════════════════════════════════════
#  CSS  — Sistema de diseño completo
# ════════════════════════════════════════════════════════════
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}}

/* ══════════════════════════════════════════
   DESIGN TOKENS
   ══════════════════════════════════════════ */
:root {{
  /* Backgrounds */
  --bg-main:       #F8FAFC;
  --bg-card:       #FFFFFF;
  --bg-secondary:  #F1F5F9;
  --bg-input:      #FFFFFF;

  /* Text */
  --text-primary:  #0F172A;
  --text-secondary:#475569;
  --text-muted:    #94A3B8;

  /* Borders */
  --border:        #E2E8F0;
  --border-strong: #CBD5E1;

  /* Shadows */
  --shadow-sm:     0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:     0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:     0 10px 25px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.06);

  /* Radii */
  --r-sm:  6px;
  --r-md:  10px;
  --r-lg:  14px;
  --r-xl:  18px;

  /* Accents (mantener compat) */
  --border-color:  #E2E8F0;
  --bg-secondary-alias: #F1F5F9;
  --expander-bg:   #F8FAFC;
  --hist-row-bg:   #FFFFFF;
  --hist-row-hover:#F8FAFC;
  --metric-bg:     #FFFFFF;
  --upload-bg:     #F8FAFC;
  --page-hdr-bg:   #FFFFFF;
  --cfg-card-bg:   #FFFFFF;
  --help-bg:       #FFFFFF;
  --override-bg:   #FFFFFF;
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --bg-main:       #0F172A;
    --bg-card:       #1E293B;
    --bg-secondary:  #1E293B;
    --bg-input:      #334155;
    --text-primary:  #F1F5F9;
    --text-secondary:#94A3B8;
    --text-muted:    #64748B;
    --border:        #334155;
    --border-strong: #475569;
    --shadow-sm:     0 1px 3px rgba(0,0,0,0.3);
    --shadow-md:     0 4px 12px rgba(0,0,0,0.4);
    --border-color:  #334155;
    --bg-secondary-alias: #1E293B;
    --expander-bg:   #1E293B;
    --hist-row-bg:   #1E293B;
    --hist-row-hover:#334155;
    --metric-bg:     #1E293B;
    --upload-bg:     #1E293B;
    --page-hdr-bg:   #1E293B;
    --cfg-card-bg:   #1E293B;
    --help-bg:       #1E293B;
    --override-bg:   #1E293B;
  }}
}}

/* ══════════════════════════════════════════
   BASE — FONDO Y LAYOUT
   ══════════════════════════════════════════ */
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.main, .main > div, .block-container {{
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}
.block-container {{
    padding: 28px 32px 48px 32px !important;
    max-width: 1280px;
}}

/* ══════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background: #0F172A !important;
    min-width: 230px !important;
    max-width: 230px !important;
    transform: none !important;
    visibility: visible !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}}
section[data-testid="stSidebar"] > div {{
    background: transparent !important;
}}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] * {{
    color: #CBD5E1 !important;
}}
button[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
.st-emotion-cache-zq5wmm, .st-emotion-cache-1wbqy5l,
[class*="collapsedControl"] {{ display: none !important; }}

/* Logo */
.sb-logo {{
    padding: 24px 18px 18px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 12px;
}}
.sb-logo-icon {{
    background: {AZUL};
    border-radius: var(--r-md);
    width: 38px; height: 38px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.3);
}}
.sb-logo-icon svg {{ display: block; }}
.sb-brand-name  {{ font-size: 0.83rem; font-weight: 700; color: #F1F5F9 !important; line-height: 1.2; }}
.sb-brand-sub   {{ font-size: 0.67rem; color: #64748B !important; margin-top: 1px; letter-spacing: 0.3px; }}

/* Nav section labels */
.sb-section-label {{
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 1.4px; text-transform: uppercase;
    color: #475569 !important;
    padding: 16px 18px 4px 18px;
}}

/* Nav buttons */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    color: #94A3B8 !important;
    text-align: left !important;
    padding: 8px 12px !important;
    border-radius: var(--r-sm) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    margin: 1px 6px !important;
    transition: all 0.15s !important;
    letter-spacing: 0.1px !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
    background: rgba(255,255,255,0.07) !important;
    color: #F1F5F9 !important;
}}
.nav-active {{
    display: flex; align-items: center;
    background: rgba(37,99,235,0.2) !important;
    border: 1px solid rgba(37,99,235,0.35);
    border-radius: var(--r-sm);
    padding: 8px 12px;
    margin: 1px 6px;
    font-size: 0.85rem; font-weight: 600;
    color: #93C5FD !important;
    cursor: default;
}}

/* ══════════════════════════════════════════
   PAGE HEADER
   ══════════════════════════════════════════ */
.page-hdr {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 18px 24px 16px 24px;
    margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
}}
.page-title {{
    font-size: 1.15rem; font-weight: 700;
    color: var(--text-primary); margin: 0; letter-spacing: -0.2px;
}}
.page-sub {{
    font-size: 0.8rem; color: var(--text-muted);
    margin: 3px 0 0 0; font-weight: 400;
}}
.badge-rosa {{
    background: {ROSA}18; color: {ROSA};
    border: 1px solid {ROSA}30;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.71rem; font-weight: 600; letter-spacing: 0.2px;
}}
.badge-azul {{
    background: {AZUL}18; color: {AZUL};
    border: 1px solid {AZUL}30;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.71rem; font-weight: 600;
}}

/* ══════════════════════════════════════════
   SECTION LABELS
   ══════════════════════════════════════════ */
.sec-label {{
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: var(--text-muted);
    margin: 24px 0 10px 0;
    display: flex; align-items: center; gap: 8px;
}}
.sec-label::after {{
    content: ''; flex: 1; height: 1px;
    background: var(--border);
}}

/* ══════════════════════════════════════════
   CARDS BASE
   ══════════════════════════════════════════ */
.card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 20px 22px;
}}
.card + .card {{ margin-top: 12px; }}

/* ══════════════════════════════════════════
   KPI CARDS — Dashboard
   ══════════════════════════════════════════ */
.kpi-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 20px 22px;
    position: relative; overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s;
}}
.kpi-card:hover {{
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}}
.kpi-card::after {{
    content: ''; position: absolute;
    bottom: 0; left: 0; right: 0; height: 3px;
    border-radius: 0 0 var(--r-lg) var(--r-lg);
}}
.kpi-ok::after   {{ background: {VERDE}; }}
.kpi-warn::after {{ background: {AMARILLO}; }}
.kpi-crit::after {{ background: {ROSA}; }}
.kpi-info::after {{ background: {AZUL}; }}
.kpi-icon {{
    font-size: 1.6rem; margin-bottom: 12px;
    display: block; line-height: 1;
}}
.kpi-label {{
    font-size: 0.69rem; font-weight: 700;
    letter-spacing: 0.9px; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 6px;
}}
.kpi-value {{
    font-size: 2.4rem; font-weight: 800;
    color: var(--text-primary); line-height: 1;
    letter-spacing: -1px;
}}
.kpi-detail {{
    font-size: 0.76rem; color: var(--text-muted);
    margin-top: 6px; font-weight: 400;
}}

/* ══════════════════════════════════════════
   DASHBOARD — componentes
   ══════════════════════════════════════════ */
.dash-greeting {{
    font-size: 1.45rem; font-weight: 800;
    color: var(--text-primary); margin-bottom: 2px;
    letter-spacing: -0.4px;
}}
.dash-sub {{
    font-size: 0.84rem; color: var(--text-muted);
    margin-bottom: 24px; font-weight: 400;
}}
.dash-section-title {{
    font-size: 0.69rem; font-weight: 700;
    letter-spacing: 0.9px; text-transform: uppercase;
    color: var(--text-muted);
    margin: 24px 0 12px 0; padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}}
.dash-alert-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 11px 14px;
    border-radius: var(--r-md); margin-bottom: 7px;
    font-size: 0.84rem; font-weight: 500;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-left: 3px solid transparent;
    color: var(--text-primary);
}}
.dash-alert-crit {{ border-left-color: {ROSA}; }}
.dash-alert-warn {{ border-left-color: {AMARILLO}; }}
.dash-alert-info {{ border-left-color: {AZUL}; }}
.dash-suc-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 9px 0; border-bottom: 1px solid var(--border);
    font-size: 0.84rem; color: var(--text-primary);
}}
.dash-suc-row:last-child {{ border-bottom: none; }}
.dash-suc-name {{ flex: 1; font-weight: 500; font-size: 0.82rem; }}
.dash-suc-bar-wrap {{
    width: 72px; background: var(--bg-secondary);
    border-radius: 4px; height: 5px;
}}
.dash-suc-bar {{ height: 5px; border-radius: 4px; background: {AZUL}; }}
.dash-suc-cnt {{
    width: 22px; text-align: right;
    font-weight: 700; color: {AZUL}; font-size: 0.8rem;
}}
.dash-progress-wrap {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 14px 18px; margin-bottom: 8px;
}}
.dash-progress-label {{
    font-size: 0.8rem; color: var(--text-secondary);
    margin-bottom: 8px; font-weight: 500;
}}
.dash-progress-bar-bg {{
    background: var(--border); border-radius: 6px; height: 8px;
    overflow: hidden;
}}
.dash-progress-bar {{
    height: 8px; border-radius: 6px;
    background: linear-gradient(90deg, {AZUL}, {VERDE});
}}
.dash-ultimo-cruce {{
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--r-md); padding: 14px 18px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: var(--shadow-sm);
}}
.dash-uc-icon {{ font-size: 1.5rem; flex-shrink: 0; }}
.dash-uc-name {{ font-weight: 600; font-size: 0.88rem; color: var(--text-primary); }}
.dash-uc-meta {{ color: var(--text-muted); font-size: 0.76rem; margin-top: 3px; }}

/* ══════════════════════════════════════════
   RESULT BANNER
   ══════════════════════════════════════════ */
.result-banner {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border-radius: var(--r-lg);
    padding: 16px 22px; color: white; margin-bottom: 20px;
    box-shadow: var(--shadow-md);
}}

/* ══════════════════════════════════════════
   UPLOAD ZONES
   ══════════════════════════════════════════ */
.upload-zone {{
    background: var(--bg-card);
    border: 1.5px dashed var(--border-strong);
    border-radius: var(--r-lg); padding: 20px 16px;
    text-align: center; margin-bottom: 4px;
    transition: border-color 0.2s, background 0.2s;
}}
.upload-zone:hover {{
    border-color: {AZUL};
    background: {AZUL}06;
}}
.upload-zone-title {{ color: var(--text-primary); font-weight: 700; font-size: 0.9rem; }}
.upload-zone-sub   {{ color: var(--text-muted); font-size: 0.77rem; margin-top: 5px; line-height: 1.4; }}

/* ══════════════════════════════════════════
   BOTONES
   ══════════════════════════════════════════ */
div[data-testid="stButton"] > button {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border-radius: var(--r-sm) !important;
    transition: all 0.15s !important;
    letter-spacing: 0.1px !important;
}}
div[data-testid="stButton"] > button[kind="primary"] {{
    background: {AZUL} !important;
    border: none !important;
    color: white !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 10px 0 !important;
    box-shadow: 0 1px 3px rgba(37,99,235,0.4) !important;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background: {AZUL_OSCURO} !important;
    box-shadow: 0 3px 8px rgba(37,99,235,0.5) !important;
    transform: translateY(-1px) !important;
}}
div[data-testid="stButton"] > button[kind="secondary"],
div[data-testid="stButton"] > button:not([kind="primary"]) {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}}
div[data-testid="stButton"] > button:not([kind="primary"]):hover {{
    background: var(--bg-secondary) !important;
    border-color: var(--text-muted) !important;
    color: var(--text-primary) !important;
}}
div[data-testid="stDownloadButton"] > button {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border-radius: var(--r-sm) !important;
    padding: 10px 0 !important;
    transition: all 0.15s !important;
}}
div[data-testid="stDownloadButton"] > button:hover {{
    background: var(--bg-secondary) !important;
    border-color: {AZUL} !important;
    color: {AZUL} !important;
}}

/* ══════════════════════════════════════════
   MÉTRICAS NATIVAS
   ══════════════════════════════════════════ */
div[data-testid="metric-container"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 16px 18px !important;
}}
div[data-testid="metric-container"] label {{
    font-size: 0.69rem !important; font-weight: 700 !important;
    letter-spacing: 0.8px !important; text-transform: uppercase !important;
    color: var(--text-muted) !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.9rem !important; font-weight: 800 !important;
    color: var(--text-primary) !important; letter-spacing: -0.5px !important;
}}

/* ══════════════════════════════════════════
   EXPANDERS
   ══════════════════════════════════════════ */
[data-testid="stExpander"] {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--shadow-sm) !important;
}}
[data-testid="stExpander"] summary {{
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
}}

/* ══════════════════════════════════════════
   ZONA BADGES
   ══════════════════════════════════════════ */
.zona-0 {{ background:#EFF6FF; color:#1E40AF; border-radius:4px; padding:1px 7px; font-size:0.71rem; font-weight:600; }}
.zona-1 {{ background:#F0FDF4; color:#166534; border-radius:4px; padding:1px 7px; font-size:0.71rem; font-weight:600; }}
.zona-2 {{ background:#FFFBEB; color:#92400E; border-radius:4px; padding:1px 7px; font-size:0.71rem; font-weight:600; }}
.zona-3 {{ background:#FFF7ED; color:#9A3412; border-radius:4px; padding:1px 7px; font-size:0.71rem; font-weight:600; }}
.zona-4 {{ background:#FFF1F2; color:#9F1239; border-radius:4px; padding:1px 7px; font-size:0.71rem; font-weight:600; }}
@media (prefers-color-scheme: dark) {{
  .zona-0 {{ background:#172554; color:#93C5FD; }}
  .zona-1 {{ background:#052E16; color:#86EFAC; }}
  .zona-2 {{ background:#422006; color:#FCD34D; }}
  .zona-3 {{ background:#431407; color:#FDBA74; }}
  .zona-4 {{ background:#4C0519; color:#FDA4AF; }}
}}

/* ══════════════════════════════════════════
   ESTADO BADGES
   ══════════════════════════════════════════ */
.est-badge {{
    display: inline-flex; align-items: center;
    border-radius: 4px;
    padding: 3px 8px; font-size: 0.72rem; font-weight: 600;
    white-space: nowrap; letter-spacing: 0.1px;
}}
.eb-busqueda      {{ background:#EFF6FF; color:#1D4ED8; }}
.eb-encontrado    {{ background:#F0FDF4; color:#15803D; }}
.eb-malstock      {{ background:#FFFBEB; color:#B45309; }}
.eb-llamarsuc     {{ background:#FFF7ED; color:#C2410C; }}
.eb-resuelto      {{ background:#FAF5FF; color:#7C3AED; }}
.eb-llamarcliente {{ background:#FFF1F2; color:#BE123C; }}
@media (prefers-color-scheme: dark) {{
  .eb-busqueda      {{ background:#1E3A8A; color:#93C5FD; }}
  .eb-encontrado    {{ background:#14532D; color:#86EFAC; }}
  .eb-malstock      {{ background:#451A03; color:#FCD34D; }}
  .eb-llamarsuc     {{ background:#431407; color:#FDBA74; }}
  .eb-resuelto      {{ background:#2E1065; color:#C4B5FD; }}
  .eb-llamarcliente {{ background:#4C0519; color:#FDA4AF; }}
}}

/* ══════════════════════════════════════════
   TABLA DE RESULTADOS
   ══════════════════════════════════════════ */
.tbl-wrap {{
    border: 1px solid var(--border);
    border-radius: var(--r-lg); overflow: hidden;
    box-shadow: var(--shadow-sm);
    margin-top: 8px;
}}
.tbl-hdr {{
    display: grid;
    grid-template-columns: 88px 1fr 180px 56px 130px;
    background: var(--bg-secondary);
    padding: 10px 16px;
    font-size: 0.67rem; font-weight: 700;
    letter-spacing: 0.9px; text-transform: uppercase;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
}}
.tbl-group-hdr {{
    background: {AZUL}0D;
    border-left: 3px solid {AZUL};
    padding: 7px 16px; font-size: 0.78rem; font-weight: 700;
    color: {AZUL}; display: flex; align-items: center; gap: 8px;
}}
@media (prefers-color-scheme: dark) {{
  .tbl-group-hdr {{ color: #93C5FD; background: #172554; border-left-color: #3B82F6; }}
}}
.tbl-row {{
    display: grid;
    grid-template-columns: 88px 1fr 180px 56px 130px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    align-items: center; color: var(--text-primary);
    background: var(--bg-card);
    transition: background 0.1s;
    font-size: 0.84rem;
}}
.tbl-row:hover {{ background: var(--bg-secondary); }}
.tbl-row:last-child {{ border-bottom: none; }}
.tbl-row.sin-cob {{ background: #FFF1F2; }}
@media (prefers-color-scheme: dark) {{ .tbl-row.sin-cob {{ background: #4C0519; }} }}
.tbl-pedido   {{ font-weight: 700; color: {AZUL}; font-size: 0.8rem; letter-spacing: 0.2px; }}
.tbl-prod     {{ font-weight: 600; color: var(--text-primary); }}
.tbl-prod-sub {{ font-size: 0.73rem; color: var(--text-muted); margin-top: 3px; font-weight: 400; }}
.tbl-farm     {{ font-size: 0.82rem; font-weight: 500; color: var(--text-primary); }}
.tbl-farm-zona {{ margin-top: 3px; }}
.tbl-uds     {{
    font-weight: 800; font-size: 1.05rem; color: {AZUL};
    text-align: center;
}}

/* ══════════════════════════════════════════
   HISTORIAL
   ══════════════════════════════════════════ */
.hist-hdr {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--r-md) var(--r-md) 0 0;
    padding: 10px 16px;
    font-size: 0.69rem; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
    color: var(--text-muted); display: flex;
}}
.hist-row {{
    background: var(--bg-card);
    border: 1px solid var(--border); border-top: none;
    padding: 12px 16px; font-size: 0.84rem;
    display: flex; align-items: center;
    color: var(--text-primary);
    transition: background 0.1s;
}}
.hist-row:hover {{ background: var(--bg-secondary); }}
.hist-row:last-child {{ border-radius: 0 0 var(--r-md) var(--r-md); }}
.hc-id   {{ width: 58px; flex-shrink: 0; color: {AZUL}; font-weight: 700; font-size: 0.8rem; }}
.hc-name {{ flex: 1; }}
.hc-hora {{ width: 115px; flex-shrink: 0; color: var(--text-muted); font-size: 0.75rem; }}
.hc-stat {{ width: 155px; flex-shrink: 0; text-align: center; }}
.hc-dl   {{ width: 78px; flex-shrink: 0; text-align: right; }}

/* ══════════════════════════════════════════
   CONFIG CARDS / AYUDA
   ══════════════════════════════════════════ */
.cfg-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 18px 22px; margin-bottom: 12px;
}}
.cfg-card-title {{
    color: var(--text-primary); font-weight: 700; font-size: 0.9rem;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}}
.help-step {{
    display: flex; gap: 16px; align-items: flex-start;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 16px 20px; margin-bottom: 10px;
}}
.help-num {{
    background: {AZUL}; color: white; border-radius: 50%;
    width: 28px; height: 28px; display: flex;
    align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.8rem; flex-shrink: 0;
}}
.help-body strong {{ color: {AZUL}; font-weight: 700; }}
.help-body p {{ color: var(--text-secondary); font-size: 0.83rem; margin: 4px 0 0 0; line-height: 1.5; }}

/* ══════════════════════════════════════════
   OVERRIDE ROWS
   ══════════════════════════════════════════ */
.override-row {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-md); padding: 10px 14px; margin-bottom: 6px;
    display: flex; align-items: center; gap: 12px;
    transition: box-shadow 0.15s;
}}
.override-row:hover {{ box-shadow: var(--shadow-sm); }}
.override-producto {{ font-weight: 600; color: var(--text-primary); flex: 1; font-size: 0.85rem; }}
.override-sucursal {{ color: var(--text-secondary); font-size: 0.83rem; }}
.override-zona     {{ font-size: 0.72rem; }}
.override-stock    {{ font-size: 0.78rem; color: var(--text-muted); }}

/* ══════════════════════════════════════════
   VISTA CADETE
   ══════════════════════════════════════════ */
.cadete-progress-wrap {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-sm);
    padding: 18px 20px; margin-bottom: 20px;
}}
.cadete-progress-title {{
    font-size: 1rem; font-weight: 700;
    color: var(--text-primary); margin-bottom: 0;
}}
.cadete-farmacia-hdr {{
    background: {AZUL};
    color: white; border-radius: var(--r-md) var(--r-md) 0 0;
    padding: 12px 16px; font-weight: 700; font-size: 0.9rem;
    margin-top: 18px; display: flex; align-items: center; gap: 10px;
    letter-spacing: 0.1px;
}}
.cadete-farmacia-badge {{
    background: rgba(255,255,255,0.18);
    border-radius: 6px;
    padding: 3px 10px; font-size: 0.75rem; margin-left: auto;
    font-weight: 600;
}}
.cadete-item {{
    background: var(--bg-card);
    border: 1px solid var(--border); border-top: none;
    padding: 14px 16px;
}}
.cadete-item:last-child {{ border-radius: 0 0 var(--r-md) var(--r-md); }}
.cadete-producto {{
    font-weight: 700; color: var(--text-primary);
    font-size: 0.97rem; line-height: 1.3;
}}
.cadete-meta {{
    color: var(--text-muted); font-size: 0.77rem;
    margin-top: 4px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}}
.cadete-qty {{
    background: {AZUL}18; color: {AZUL};
    border: 1px solid {AZUL}30;
    border-radius: 5px;
    padding: 2px 9px; font-weight: 700; font-size: 0.82rem; display: inline-block;
}}
.est-busqueda      {{ background:#EFF6FF; color:#1D4ED8; border-radius:4px; padding:3px 8px; font-size:0.75rem; font-weight:600; }}
.est-encontrado    {{ background:#F0FDF4; color:#15803D; border-radius:4px; padding:3px 8px; font-size:0.75rem; font-weight:600; }}
.est-malstock      {{ background:#FFFBEB; color:#B45309; border-radius:4px; padding:3px 8px; font-size:0.75rem; font-weight:600; }}
.est-llamar        {{ background:#FFF7ED; color:#C2410C; border-radius:4px; padding:3px 8px; font-size:0.75rem; font-weight:600; }}
.est-llamarcliente {{ background:#FFF1F2; color:#BE123C; border-radius:4px; padding:3px 8px; font-size:0.75rem; font-weight:600; }}
@media (prefers-color-scheme: dark) {{
  .est-busqueda      {{ background:#1E3A8A; color:#93C5FD; }}
  .est-encontrado    {{ background:#14532D; color:#86EFAC; }}
  .est-malstock      {{ background:#451A03; color:#FCD34D; }}
  .est-llamar        {{ background:#431407; color:#FDBA74; }}
  .est-llamarcliente {{ background:#4C0519; color:#FDA4AF; }}
}}

/* ── Inputs ── */
[data-testid="stTextInput"] > div > div > input {{
    border-radius: var(--r-sm) !important;
    border-color: var(--border-strong) !important;
    font-size: 0.85rem !important;
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
}}
[data-testid="stTextInput"] > div > div > input:focus {{
    border-color: {AZUL} !important;
    box-shadow: 0 0 0 2px {AZUL}25 !important;
}}

/* ══════════════════════════════════════════
   TABS (st.tabs)
   ══════════════════════════════════════════ */
[data-testid="stTabs"] > div:first-child {{
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-bottom: none !important;
    border-radius: var(--r-md) var(--r-md) 0 0 !important;
    gap: 2px !important;
    padding: 4px 4px 0 4px !important;
}}
[data-testid="stTabs"] button[role="tab"] {{
    border-radius: var(--r-sm) var(--r-sm) 0 0 !important;
    font-size: 0.87rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    padding: 8px 20px !important;
    border: none !important;
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
    transition: color 0.15s !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{
    color: var(--text-primary) !important;
    background: rgba(0,0,0,0.03) !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {AZUL} !important;
    background: var(--bg-card) !important;
    border-bottom: 2px solid {AZUL} !important;
    font-weight: 700 !important;
}}
[data-testid="stTabs"] > div:last-child {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 0 var(--r-md) var(--r-md) !important;
    padding: 16px 12px 12px 12px !important;
}}

/* ══════════════════════════════════════════
   CADETE — BARRA INFERIOR FIJA
   ══════════════════════════════════════════ */
.cadete-sticky-bar {{
    position: fixed; bottom: 0;
    left: 234px; right: 0; z-index: 900;
    background: var(--bg-card);
    border-top: 2px solid var(--border);
    box-shadow: 0 -4px 24px rgba(0,0,0,0.10);
    padding: 11px 28px;
    display: flex; align-items: center; gap: 14px;
}}
.cadete-sticky-stat {{
    font-size: 0.84rem; font-weight: 600;
    color: var(--text-primary); white-space: nowrap;
}}
.cadete-sticky-bar-bg {{
    flex: 1; height: 8px; border-radius: 4px;
    background: var(--border); overflow: hidden;
}}
.cadete-sticky-bar-fill {{
    height: 8px; border-radius: 4px;
    transition: width 0.4s ease;
}}
.cadete-sticky-pct {{
    font-weight: 800; font-size: 1rem;
    white-space: nowrap; min-width: 44px; text-align: right;
}}
@media (max-width: 768px) {{
    .cadete-sticky-bar {{ left: 0 !important; padding: 10px 16px; }}
}}

/* ── Misc ── */
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
"""


# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

def _cargar_config() -> dict:
    """Lee config.yaml sin caché para siempre tener la versión actualizada."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _guardar_temporal(uploaded_file) -> str:
    sufijo = pathlib.Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=sufijo)
    tmp.write(uploaded_file.read())
    tmp.flush()
    tmp.close()
    return tmp.name


def _excel_a_bytes(df_ruta, df_sin_stock, estados_busqueda) -> bytes:
    from src.exporter import exportar_excel
    df_exp = df_ruta.drop(columns=["_gtin_key", "prioridad"], errors="ignore").copy()
    # Aplicar actualizaciones de estado hechas desde la vista cadete
    for idx, estado in st.session_state.get("estados_cadete", {}).items():
        if idx < len(df_exp) and "Estado de búsqueda" in df_exp.columns:
            df_exp.at[idx, "Estado de búsqueda"] = estado
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        path_tmp = tmp.name
    exportar_excel(path_salida=path_tmp, df_ruta=df_exp,
                   df_sin_stock=df_sin_stock, estados_busqueda=estados_busqueda)
    with open(path_tmp, "rb") as f:
        data = f.read()
    os.unlink(path_tmp)
    return data


def _init_session():
    defaults = {
        "pagina":              "dashboard",
        "historial":           [],
        "ultimo_resultado":    None,
        "stock_por_producto":  {},
        "overrides":           {},
        "df_ruta_editable":    None,
        "vista_planilla":      "pedido",   # "pedido" | "ruta"
        "estados_cadete":      {},         # {row_idx → estado actualizado por el cadete}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _ir_a(pagina: str):
    st.session_state.pagina = pagina


def _agregar_historial(nombre_ped, nombre_stk, filas, sin_cob, excel_bytes, filename):
    n = len(st.session_state.historial) + 1
    st.session_state.historial.insert(0, {
        "id":       f"C{n:03d}",
        "pedidos":  nombre_ped,
        "stock":    nombre_stk,
        "hora":     datetime.now().strftime("%H:%M  %d/%m/%y"),
        "filas":    filas,
        "sin_cob":  sin_cob,
        "bytes":    excel_bytes,
        "filename": filename,
    })


def _aplicar_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza la columna Farmacia según los overrides guardados."""
    df = df.copy()
    for idx, nuevo_nodo in st.session_state.overrides.items():
        if idx < len(df):
            df.at[idx, "Farmacia"] = nuevo_nodo
            # Recalcular estado sugerido según si es remota o no
            zona_nueva = st.session_state.get(f"_zona_override_{idx}", "")
            if "Remota" in zona_nueva:
                df.at[idx, "Estado de búsqueda"] = "Llamar a suc"
    return df


# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════

def _render_sidebar():
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────
        st.markdown(f"""
        <div class="sb-logo">
          <div class="sb-logo-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <rect x="8" y="1" width="4" height="18" rx="1.5" fill="white"/>
              <rect x="1" y="8" width="18" height="4" rx="1.5" fill="white"/>
            </svg>
          </div>
          <div>
            <div class="sb-brand-name">Farmacias Global</div>
            <div class="sb-brand-sub">Stock · Operaciones</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        pagina_actual = st.session_state.pagina

        def _nav_item(key, icon, label):
            if pagina_actual == key:
                st.markdown(
                    f'<div class="nav-active">{icon}&nbsp; {label}</div>',
                    unsafe_allow_html=True)
            else:
                st.button(f"{icon}  {label}", key=f"nav_{key}",
                          use_container_width=True,
                          on_click=_ir_a, args=(key,))

        # ── OPERACIONES
        st.markdown('<div class="sb-section-label">Operaciones</div>', unsafe_allow_html=True)
        _nav_item("dashboard",   "◼", "Dashboard")
        _nav_item("nuevo_cruce", "＋", "Nuevo Cruce")
        _nav_item("historial",   "≡", "Historial")

        # ── CADETE
        st.markdown('<div class="sb-section-label">Trabajo</div>', unsafe_allow_html=True)
        _nav_item("cadete", "→", "Vista Cadete")

        # ── SISTEMA
        st.markdown('<div class="sb-section-label">Sistema</div>', unsafe_allow_html=True)
        _nav_item("configuracion", "◎", "Configuración")
        _nav_item("ayuda",         "?", "Ayuda")

        # ── Estado de sesión ───────────────────────────────
        res = st.session_state.ultimo_resultado
        if res:
            df_r = st.session_state.df_ruta_editable
            enc = sum(1 for v in st.session_state.estados_cadete.values()
                      if v in {"Encontrado", "Mal stock - Resuelto"})
            total = len(df_r) if df_r is not None else 0
            pct   = int(enc / total * 100) if total > 0 else 0
            bar_c = "#059669" if pct == 100 else "#2563EB"
            st.markdown(f"""
            <div style="margin:20px 8px 0 8px;padding:12px 14px;
                        background:rgba(255,255,255,0.05);
                        border:1px solid rgba(255,255,255,0.08);
                        border-radius:8px;">
              <div style="font-size:0.69rem;color:#64748B;letter-spacing:0.8px;
                          text-transform:uppercase;font-weight:700;margin-bottom:8px">
                Sesión activa
              </div>
              <div style="font-size:0.8rem;color:#CBD5E1;font-weight:500;margin-bottom:6px">
                {res.get('filas',0)} filas · {res.get('sin_cob',0)} sin cob.
              </div>
              <div style="background:rgba(255,255,255,0.1);border-radius:4px;height:4px">
                <div style="height:4px;border-radius:4px;width:{max(4,pct)}%;
                            background:{bar_c};transition:width 0.3s"></div>
              </div>
              <div style="font-size:0.72rem;color:#64748B;margin-top:5px">
                Cadete: {enc}/{total} encontrados
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="position:absolute;bottom:14px;left:0;right:0;
                    text-align:center;color:#334155;font-size:0.67rem;padding:0 10px;">
          v1.2 · Global Ecommerce
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  HELPERS — tabla mejorada
# ════════════════════════════════════════════════════════════

def _badge_estado(estado: str) -> str:
    mapa = {
        "Búsqueda":           "eb-busqueda",
        "Encontrado":         "eb-encontrado",
        "Mal stock":          "eb-malstock",
        "Llamar a suc":       "eb-llamarsuc",
        "Mal stock - Resuelto": "eb-resuelto",
        "Llamar cliente":     "eb-llamarcliente",
    }
    cls = mapa.get(estado, "eb-busqueda")
    return f'<span class="est-badge {cls}">{estado}</span>'


def _badge_zona(zona: str) -> str:
    mapa = {
        "Deposito":            "zona-0",
        "NQN Capital":         "zona-1",
        "Centenario/Plottier": "zona-2",
        "Cercana":             "zona-3",
        "Remota":              "zona-4",
    }
    cls = mapa.get(zona, "zona-1")
    return f'<span class="{cls}">{zona}</span>'


def _render_tabla_mejorada(df: pd.DataFrame, filtro: str = ""):
    """Tabla custom agrupada por N° Pedido con badges de estado y zona."""
    if df.empty:
        st.info("No hay filas para mostrar.")
        return

    cols_drop = ["_gtin_key", "prioridad"]
    df_v = df.drop(columns=cols_drop, errors="ignore").copy()

    # Aplicar filtro de texto
    if filtro.strip():
        q = filtro.strip().lower()
        mask = (
            df_v.get("Producto", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | df_v.get("N° Pedido", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | df_v.get("Farmacia", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
        )
        df_v = df_v[mask]
        if df_v.empty:
            st.warning(f"Sin resultados para «{filtro}»")
            return

    # Header
    st.markdown("""
    <div class="tbl-wrap">
    <div class="tbl-hdr">
      <span>Pedido</span>
      <span>Producto</span>
      <span>Farmacia</span>
      <span style="text-align:center">Uds</span>
      <span>Estado</span>
    </div>
    """, unsafe_allow_html=True)

    # Agrupar por pedido
    col_ped = "N° Pedido" if "N° Pedido" in df_v.columns else None
    if col_ped:
        pedidos = df_v[col_ped].unique().tolist()
    else:
        pedidos = [None]

    for ped in pedidos:
        if col_ped and ped is not None and str(ped) not in ("", "nan", "None"):
            df_ped = df_v[df_v[col_ped] == ped]
            n_filas = len(df_ped)
            n_enc = (df_ped.get("Estado de búsqueda", pd.Series()) == "Encontrado").sum()
            st.markdown(
                f'<div class="tbl-group-hdr">'
                f'Pedido #{ped} &nbsp;·&nbsp; {n_filas} producto(s)'
                f'{"&nbsp; ✅ " + str(n_enc) + " encontrado(s)" if n_enc else ""}'
                f'</div>',
                unsafe_allow_html=True)
        else:
            df_ped = df_v

        for _, row in df_ped.iterrows():
            producto  = str(row.get("Producto", ""))[:45]
            variante  = str(row.get("Tipo / Variante", "") or "")
            farmacia  = str(row.get("Farmacia", ""))
            zona      = str(row.get("Zona", ""))
            uds       = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
            estado    = str(row.get("Estado de búsqueda", "Búsqueda"))
            stock_suc = row.get("Stock sucursal", "")
            sosp      = row.get("⚠️ Stock", "") == "⚠️ Verificar"
            sin_cob   = farmacia == "— SIN COBERTURA —"
            row_cls   = "tbl-row sin-cob" if sin_cob else "tbl-row"

            prod_sub = ""
            if variante and variante not in ("nan", "None", ""):
                prod_sub += variante
            if sosp:
                prod_sub += (' · ' if prod_sub else '') + '⚠️ Stock a verificar'
            if stock_suc != "" and not sin_cob:
                prod_sub += f'{" · " if prod_sub else ""}Stock: {stock_suc}'

            st.markdown(f"""
            <div class="{row_cls}">
              <span class="tbl-pedido">{str(row.get("N° Pedido", "")) if not col_ped else ""}</span>
              <span>
                <div class="tbl-prod">{producto}</div>
                {"<div class='tbl-prod-sub'>" + prod_sub + "</div>" if prod_sub else ""}
              </span>
              <span>
                <div class="tbl-farm">{farmacia}</div>
                <div class="tbl-farm-zona">{_badge_zona(zona)}</div>
              </span>
              <span class="tbl-uds">{uds}</span>
              <span>{_badge_estado(estado)}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: DASHBOARD
# ════════════════════════════════════════════════════════════

def _page_dashboard(cfg):
    import calendar

    dias_es = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    meses_es = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    ahora = datetime.now()
    dia_semana = dias_es[ahora.weekday()]
    fecha_fmt  = f"{ahora.day} {meses_es[ahora.month]} {ahora.year}"

    res      = st.session_state.ultimo_resultado
    df_ruta  = st.session_state.df_ruta_editable
    hist     = st.session_state.historial

    # ── Calcular métricas ──────────────────────────────────
    pedidos_unicos  = 0
    filas_planilla  = 0
    sin_cobertura   = 0
    stock_sosp      = 0
    pct_cubierto    = 0
    sucursales_uso: dict = {}

    if res:
        pedidos_unicos = res.get("pedidos_unicos", res.get("pedidos_activos", 0))
        filas_planilla = res.get("filas", 0)
        sin_cobertura  = res.get("sin_cob", 0)

    if df_ruta is not None and not df_ruta.empty:
        stock_sosp = int((df_ruta.get("⚠️ Stock", pd.Series()) == "⚠️ Verificar").sum())
        total_asig = len(df_ruta[df_ruta.get("Farmacia", pd.Series()) != "— SIN COBERTURA —"])
        pct_cubierto = int(total_asig / len(df_ruta) * 100) if len(df_ruta) > 0 else 100
        # Conteo por farmacia
        if "Farmacia" in df_ruta.columns:
            for farm, cnt in df_ruta["Farmacia"].value_counts().items():
                if farm != "— SIN COBERTURA —":
                    sucursales_uso[str(farm)] = int(cnt)

    estados_cadete  = st.session_state.get("estados_cadete", {})
    enc_cadete = sum(1 for v in estados_cadete.values() if v in {"Encontrado","Mal stock - Resuelto"})

    # ── Greeting ──────────────────────────────────────────
    estado_operacion = "Operación activa" if res else "Sin actividad"
    dot_color = VERDE if res else "#94A3B8"
    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px">
      <div>
        <div class="dash-greeting">Buen día, {dia_semana}</div>
        <div class="dash-sub">{fecha_fmt} &nbsp;·&nbsp;
          {"Planilla activa · " + str(filas_planilla) + " filas"
           if res else "Sin planilla generada hoy"}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:7px;
                  background:var(--bg-card);border:1px solid var(--border);
                  border-radius:20px;padding:6px 14px;font-size:0.78rem;
                  font-weight:600;color:var(--text-secondary);margin-top:4px">
        <span style="width:7px;height:7px;border-radius:50%;
                     background:{dot_color};display:inline-block"></span>
        {estado_operacion}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI cards ─────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card kpi-info">
          <span class="kpi-icon">📦</span>
          <div class="kpi-label">Pedidos activos</div>
          <div class="kpi-value">{pedidos_unicos if pedidos_unicos else "—"}</div>
          <div class="kpi-detail">{filas_planilla} líneas en planilla</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        cls = "kpi-crit" if sin_cobertura > 0 else "kpi-ok"
        icn = "🔴" if sin_cobertura > 0 else "✅"
        st.markdown(f"""
        <div class="kpi-card {cls}">
          <span class="kpi-icon">{icn}</span>
          <div class="kpi-label">Sin cobertura</div>
          <div class="kpi-value">{sin_cobertura if res else "—"}</div>
          <div class="kpi-detail">{"Requieren gestión manual" if sin_cobertura > 0 else "Todos cubiertos"}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        cls = "kpi-warn" if stock_sosp > 0 else "kpi-ok"
        icn = "⚠️" if stock_sosp > 0 else "✅"
        st.markdown(f"""
        <div class="kpi-card {cls}">
          <span class="kpi-icon">{icn}</span>
          <div class="kpi-label">Stock a verificar</div>
          <div class="kpi-value">{stock_sosp if res else "—"}</div>
          <div class="kpi-detail">{"Verificar antes de enviar" if stock_sosp > 0 else "Sin alertas"}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        cls = "kpi-ok" if enc_cadete >= filas_planilla > 0 else ("kpi-info" if enc_cadete > 0 else "kpi-info")
        icn = "✅" if (enc_cadete >= filas_planilla > 0) else "🚴"
        st.markdown(f"""
        <div class="kpi-card {cls}">
          <span class="kpi-icon">{icn}</span>
          <div class="kpi-label">Cadete — encontrados</div>
          <div class="kpi-value">{enc_cadete if estados_cadete else "—"}</div>
          <div class="kpi-detail">{"de " + str(filas_planilla) + " asignados" if filas_planilla else "Sin actividad"}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_izq, col_der = st.columns([3, 2])

    with col_izq:
        # ── Progreso de cobertura ──────────────────────────
        if res:
            bar_w = max(4, pct_cubierto)
            color_bar = VERDE if pct_cubierto == 100 else AZUL
            st.markdown(f"""
            <div class="dash-section-title">Estado de cobertura</div>
            <div class="dash-progress-wrap">
              <div class="dash-progress-label">
                {pct_cubierto}% de pedidos con sucursal asignada &nbsp;·&nbsp;
                {sin_cobertura} sin cobertura
              </div>
              <div class="dash-progress-bar-bg">
                <div class="dash-progress-bar" style="width:{bar_w}%;background:{color_bar}"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Progreso cadete ────────────────────────────
            if estados_cadete and filas_planilla > 0:
                pct_cad = int(enc_cadete / filas_planilla * 100)
                st.markdown(f"""
                <div class="dash-progress-wrap">
                  <div class="dash-progress-label">
                    Cadete: {enc_cadete}/{filas_planilla} productos encontrados ({pct_cad}%)
                  </div>
                  <div class="dash-progress-bar-bg">
                    <div class="dash-progress-bar" style="width:{max(4,pct_cad)}%"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Alertas ────────────────────────────────────────
        alertas = []
        if sin_cobertura > 0:
            alertas.append(("crit", "🔴", f"{sin_cobertura} producto(s) sin cobertura — requieren gestión manual"))
        if stock_sosp > 0:
            alertas.append(("warn", "⚠️", f"{stock_sosp} fila(s) con stock sospechoso — verificar con la sucursal"))
        if df_ruta is not None and not df_ruta.empty and "Zona" in df_ruta.columns:
            remotas = df_ruta[df_ruta["Zona"] == "Remota"]
            if not remotas.empty:
                n_r = len(remotas["Farmacia"].unique()) if "Farmacia" in remotas.columns else len(remotas)
                alertas.append(("info", "📞", f"{n_r} sucursal(es) remota(s) — llamar antes de enviar cadete"))
        if not hist:
            alertas.append(("info", "⚡", "No hay planilla generada hoy — hacé clic en Nuevo Cruce para empezar"))

        if alertas:
            st.markdown('<div class="dash-section-title">Alertas</div>', unsafe_allow_html=True)
            for tipo, icon, msg in alertas:
                st.markdown(
                    f'<div class="dash-alert-row dash-alert-{tipo}">{icon}&nbsp; {msg}</div>',
                    unsafe_allow_html=True)

        # ── Acciones rápidas ───────────────────────────────
        st.markdown('<div class="dash-section-title">Acciones rápidas</div>', unsafe_allow_html=True)
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            st.button("⚡  Nuevo Cruce", type="primary", use_container_width=True,
                      on_click=_ir_a, args=("nuevo_cruce",))
        with qa2:
            st.button("🚴  Vista Cadete", use_container_width=True,
                      on_click=_ir_a, args=("cadete",))
        with qa3:
            st.button("📋  Historial", use_container_width=True,
                      on_click=_ir_a, args=("historial",))

    with col_der:
        # ── Sucursales más usadas ──────────────────────────
        if sucursales_uso:
            st.markdown('<div class="dash-section-title">Sucursales más usadas hoy</div>',
                        unsafe_allow_html=True)
            max_cnt = max(sucursales_uso.values()) if sucursales_uso else 1
            top5 = sorted(sucursales_uso.items(), key=lambda x: x[1], reverse=True)[:6]
            for nombre, cnt in top5:
                pct_bar = int(cnt / max_cnt * 100)
                nombre_corto = nombre[:28] + "…" if len(nombre) > 28 else nombre
                st.markdown(f"""
                <div class="dash-suc-row">
                  <span class="dash-suc-name">{nombre_corto}</span>
                  <span class="dash-suc-bar-wrap">
                    <span class="dash-suc-bar" style="width:{pct_bar}%"></span>
                  </span>
                  <span class="dash-suc-cnt">{cnt}</span>
                </div>
                """, unsafe_allow_html=True)

        # ── Último cruce ───────────────────────────────────
        if hist:
            ultimo = hist[0]
            badge_cob = (f'<span style="color:#BE123C;font-weight:700">'
                         f'⚠️ {ultimo["sin_cob"]} sin cobertura</span>'
                         if ultimo["sin_cob"] > 0
                         else '<span style="color:#059669;font-weight:700">✅ Completo</span>')
            st.markdown(f"""
            <div class="dash-section-title">Último cruce generado</div>
            <div class="dash-ultimo-cruce">
              <span class="dash-uc-icon">📁</span>
              <div style="flex:1">
                <div class="dash-uc-name">{ultimo["pedidos"]}</div>
                <div class="dash-uc-meta">{ultimo["hora"]} &nbsp;·&nbsp; {ultimo["filas"]} filas &nbsp;·&nbsp; {badge_cob}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.download_button(
                label="📥  Descargar último Excel",
                data=ultimo["bytes"],
                file_name=ultimo["filename"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ════════════════════════════════════════════════════════════
#  PÁGINA: NUEVO CRUCE
# ════════════════════════════════════════════════════════════

def _page_nuevo_cruce(cfg):
    st.markdown(f"""
    <div class="page-hdr">
      <div>
        <p class="page-title">⚡ Nuevo Cruce de Stock</p>
        <p class="page-sub">Pedidos Ecommerce → Planilla del Cadete</p>
      </div>
      <span class="badge-rosa">Ecommerce · Logística</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Resultado anterior visible ─────────────────────────
    res = st.session_state.ultimo_resultado
    if res:
        sin_cob = res["sin_cob"]
        banner_bg = f"background:linear-gradient(135deg,{AZUL} 0%,{AZUL_OSCURO} 100%)"
        if sin_cob > 0:
            banner_bg = f"background:linear-gradient(135deg,#B45309 0%,#92400E 100%)"
        st.markdown(f"""
        <div class="result-banner" style="{banner_bg}">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div>
              <div style="font-weight:700;font-size:0.95rem;margin-bottom:3px">
                {"⚠️ Cruce con productos sin cobertura" if sin_cob > 0 else "✅ Planilla generada correctamente"}
              </div>
              <div style="opacity:0.8;font-size:0.8rem">{res['hora']} &nbsp;·&nbsp; {res['filename']}</div>
            </div>
            <div style="text-align:right;font-size:0.8rem;opacity:0.85">
              {res['filas']} filas &nbsp;·&nbsp;
              {"<strong>" + str(sin_cob) + " sin cobertura</strong>" if sin_cob > 0 else "Todo cubierto"}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Métricas (4 columnas) ──────────────────────────
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Pedidos únicos",    res.get("pedidos_unicos", res["pedidos_activos"]))
        col_b.metric("Líneas de pedido",  res["pedidos_activos"])
        col_c.metric("Filas en planilla", res["filas"])
        col_d.metric("Sin cobertura",     res["sin_cob"],
                     delta="⚠️ Revisar" if res["sin_cob"] > 0 else None,
                     delta_color="inverse")

        # ── Alerta de stock sospechoso ─────────────────────
        df_editable = st.session_state.df_ruta_editable
        if df_editable is not None and not df_editable.empty:
            n_sosp = (df_editable.get("⚠️ Stock", pd.Series()) == "⚠️ Verificar").sum()
            if n_sosp > 0:
                st.warning(
                    f"⚠️ **{n_sosp} fila(s) con stock sospechoso** — "
                    f"La sucursal asignada tiene más de "
                    f"{cfg['optimizacion'].get('stock_sospechoso_umbral', 200)} unidades. "
                    f"Verificá con la sucursal antes de enviar al cadete."
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Aplicar overrides ──────────────────────────────
        from src.optimizer import ordenar_por_pedido, ordenar_por_ruta
        df_con_overrides = _aplicar_overrides(df_editable) if df_editable is not None \
                           else res.get("df_ruta", pd.DataFrame())

        # ── Cambio manual de sucursal ──────────────────────
        if df_editable is not None and not df_editable.empty:
            with st.expander("✏️  Cambiar sucursal asignada (opcional)", expanded=False):
                st.caption("Seleccioná 'Cambiar' en cualquier fila para elegir una sucursal diferente.")

                mapa_stk      = st.session_state.get("mapa_stock_guardado", {})
                col_nodo_stk  = mapa_stk.get("nodo",  "nodo")
                col_stock_stk = mapa_stk.get("stock", "stock")

                for idx, row in df_editable.iterrows():
                    if row.get("Farmacia", "") == "— SIN COBERTURA —":
                        continue

                    gtin_key        = row.get("_gtin_key", "")
                    override_actual = st.session_state.overrides.get(idx)
                    farmacia_actual = override_actual if override_actual else row["Farmacia"]
                    nro_ped         = row.get("N° Pedido", "")
                    sosp_flag       = "⚠️ " if row.get("⚠️ Stock") == "⚠️ Verificar" else ""

                    zona_cls = {
                        "Deposito":             "zona-0",
                        "NQN Capital":          "zona-1",
                        "Centenario/Plottier":  "zona-2",
                        "Cercana":              "zona-3",
                        "Remota":               "zona-4",
                    }.get(row.get("Zona", ""), "zona-1")

                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"""
                        <div class="override-row">
                          <span style="color:#888;font-size:0.78rem;width:80px;flex-shrink:0">
                            #{nro_ped}
                          </span>
                          <span class="override-producto">{sosp_flag}{str(row.get('Producto',''))[:35]}</span>
                          <span class="override-sucursal">🏪 {farmacia_actual}</span>
                          <span class="{zona_cls}">{row.get('Zona','')}</span>
                          <span class="override-stock">Stock: {row.get('Stock sucursal',0)}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        if st.button("✏️", key=f"btn_cambiar_{idx}",
                                     use_container_width=True,
                                     help="Cambiar sucursal"):
                            st.session_state[f"editando_{idx}"] = True

                    if st.session_state.get(f"editando_{idx}"):
                        opciones_df = st.session_state.stock_por_producto.get(gtin_key)
                        if opciones_df is not None and col_nodo_stk in opciones_df.columns:
                            from src.optimizer import obtener_opciones_sucursal
                            max_op   = cfg["optimizacion"].get("max_opciones_override", 5)
                            opciones = obtener_opciones_sucursal(
                                df_stock_producto=opciones_df,
                                col_nodo=col_nodo_stk,
                                col_stock=col_stock_stk,
                                zonas_cfg=cfg["zonas"],
                                zona_labels={int(k): v for k, v in cfg.get("zona_labels", {}).items()},
                                max_opciones=max_op,
                            )
                            if opciones:
                                labels   = [o["label"] for o in opciones]
                                zonas_op = {o["label"]: o["zona"] for o in opciones}
                                default_idx = next(
                                    (i for i, o in enumerate(opciones) if o["nodo"] == farmacia_actual), 0
                                )
                                col_sel, col_ok, col_cancel = st.columns([4, 1, 1])
                                with col_sel:
                                    seleccion = st.selectbox(
                                        "Sucursal:", options=labels, index=default_idx,
                                        key=f"sel_{idx}", label_visibility="collapsed",
                                    )
                                with col_ok:
                                    if st.button("✅", key=f"ok_{idx}", use_container_width=True,
                                                 help="Aplicar cambio"):
                                        nodo_elegido = opciones[labels.index(seleccion)]["nodo"]
                                        st.session_state.overrides[idx] = nodo_elegido
                                        st.session_state[f"_zona_override_{idx}"] = zonas_op[seleccion]
                                        st.session_state[f"editando_{idx}"] = False
                                with col_cancel:
                                    if st.button("✖", key=f"cancel_{idx}", use_container_width=True,
                                                 help="Cancelar"):
                                        st.session_state[f"editando_{idx}"] = False

        # ── Info overrides ─────────────────────────────────
        if st.session_state.overrides:
            st.info(f"📝 {len(st.session_state.overrides)} cambio(s) manual(es) aplicado(s) — "
                    f"el Excel refleja esos cambios.")

        # ── Botón descarga ─────────────────────────────────
        df_export = ordenar_por_pedido(df_con_overrides)
        excel_dl = _excel_a_bytes(df_export, res["df_sin_stock"], cfg["estados_busqueda"])
        st.download_button(
            label="📥  Descargar Planilla Excel",
            data=excel_dl,
            file_name=res["filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # ── Vista previa con tabs ─────────────────────────
        if not df_con_overrides.empty:
            st.markdown('<p class="sec-label">📋 Planilla Cadete</p>', unsafe_allow_html=True)
            col_flt, _ = st.columns([2, 3])
            with col_flt:
                filtro_txt = st.text_input(
                    "Buscar", placeholder="🔍 Filtrar por pedido, producto o farmacia…",
                    label_visibility="collapsed", key="filtro_tabla")

            tab_ped, tab_ruta = st.tabs(["📦  Por pedido", "🗺️  Ruta cadete"])
            with tab_ped:
                st.caption("📦 **Por pedido:** todos los productos del mismo N° pedido juntos. "
                           "Útil para verificar que un pedido queda completo.")
                _render_tabla_mejorada(ordenar_por_pedido(df_con_overrides), filtro=filtro_txt)
            with tab_ruta:
                st.caption("🗺️ **Ruta cadete:** agrupado por sucursal para minimizar paradas.")
                _render_tabla_mejorada(ordenar_por_ruta(df_con_overrides), filtro=filtro_txt)

        if not res["df_sin_stock"].empty:
            st.markdown('<p class="sec-label">⚠️ Productos sin cobertura</p>',
                        unsafe_allow_html=True)
            st.dataframe(res["df_sin_stock"], use_container_width=True)

        st.divider()
        st.markdown('<p class="sec-label">🔄 Ejecutar nuevo cruce</p>',
                    unsafe_allow_html=True)

    # ── Carga de archivos ──────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="upload-zone">
          <div class="upload-zone-title">📋 Archivo de Pedidos</div>
          <div class="upload-zone-sub">Exportá los pedidos con estado <em>Abierta</em><br>.xlsx o .csv</div>
        </div>
        """, unsafe_allow_html=True)
        archivo_pedidos = st.file_uploader("Pedidos", type=["xlsx","xls","csv","txt"],
                                           label_visibility="collapsed", key="up_pedidos")
        if archivo_pedidos:
            st.success(f"✅ {archivo_pedidos.name}")

    with col2:
        st.markdown("""
        <div class="upload-zone">
          <div class="upload-zone-title">🏪 Stock de Sucursales</div>
          <div class="upload-zone-sub">Exportá desde la base de datos<br>.xlsx o .csv</div>
        </div>
        """, unsafe_allow_html=True)
        archivo_stock = st.file_uploader("Stock", type=["xlsx","xls","csv","txt"],
                                         label_visibility="collapsed", key="up_stock")
        if archivo_stock:
            st.success(f"✅ {archivo_stock.name}")

    # Vista previa colapsada
    if archivo_pedidos or archivo_stock:
        with st.expander("👁️  Ver vista previa de los archivos"):
            if archivo_pedidos:
                archivo_pedidos.seek(0)
                try:
                    ext = pathlib.Path(archivo_pedidos.name).suffix.lower()
                    df_p = pd.read_excel(archivo_pedidos) if ext in (".xlsx",".xls") \
                           else pd.read_csv(archivo_pedidos, sep=None, engine="python", dtype=str)
                    st.caption("Pedidos — primeras 5 filas")
                    st.dataframe(df_p.head(5), use_container_width=True)
                    archivo_pedidos.seek(0)
                except Exception as e:
                    st.warning(f"No se pudo previsualizar: {e}")
            if archivo_stock:
                archivo_stock.seek(0)
                try:
                    ext = pathlib.Path(archivo_stock.name).suffix.lower()
                    df_s = pd.read_excel(archivo_stock) if ext in (".xlsx",".xls") \
                           else pd.read_csv(archivo_stock, sep=None, engine="python", dtype=str)
                    st.caption("Stock — primeras 5 filas")
                    st.dataframe(df_s.head(5), use_container_width=True)
                    archivo_stock.seek(0)
                except Exception as e:
                    st.warning(f"No se pudo previsualizar: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    if archivo_pedidos is None or archivo_stock is None:
        st.info("⬆️  Cargá los dos archivos para habilitar la generación.")
        return

    if not st.button("⚡  GENERAR PLANILLA DEL CADETE", type="primary",
                     use_container_width=True):
        return

    # ── Pipeline ───────────────────────────────────────────
    from src.logger import limpiar_log, get_log_records
    from src.loader import cargar_archivo
    from src.matcher import mapear_columnas_pedidos, mapear_columnas_stock
    from src.optimizer import construir_planilla

    limpiar_log()
    barra = st.progress(0, text="Iniciando...")

    try:
        barra.progress(10, text="Leyendo archivos...")
        archivo_pedidos.seek(0); archivo_stock.seek(0)
        df_pedidos = cargar_archivo(_guardar_temporal(archivo_pedidos))
        df_stock   = cargar_archivo(_guardar_temporal(archivo_stock))

        barra.progress(30, text="Identificando columnas...")
        mapa_pedidos = mapear_columnas_pedidos(df_pedidos, cfg)
        mapa_stock   = mapear_columnas_stock(df_stock, cfg)

        barra.progress(60, text="Cruzando stock y optimizando sucursales...")
        df_ruta, df_sin_stock, stock_por_producto = construir_planilla(
            df_pedidos=df_pedidos, df_stock=df_stock,
            mapa_pedidos=mapa_pedidos, mapa_stock=mapa_stock, cfg=cfg,
        )

        barra.progress(85, text="Generando Excel...")
        excel_bytes = _excel_a_bytes(df_ruta, df_sin_stock, cfg["estados_busqueda"])
        barra.progress(100, text="¡Listo!")

    except Exception as e:
        barra.empty()
        st.error(f"❌ Error: {e}")
        with st.expander("Ver detalle técnico"):
            import traceback; st.code(traceback.format_exc())
        return

    barra.empty()

    df_activos_tmp = df_pedidos[
        df_pedidos[mapa_pedidos["estado"]]
        .apply(lambda v: str(v).strip().lower()) == cfg["pedidos"]["estado_activo"].lower()
    ]
    pedidos_activos = len(df_activos_tmp)
    col_nro = mapa_pedidos.get("nro_pedido")
    pedidos_unicos = int(df_activos_tmp[col_nro].nunique()) if col_nro else pedidos_activos

    filename = f"planilla_cadete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Guardar en session_state
    st.session_state.ultimo_resultado = {
        "hora":            datetime.now().strftime("%H:%M  %d/%m/%y"),
        "pedidos_unicos":  pedidos_unicos,
        "pedidos_activos": pedidos_activos,
        "filas":           len(df_ruta),
        "sin_cob":         len(df_sin_stock),
        "df_sin_stock":    df_sin_stock,
        "df_ruta":         df_ruta,
        "filename":        filename,
    }
    st.session_state.df_ruta_editable    = df_ruta.copy()
    st.session_state.stock_por_producto  = stock_por_producto
    st.session_state.mapa_stock_guardado = mapa_stock
    st.session_state.overrides           = {}  # limpiar overrides del cruce anterior

    _agregar_historial(archivo_pedidos.name, archivo_stock.name,
                       len(df_ruta), len(df_sin_stock), excel_bytes, filename)

    # Advertencias
    registros = get_log_records()
    warns = [r for r in registros if r["nivel"] in ("WARNING","ERROR")]
    if warns:
        with st.expander(f"⚠️ {len(warns)} advertencia(s) durante el proceso"):
            for r in warns:
                st.markdown(f"<span style='font-size:0.83rem'>**{r['nivel']}** "
                            f"`{r['timestamp']}` — {r['mensaje']}</span>",
                            unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: HISTORIAL
# ════════════════════════════════════════════════════════════

def _page_historial():
    n = len(st.session_state.historial)
    st.markdown(f"""
    <div class="page-hdr">
      <div>
        <p class="page-title">📋 Historial de Cruces</p>
        <p class="page-sub">Planillas generadas en esta sesión</p>
      </div>
      <span class="badge-azul">{n} cruce(s)</span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.historial:
        st.info("Todavía no generaste ningún cruce en esta sesión.")
        return

    st.markdown(f"""
    <div class="hist-hdr">
      <span class="hc-id">ID</span>
      <span class="hc-name">Archivos procesados</span>
      <span class="hc-hora">Hora</span>
      <span class="hc-stat">Resultados</span>
      <span class="hc-dl">Descargar</span>
    </div>
    """, unsafe_allow_html=True)

    for item in st.session_state.historial:
        badge = (f'<span style="background:#FFF3E0;color:#E65100;border-radius:10px;'
                 f'padding:2px 8px;font-size:0.75rem;">⚠️ {item["sin_cob"]} sin cob.</span>'
                 if item["sin_cob"] > 0
                 else '<span style="background:#F0FDF4;color:#059669;border-radius:10px;'
                      'padding:2px 8px;font-size:0.75rem;">✅ Completo</span>')

        st.markdown(f"""
        <div class="hist-row">
          <span class="hc-id">{item["id"]}</span>
          <span class="hc-name">
            <strong style="color:var(--text-primary)">{item["pedidos"]}</strong><br>
            <span style="color:#999;font-size:0.78rem">{item["stock"]}</span>
          </span>
          <span class="hc-hora">{item["hora"]}</span>
          <span class="hc-stat"><strong>{item["filas"]}</strong> filas &nbsp; {badge}</span>
          <span class="hc-dl"></span>
        </div>
        """, unsafe_allow_html=True)

        _, col_dl = st.columns([6, 1])
        with col_dl:
            st.download_button("📥", data=item["bytes"], file_name=item["filename"],
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key=f"dl_{item['id']}", help=item["filename"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Guardar / restaurar sesión ─────────────────────────
    st.markdown('<p class="sec-label">💾 Guardar sesión</p>', unsafe_allow_html=True)
    st.caption("Guardá la sesión actual para continuar mañana o en otro dispositivo.")

    col_exp, col_imp, col_del = st.columns([2, 2, 1])

    with col_exp:
        import json, base64
        session_data: dict = {"historial": [], "estados_cadete": st.session_state.estados_cadete}
        for item in st.session_state.historial:
            entry = {k: v for k, v in item.items() if k != "bytes"}
            entry["bytes_b64"] = base64.b64encode(item["bytes"]).decode()
            session_data["historial"].append(entry)
        if st.session_state.df_ruta_editable is not None:
            session_data["df_ruta"] = st.session_state.df_ruta_editable.to_json(orient="records", force_ascii=False)
        json_bytes = json.dumps(session_data, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="💾  Exportar sesión (.json)",
            data=json_bytes,
            file_name=f"sesion_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_imp:
        archivo_sesion = st.file_uploader("Restaurar sesión", type=["json"],
                                          label_visibility="collapsed",
                                          key="up_sesion")
        if archivo_sesion:
            try:
                import json, base64
                data = json.loads(archivo_sesion.read().decode("utf-8"))
                st.session_state.historial = []
                for entry in data.get("historial", []):
                    e = {k: v for k, v in entry.items() if k != "bytes_b64"}
                    e["bytes"] = base64.b64decode(entry["bytes_b64"])
                    st.session_state.historial.append(e)
                st.session_state.estados_cadete = data.get("estados_cadete", {})
                if "df_ruta" in data:
                    df_rest = pd.read_json(data["df_ruta"], orient="records")
                    st.session_state.df_ruta_editable = df_rest
                    if not df_rest.empty:
                        st.session_state.ultimo_resultado = {
                            "hora": st.session_state.historial[0]["hora"] if st.session_state.historial else "—",
                            "pedidos_unicos":  "—",
                            "pedidos_activos": "—",
                            "filas":           len(df_rest),
                            "sin_cob":         0,
                            "df_sin_stock":    pd.DataFrame(),
                            "df_ruta":         df_rest,
                            "filename":        st.session_state.historial[0]["filename"] if st.session_state.historial else "planilla.xlsx",
                        }
                st.success("✅ Sesión restaurada")
            except Exception as e:
                st.error(f"Error al restaurar: {e}")

    with col_del:
        if st.button("🗑️", use_container_width=True, help="Limpiar historial"):
            st.session_state.historial = []
            st.session_state.ultimo_resultado = None
            st.session_state.overrides = {}
            st.session_state.estados_cadete = {}


# ════════════════════════════════════════════════════════════
#  PÁGINA: CONFIGURACIÓN
# ════════════════════════════════════════════════════════════

def _page_configuracion(cfg):
    st.markdown("""
    <div class="page-hdr">
      <div>
        <p class="page-title">⚙️ Configuración</p>
        <p class="page-sub">Parámetros actuales del sistema</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("Para modificar la configuración, editá el archivo **config.yaml** en la carpeta del proyecto.")

    labels = {int(k): v for k, v in cfg.get("zona_labels", {}).items()}
    zona_clases = ["zona-0", "zona-1", "zona-2", "zona-3", "zona-4"]

    col1, col2 = st.columns(2)
    with col1:
        keys_prioridad = [
            ("prioridad_0_deposito",         0),
            ("prioridad_1_nqn_capital",       1),
            ("prioridad_2_centenario_plottier", 2),
        ]
        for key, p in keys_prioridad:
            label = labels.get(p, f"Prioridad {p}")
            cls   = zona_clases[p]
            st.markdown(f'<div class="cfg-card"><div class="cfg-card-title">'
                        f'<span class="{cls}">{p}</span> &nbsp; {label}</div>',
                        unsafe_allow_html=True)
            for frag in cfg["zonas"].get(key, []):
                st.markdown(f"&nbsp;&nbsp;• `{frag}`")
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        keys_prioridad2 = [
            ("prioridad_3_cercanas",  3),
            ("prioridad_4_remotas",   4),
        ]
        for key, p in keys_prioridad2:
            label = labels.get(p, f"Prioridad {p}")
            cls   = zona_clases[p]
            st.markdown(f'<div class="cfg-card"><div class="cfg-card-title">'
                        f'<span class="{cls}">{p}</span> &nbsp; {label}</div>',
                        unsafe_allow_html=True)
            for frag in cfg["zonas"].get(key, []):
                st.markdown(f"&nbsp;&nbsp;• `{frag}`")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cfg-card"><div class="cfg-card-title">⚡ Reglas</div>',
                    unsafe_allow_html=True)
        opt = cfg["optimizacion"]
        st.markdown(f"&nbsp;&nbsp;• Máx. sucursales por producto: **{opt['max_sucursales_por_producto']}**")
        st.markdown(f"&nbsp;&nbsp;• Opciones en selector manual: **{opt.get('max_opciones_override', 5)}**")
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: AYUDA
# ════════════════════════════════════════════════════════════

def _page_ayuda():
    st.markdown("""
    <div class="page-hdr">
      <div>
        <p class="page-title">❓ Guía de uso</p>
        <p class="page-sub">Instrucciones para el operador</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Paso a paso ──────────────────────────────────────────
    pasos = [
        ("Exportá el archivo de pedidos desde Batitienda",
         "Ingresá al panel de Batitienda → <strong>Pedidos</strong> → filtrá por estado "
         "<strong>Abierta</strong> → exportá en formato <strong>.xlsx</strong> o <strong>.csv</strong>. "
         "El sistema detecta automáticamente las columnas aunque cambien de posición o nombre."),
        ("Exportá el stock de sucursales desde Zetti",
         "Desde la base de datos ejecutá la consulta de stock por nodo. "
         "El archivo debe tener las columnas de <strong>ID/GTIN</strong>, <strong>SKU</strong>, "
         "<strong>Nodo (sucursal)</strong> y <strong>Stock</strong>. "
         "Exportá en <strong>.xlsx</strong> o <strong>.csv</strong>."),
        ("Cargá los dos archivos en la aplicación",
         "En <strong>⚡ Nuevo Cruce</strong>, arrastrá o seleccioná el archivo de pedidos en la "
         "zona izquierda y el de stock en la derecha. "
         "Podés previsualizar las primeras filas con <em>👁️ Ver vista previa de los archivos</em> "
         "para verificar que el sistema los leyó correctamente."),
        ("Generá la planilla",
         "Hacé clic en <strong>GENERAR PLANILLA DEL CADETE</strong>. "
         "El sistema cruza cada pedido con el stock disponible y asigna la sucursal más conveniente "
         "según el orden de prioridad:<br>"
         "&nbsp;&nbsp;🔵 Depósito ecommerce → 🟢 NQN Capital → 🟡 Centenario/Plottier "
         "→ 🟠 Cercanas → 🔴 Remotas.<br>"
         "Si un producto no tiene stock en ninguna sucursal queda en la pestaña "
         "<strong>Sin Cobertura</strong>."),
        ("Revisá las alertas de stock sospechoso",
         "Si aparece un aviso <strong>⚠️ Stock sospechoso</strong> en amarillo, significa que "
         "una o más sucursales tienen una cantidad inusualmente alta (más de 200 unidades). "
         "Verificá con la sucursal antes de enviar al cadete — puede ser un error de carga en Zetti."),
        ("Elegí la vista que más te sirva",
         "<strong>📦 Por pedido</strong>: todos los productos del mismo N° de pedido aparecen juntos. "
         "Útil para verificar que un pedido queda completo.<br>"
         "<strong>🗺️ Ruta cadete</strong>: agrupa por sucursal para minimizar las paradas. "
         "El cadete va a una farmacia y busca todo lo que necesita ahí antes de pasar a la siguiente."),
        ("Cambiá la sucursal asignada si es necesario",
         "Abrí <strong>✏️ Cambiar sucursal asignada</strong> para ver las 5 mejores opciones "
         "por producto (con stock y zona). Hacé clic en ✏️ en la fila que querés cambiar, "
         "elegí la sucursal con el selector y confirmá con ✅. "
         "El contador de cambios se muestra debajo. El Excel descargado refleja siempre los cambios."),
        ("Descargá el Excel y compartilo con el cadete",
         "El botón <strong>📥 Descargar Planilla Excel</strong> genera el archivo con 3 pestañas:<br>"
         "• <strong>Planilla Cadete</strong>: filas con farmacia asignada y dropdown de estado.<br>"
         "• <strong>Sin Cobertura</strong>: productos sin stock para gestionar por separado.<br>"
         "• <strong>Log</strong>: registro técnico del proceso para auditoría.<br>"
         "El cadete actualiza el estado de cada fila desde el dropdown mientras trabaja."),
    ]

    for i, (titulo, desc) in enumerate(pasos, 1):
        st.markdown(f"""
        <div class="help-step">
          <div class="help-num">{i}</div>
          <div class="help-body">
            <strong>{titulo}</strong>
            <p>{desc}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Referencia rápida ────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="cfg-card">
          <div class="cfg-card-title">Prioridad de sucursales</div>
          <p style="font-size:0.85rem;margin:0 0 6px 0">El sistema asigna siempre la sucursal de mayor
          prioridad que tenga stock suficiente.</p>
          <div style="display:flex;flex-direction:column;gap:5px;font-size:0.84rem">
            <span><span class="zona-0">0 · Depósito</span> &nbsp; APT-ECOMMERCE-NQN (primero siempre)</span>
            <span><span class="zona-1">1 · NQN Capital</span> &nbsp; Todas las sucursales de Neuquén centro</span>
            <span><span class="zona-2">2 · Centenario / Plottier</span> &nbsp; Segunda zona</span>
            <span><span class="zona-3">3 · Cercanas</span> &nbsp; Añelo, El Chañar</span>
            <span><span class="zona-4">4 · Remotas</span> &nbsp; Cutral Co, Zapala, Madryn → llamado</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="cfg-card">
          <div class="cfg-card-title">Estados del dropdown en el Excel</div>
          <p style="font-size:0.85rem;margin:0 0 6px 0">El cadete actualiza el estado de cada fila
          durante la búsqueda.</p>
          <div style="display:flex;flex-direction:column;gap:5px;font-size:0.84rem">
            <span>🔵 <strong>Búsqueda</strong> — estado inicial, producto por buscar</span>
            <span>✅ <strong>Encontrado</strong> — el cadete lo encontró y retiró</span>
            <span>🟡 <strong>Mal stock</strong> — la sucursal no tenía lo indicado</span>
            <span>📞 <strong>Llamar a suc</strong> — sucursal remota, llamar antes de ir</span>
            <span>🟡 <strong>Mal stock - Resuelto</strong> — se buscó en otra sucursal</span>
            <span>🔴 <strong>Llamar cliente</strong> — sin stock, hay que avisar al cliente</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Preguntas frecuentes ─────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec-label">❓ Preguntas frecuentes</p>', unsafe_allow_html=True)

    faqs = [
        ("¿Qué pasa si un producto tiene múltiples GTIN?",
         "Si la columna GTIN del pedido contiene varios códigos separados por coma, "
         "el sistema los verifica todos contra el stock y usa el primer match que encuentre."),
        ("¿Por qué aparece ⚠️ en la columna Stock?",
         "Cuando una sucursal tiene más de 200 unidades de un producto, el sistema lo marca "
         "como stock sospechoso. Puede ser un error de carga en Zetti. "
         "El umbral se puede ajustar en config.yaml → optimizacion.stock_sospechoso_umbral."),
        ("¿Cuándo usar 'Ruta cadete' vs 'Por pedido'?",
         "Usá <strong>Ruta cadete</strong> cuando ya confirmaste todos los pedidos y el cadete "
         "está por salir — minimiza las paradas. "
         "Usá <strong>Por pedido</strong> para verificar que cada pedido queda completo "
         "o para buscar un pedido específico en la planilla."),
        ("¿Qué significan los productos en 'Sin Cobertura'?",
         "Son productos que no se encontraron en el archivo de stock (sin match de GTIN/SKU) "
         "o que tienen stock 0 en todas las sucursales. "
         "Hay que gestionarlos manualmente o avisar al cliente."),
        ("¿Se puede reutilizar el mismo cruce?",
         "Sí. Los cruces del día quedan en el <strong>📋 Historial</strong> durante la sesión. "
         "Podés descargar cualquier cruce anterior desde ahí. "
         "Al cerrar el navegador se pierde el historial."),
    ]

    for preg, resp in faqs:
        with st.expander(preg):
            st.markdown(f"<span style='font-size:0.87rem'>{resp}</span>",
                        unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: VISTA CADETE
# ════════════════════════════════════════════════════════════

def _page_cadete(cfg):
    st.markdown("""
    <div class="page-hdr">
      <div>
        <p class="page-title">🚴 Vista Cadete</p>
        <p class="page-sub">Checklist de búsqueda — marcá cada producto mientras lo encontrás</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    df_ruta = st.session_state.df_ruta_editable
    if df_ruta is None or df_ruta.empty:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px">
          <div style="font-size:3rem;margin-bottom:16px">🚴</div>
          <div style="font-size:1.1rem;font-weight:700;margin-bottom:8px">No hay planilla activa</div>
          <div style="color:var(--text-muted);font-size:0.9rem">
            El operador debe generar un cruce primero desde ⚡ Nuevo Cruce
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("⚡  Ir a Nuevo Cruce", type="primary",
                  use_container_width=True, on_click=_ir_a, args=("nuevo_cruce",))
        return

    from src.optimizer import ordenar_por_ruta
    df = _aplicar_overrides(df_ruta)
    df = ordenar_por_ruta(df)

    estados_opciones = cfg.get("estados_busqueda",
        ["Búsqueda", "Encontrado", "Mal stock", "Llamar a suc",
         "Mal stock - Resuelto", "Llamar cliente"])

    enc_set = {"Encontrado", "Mal stock - Resuelto"}
    estados_actuales = {
        idx: st.session_state.estados_cadete.get(
            idx, str(df.at[idx, "Estado de búsqueda"])
            if "Estado de búsqueda" in df.columns else "Búsqueda")
        for idx in df.index
    }

    farmacias_validas = [f for f in df["Farmacia"].unique()
                         if f != "— SIN COBERTURA —"] if "Farmacia" in df.columns else []
    total = sum(len(df[df["Farmacia"] == f]) for f in farmacias_validas)
    encontrados = sum(1 for idx, v in estados_actuales.items()
                      if v in enc_set and df.at[idx, "Farmacia"] != "— SIN COBERTURA —")
    pct = int(encontrados / total * 100) if total > 0 else 0
    color_pct = VERDE if pct == 100 else (AZUL if pct > 0 else "#888")

    # ── Barra de progreso principal ────────────────────────
    bar_w = max(3, pct)
    st.markdown(f"""
    <div class="cadete-progress-wrap" style="margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span class="cadete-progress-title" style="margin-bottom:0">
          {"✅ ¡Todo listo!" if pct == 100 else f"Progreso del día"}
        </span>
        <span style="font-size:1.6rem;font-weight:800;color:{color_pct}">{pct}%</span>
      </div>
      <div style="background:var(--border-color);border-radius:8px;height:12px;overflow:hidden">
        <div style="height:12px;border-radius:8px;width:{bar_w}%;
             background:linear-gradient(90deg,{AZUL},{VERDE});transition:width 0.4s"></div>
      </div>
      <div style="display:flex;gap:16px;margin-top:8px;font-size:0.82rem;color:var(--text-muted)">
        <span>✅ <strong style="color:{VERDE}">{encontrados}</strong> encontrados</span>
        <span>⏳ <strong>{total - encontrados}</strong> pendientes</span>
        <span>🏪 <strong>{len(farmacias_validas)}</strong> farmacias</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CSS para espacio libre sobre la barra fija ─────────
    st.markdown("<style>.block-container{padding-bottom:72px!important}</style>",
                unsafe_allow_html=True)

    # ── Acciones: descarga y reset ─────────────────────────
    res_data = st.session_state.ultimo_resultado
    col_dl, col_reset = st.columns([5, 1])
    with col_dl:
        if res_data:
            excel_bytes = _excel_a_bytes(df, res_data["df_sin_stock"], estados_opciones)
            st.download_button(
                label="📥  Descargar Excel actualizado",
                data=excel_bytes,
                file_name=res_data.get("filename", "planilla_cadete.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with col_reset:
        if st.button("↩️ Reset", use_container_width=True, help="Resetear todos los estados"):
            st.session_state.estados_cadete = {}

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Farmacias en orden de ruta ─────────────────────────
    todas_farmacias = list(df["Farmacia"].unique()) if "Farmacia" in df.columns else []

    for i_farm, farmacia in enumerate(todas_farmacias):
        df_farm    = df[df["Farmacia"] == farmacia]
        es_sin_cob = farmacia == "— SIN COBERTURA —"
        zona_label = str(df_farm.iloc[0].get("Zona", "")) if not df_farm.empty else ""

        enc_farm   = sum(1 for idx in df_farm.index
                         if estados_actuales.get(idx, "") in enc_set)
        total_farm = len(df_farm)
        farm_lista = (enc_farm >= total_farm) and not es_sin_cob

        zona_cls = {"Deposito":"zona-0","NQN Capital":"zona-1",
                    "Centenario/Plottier":"zona-2","Cercana":"zona-3",
                    "Remota":"zona-4"}.get(zona_label,"zona-1")
        if es_sin_cob:
            zona_cls = "zona-4"

        # Header con color según si está completa
        hdr_bg = "#059669" if farm_lista else ("#BE123C" if es_sin_cob else AZUL)
        check_icon = "✅" if farm_lista else "🏪"
        pct_farm = int(enc_farm / total_farm * 100) if total_farm > 0 else 0

        st.markdown(f"""
        <div class="cadete-farmacia-hdr" style="background:{hdr_bg}">
          {check_icon} &nbsp; {farmacia}
          &nbsp; <span class="{zona_cls}" style="flex-shrink:0">{zona_label}</span>
          <span class="cadete-farmacia-badge">
            {enc_farm}/{total_farm} &nbsp; {pct_farm}%
          </span>
        </div>
        """, unsafe_allow_html=True)

        if es_sin_cob:
            for _, row in df_farm.iterrows():
                prod = str(row.get("Producto", ""))[:55]
                ped  = str(row.get("N° Pedido", "") or "")
                uds  = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
                st.markdown(f"""
                <div class="cadete-item" style="display:flex;justify-content:space-between;align-items:center">
                  <div>
                    <div class="cadete-producto" style="color:#BE123C">{prod}</div>
                    <div class="cadete-meta">
                      {"Pedido: <strong>#" + ped + "</strong> &nbsp;" if ped not in ("","nan","None") else ""}
                      <span class="cadete-qty">× {uds}</span>
                    </div>
                  </div>
                  <span class="est-badge eb-llamarcliente">Llamar cliente</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            continue

        # ── Items de esta farmacia ─────────────────────────
        for idx, row in df_farm.iterrows():
            producto     = str(row.get("Producto", ""))[:55]
            variante     = str(row.get("Tipo / Variante", "") or "")
            nro_ped      = str(row.get("N° Pedido", "") or "")
            cantidad     = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
            sosp         = row.get("⚠️ Stock", "") == "⚠️ Verificar"
            zona_r       = zona_label == "Remota"
            estado_og    = str(row.get("Estado de búsqueda", "Búsqueda"))
            estado_act   = estados_actuales.get(idx, estado_og)
            encontrado   = estado_act in enc_set
            sin_stock_it = estado_act in {"Mal stock", "Llamar cliente"}

            # Fondo según estado
            if encontrado:
                item_bg = "#F0FDF4"
                prod_style = "color:#059669;text-decoration:line-through"
            elif sin_stock_it:
                item_bg = "#FFF8E1"
                prod_style = "color:#B45309"
            else:
                item_bg = "var(--bg-card)"
                prod_style = "color:var(--text-primary)"

            # Alertas inline
            alertas_html = ""
            if sosp:
                alertas_html += '<div style="background:#FFFBEB;border-left:3px solid #D97706;padding:5px 10px;border-radius:5px;font-size:0.77rem;margin-top:6px;color:#92400E;font-weight:500">⚠️ Stock sospechoso — verificar con la sucursal</div>'
            if zona_r:
                alertas_html += '<div style="background:#FFF3E0;border-left:3px solid #E65100;padding:4px 8px;border-radius:4px;font-size:0.78rem;margin-top:4px">📞 Sucursal remota — llamar antes de ir</div>'

            meta_parts = []
            if variante and variante not in ("nan", "None", ""):
                meta_parts.append(variante)
            if nro_ped and nro_ped not in ("", "nan", "None"):
                meta_parts.append(f"Pedido #{nro_ped}")

            st.markdown(f"""
            <div class="cadete-item" style="background:{item_bg}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">
                <div style="flex:1">
                  <div class="cadete-producto" style="{prod_style}">{producto}</div>
                  <div class="cadete-meta" style="margin-top:3px">
                    {(" &nbsp;·&nbsp; ".join(meta_parts) + " &nbsp;") if meta_parts else ""}
                    <span class="cadete-qty">× {cantidad}</span>
                  </div>
                  {alertas_html}
                </div>
                <div style="display:flex;align-items:center;gap:6px;flex-shrink:0">
                  {_badge_estado(estado_act)}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Botones de acción — grandes, táctiles
            if not encontrado:
                b1, b2, b3 = st.columns([3, 2, 2])
                with b1:
                    if st.button("✅  Encontrado", key=f"enc_{idx}",
                                 use_container_width=True, type="primary"):
                        st.session_state.estados_cadete[idx] = "Encontrado"
                with b2:
                    if st.button("✖  Sin stock", key=f"sin_{idx}",
                                 use_container_width=True):
                        st.session_state.estados_cadete[idx] = "Mal stock"
                with b3:
                    if zona_r:
                        if st.button("📞  Llamar", key=f"call_{idx}",
                                     use_container_width=True):
                            st.session_state.estados_cadete[idx] = "Llamar a suc"
                    else:
                        # selector compacto para otros estados
                        default_i = estados_opciones.index(estado_act) \
                            if estado_act in estados_opciones else 0
                        nuevo_est = st.selectbox("", options=estados_opciones,
                            index=default_i, key=f"cad_sel_{idx}",
                            label_visibility="collapsed")
                        if nuevo_est != estado_act:
                            st.session_state.estados_cadete[idx] = nuevo_est
            else:
                # Encontrado → solo botón deshacer
                if st.button("↩️  Deshacer", key=f"undo_{idx}",
                             use_container_width=False):
                    st.session_state.estados_cadete[idx] = "Búsqueda"

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

        # ── Auto-avance: si farmacia completa, mostrar botón destacado ──
        if farm_lista and i_farm < len(todas_farmacias) - 1:
            proxima = todas_farmacias[i_farm + 1]
            if proxima != "— SIN COBERTURA —":
                st.success(f"✅ Farmacia completa — siguiente: **{proxima}**")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Barra inferior fija ────────────────────────────────
    bar_fill  = max(3, pct)
    bar_color = VERDE if pct == 100 else (AZUL if pct > 0 else "#94A3B8")
    icono_bar = "✅" if pct == 100 else "🚴"
    st.markdown(f"""
    <div class="cadete-sticky-bar">
      <span class="cadete-sticky-stat">
        {icono_bar}&nbsp; {encontrados}/{total} productos
      </span>
      <div class="cadete-sticky-bar-bg">
        <div class="cadete-sticky-bar-fill"
             style="width:{bar_fill}%;background:{bar_color}"></div>
      </div>
      <span class="cadete-sticky-pct" style="color:{bar_color}">{pct}%</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init_session()
    cfg = _cargar_config()
    _render_sidebar()

    pagina = st.session_state.pagina
    if   pagina == "dashboard":      _page_dashboard(cfg)
    elif pagina == "nuevo_cruce":    _page_nuevo_cruce(cfg)
    elif pagina == "historial":      _page_historial()
    elif pagina == "cadete":         _page_cadete(cfg)
    elif pagina == "configuracion":  _page_configuracion(cfg)
    elif pagina == "ayuda":          _page_ayuda()


if __name__ == "__main__":
    main()
