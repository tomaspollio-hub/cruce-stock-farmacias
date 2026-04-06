"""
styles.py
Bloque CSS completo del sistema de diseño.
Importa los tokens de color desde src.ui.tokens para mantener un único
punto de verdad para la paleta.
"""
from src.ui.tokens import (
    AZUL, AZUL_OSCURO,
    ROSA, VERDE, AMARILLO,
)

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
  --bg-main:       #F8FAFC;
  --bg-card:       #FFFFFF;
  --bg-secondary:  #F1F5F9;
  --bg-input:      #FFFFFF;
  --text-primary:  #0F172A;
  --text-secondary:#475569;
  --text-muted:    #94A3B8;
  --border:        #E2E8F0;
  --border-strong: #CBD5E1;
  --shadow-sm:     0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:     0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:     0 10px 25px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.06);
  --r-sm:  6px;
  --r-md:  10px;
  --r-lg:  14px;
  --r-xl:  18px;
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
.sb-section-label {{
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 1.4px; text-transform: uppercase;
    color: #475569 !important;
    padding: 16px 18px 4px 18px;
}}
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
.kpi-icon  {{ font-size: 1.6rem; margin-bottom: 12px; display: block; line-height: 1; }}
.kpi-label {{
    font-size: 0.69rem; font-weight: 700;
    letter-spacing: 0.9px; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 6px;
}}
.kpi-value {{
    font-size: 2.4rem; font-weight: 800;
    color: var(--text-primary); line-height: 1; letter-spacing: -1px;
}}
.kpi-detail {{ font-size: 0.76rem; color: var(--text-muted); margin-top: 6px; font-weight: 400; }}

/* ══════════════════════════════════════════
   DASHBOARD — componentes
   ══════════════════════════════════════════ */
.dash-greeting {{
    font-size: 1.45rem; font-weight: 800;
    color: var(--text-primary); margin-bottom: 2px; letter-spacing: -0.4px;
}}
.dash-sub {{ font-size: 0.84rem; color: var(--text-muted); margin-bottom: 24px; font-weight: 400; }}
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
.dash-suc-bar-wrap {{ width: 72px; background: var(--bg-secondary); border-radius: 4px; height: 5px; }}
.dash-suc-bar  {{ height: 5px; border-radius: 4px; background: {AZUL}; }}
.dash-suc-cnt  {{ width: 22px; text-align: right; font-weight: 700; color: {AZUL}; font-size: 0.8rem; }}
.dash-progress-wrap {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: 14px 18px; margin-bottom: 8px;
}}
.dash-progress-label {{ font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px; font-weight: 500; }}
.dash-progress-bar-bg {{ background: var(--border); border-radius: 6px; height: 8px; overflow: hidden; }}
.dash-progress-bar   {{ height: 8px; border-radius: 6px; background: linear-gradient(90deg, {AZUL}, {VERDE}); }}
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
.upload-zone:hover {{ border-color: {AZUL}; background: {AZUL}06; }}
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
    box-shadow: var(--shadow-sm); margin-top: 8px;
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
    transition: background 0.1s; font-size: 0.84rem;
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
.tbl-uds     {{ font-weight: 800; font-size: 1.05rem; color: {AZUL}; text-align: center; }}

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
    color: var(--text-primary); transition: background 0.1s;
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
.cadete-progress-title {{ font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0; }}
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
    padding: 3px 10px; font-size: 0.75rem; margin-left: auto; font-weight: 600;
}}
.cadete-item {{
    background: var(--bg-card);
    border: 1px solid var(--border); border-top: none;
    padding: 14px 16px;
}}
.cadete-item:last-child {{ border-radius: 0 0 var(--r-md) var(--r-md); }}
.cadete-producto {{ font-weight: 700; color: var(--text-primary); font-size: 0.97rem; line-height: 1.3; }}
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
.cadete-sticky-stat {{ font-size: 0.84rem; font-weight: 600; color: var(--text-primary); white-space: nowrap; }}
.cadete-sticky-bar-bg {{ flex: 1; height: 8px; border-radius: 4px; background: var(--border); overflow: hidden; }}
.cadete-sticky-bar-fill {{ height: 8px; border-radius: 4px; transition: width 0.4s ease; }}
.cadete-sticky-pct {{ font-weight: 800; font-size: 1rem; white-space: nowrap; min-width: 44px; text-align: right; }}
@media (max-width: 768px) {{
    .cadete-sticky-bar {{ left: 0 !important; padding: 10px 16px; }}
}}

/* ══════════════════════════════════════════
   CADETE — TARJETAS OPERATIVAS
   ══════════════════════════════════════════ */
.cadete-variante {{ font-size: 0.8rem; color: var(--text-secondary); margin-top: 2px; font-weight: 400; }}
.cadete-codigos {{
    display: flex; align-items: center; flex-wrap: wrap;
    gap: 6px; margin-top: 5px;
    font-size: 0.75rem; color: var(--text-muted);
}}
.cadete-codigo-chip {{
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px; padding: 1px 7px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.72rem; letter-spacing: 0.2px;
}}
.cadete-alerta-warn {{
    background: #FFFBEB; border-left: 3px solid {AMARILLO};
    border-radius: 4px; padding: 4px 10px;
    font-size: 0.76rem; color: #92400E; font-weight: 500; margin-top: 6px;
}}
.cadete-alerta-info {{
    background: #FFF7ED; border-left: 3px solid #F97316;
    border-radius: 4px; padding: 4px 10px;
    font-size: 0.76rem; color: #C2410C; font-weight: 500; margin-top: 4px;
}}
@media (prefers-color-scheme: dark) {{
  .cadete-alerta-warn {{ background:#451A03; color:#FCD34D; }}
  .cadete-alerta-info {{ background:#431407; color:#FDBA74; }}
  .cadete-codigo-chip {{ background:#1E293B; border-color:#334155; color:#94A3B8; }}
}}
.cadete-item + div[data-testid="stHorizontalBlock"] button,
.cadete-item ~ div div[data-testid="stButton"] > button {{
    min-height: 48px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border-radius: var(--r-md) !important;
    padding: 12px 6px !important;
}}

/* ══════════════════════════════════════════
   SYNC BADGE — indicador cadete activo
   ══════════════════════════════════════════ */
.sync-badge {{
    display: inline-flex; align-items: center; gap: 7px;
    background: {VERDE}14; border: 1px solid {VERDE}30;
    border-radius: var(--r-md); padding: 9px 14px;
    font-size: 0.82rem; font-weight: 500;
    color: var(--text-primary);
}}
.sync-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {VERDE}; flex-shrink: 0;
    animation: pulse-dot 2s infinite;
}}
@keyframes pulse-dot {{
  0%, 100% {{ opacity: 1; }}
  50%       {{ opacity: 0.4; }}
}}

/* ══════════════════════════════════════════
   NODO CARDS — top-5 selector
   ══════════════════════════════════════════ */
.nodo-card {{
    background: var(--bg-card);
    border: 1.5px solid var(--border);
    border-radius: var(--r-md);
    padding: 10px 14px; margin-bottom: 6px;
    display: flex; align-items: center; gap: 12px;
    cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s;
}}
.nodo-card:hover {{ border-color: {AZUL}60; box-shadow: var(--shadow-sm); }}
.nodo-card.nodo-selected {{ border-color: {AZUL}; background: {AZUL}08; }}
.nodo-nombre {{ font-weight: 600; font-size: 0.88rem; flex: 1; color: var(--text-primary); }}
.nodo-stock  {{ font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }}

/* ── Misc ── */
#MainMenu, footer, header {{ visibility: hidden; }}
</style>
"""
