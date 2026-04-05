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

AZUL        = "#1565C0"
AZUL_OSCURO = "#0D47A1"
ROSA        = "#E8194B"
GRIS        = "#F4F7FB"
VERDE       = "#2E7D32"


# ════════════════════════════════════════════════════════════
#  CSS  — adaptable modo claro / oscuro
# ════════════════════════════════════════════════════════════
CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: 'Segoe UI', Arial, sans-serif; }}

/* ══════════════════════════════════════════
   VARIABLES DE COLOR POR MODO
   ══════════════════════════════════════════ */

/* Modo CLARO (default) */
:root {{
  --bg-main:       #FFFFFF;
  --bg-secondary:  #F4F7FB;
  --bg-card:       #FFFFFF;
  --text-primary:  #1A1A2E;
  --text-secondary:#555555;
  --text-muted:    #888888;
  --border-color:  #DDE4F0;
  --metric-bg:     #FFFFFF;
  --expander-bg:   #F4F7FB;
  --hist-row-bg:   #FFFFFF;
  --hist-row-hover:#F4F7FB;
  --upload-bg:     #F4F7FB;
  --page-hdr-bg:   #FFFFFF;
  --cfg-card-bg:   #FFFFFF;
  --help-bg:       #FFFFFF;
  --override-bg:   #FFFFFF;
}}

/* Modo OSCURO */
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg-main:       #0E1117;
    --bg-secondary:  #1A1F2E;
    --bg-card:       #1E2330;
    --text-primary:  #E8EAF0;
    --text-secondary:#AAB0C0;
    --text-muted:    #707888;
    --border-color:  #2D3448;
    --metric-bg:     #1E2330;
    --expander-bg:   #1A1F2E;
    --hist-row-bg:   #1E2330;
    --hist-row-hover:#252B3D;
    --upload-bg:     #1A1F2E;
    --page-hdr-bg:   #1E2330;
    --cfg-card-bg:   #1E2330;
    --help-bg:       #1E2330;
    --override-bg:   #1E2330;
  }}
}}

/* ══════════════════════════════════════════
   FONDO PRINCIPAL
   ══════════════════════════════════════════ */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.main, .main > div, .block-container {{
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}

/* ══════════════════════════════════════════
   SIDEBAR — siempre azul Global, siempre visible
   ══════════════════════════════════════════ */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {AZUL_OSCURO} 0%, {AZUL} 100%) !important;
    min-width: 220px !important;
    max-width: 220px !important;
    transform: none !important;
    visibility: visible !important;
}}
section[data-testid="stSidebar"] > div {{
    background: transparent !important;
}}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] * {{
    color: rgba(255,255,255,0.92) !important;
}}
/* Ocultar botón de colapso — todos los selectores posibles */
button[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
.st-emotion-cache-zq5wmm,
.st-emotion-cache-1wbqy5l,
[class*="collapsedControl"] {{
    display: none !important;
}}

/* ── Logo Global en sidebar ── */
.sb-logo {{
    padding: 22px 16px 14px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.sb-logo-icon {{
    background: white;
    border-radius: 10px;
    width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}}
.sb-logo-icon svg {{ display: block; }}
.sb-brand-text {{ line-height: 1.25; }}
.sb-brand-name  {{ font-size: 0.82rem; font-weight: 700; color: white !important; }}
.sb-brand-sub   {{ font-size: 0.68rem; opacity: 0.7; color: white !important; }}

/* ── Sección label ── */
.sb-section-label {{
    font-size: 0.63rem;
    opacity: 0.5;
    padding: 12px 16px 3px 16px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: white !important;
}}

/* ── Botones nav — estilo Batitienda ── */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.85) !important;
    text-align: left !important;
    padding: 9px 16px !important;
    border-radius: 7px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    margin: 1px 4px !important;
    transition: background 0.15s, opacity 0.15s !important;
    letter-spacing: 0.1px !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
    background: rgba(255,255,255,0.13) !important;
    opacity: 0.9 !important;
    color: white !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:active {{
    background: rgba(255,255,255,0.2) !important;
}}

/* Item activo del sidebar */
.nav-active {{
    display: flex;
    align-items: center;
    background: rgba(255,255,255,0.18);
    border-radius: 7px;
    padding: 9px 16px;
    font-size: 0.88rem;
    font-weight: 700;
    color: white !important;
    margin: 1px 4px;
    cursor: default;
    letter-spacing: 0.1px;
}}

/* ══════════════════════════════════════════
   CONTENIDO PRINCIPAL
   ══════════════════════════════════════════ */

/* Header de página */
.page-hdr {{
    background: var(--page-hdr-bg);
    border-bottom: 3px solid {AZUL};
    padding: 16px 24px 12px 24px;
    margin: -24px -24px 20px -24px;
    display: flex; align-items: center; justify-content: space-between;
}}
.page-title {{ color:{AZUL_OSCURO}; font-size:1.2rem; font-weight:700; margin:0; }}
.page-sub   {{ color:var(--text-muted); font-size:0.82rem; margin:2px 0 0 0; }}

@media (prefers-color-scheme: dark) {{
  .page-title {{ color: #90CAF9 !important; }}
  .page-sub   {{ color: var(--text-muted) !important; }}
}}

.badge-rosa {{
    background:{ROSA}; color:white; border-radius:20px;
    padding:4px 12px; font-size:0.72rem; font-weight:600;
}}
.badge-azul {{
    background:{AZUL}; color:white; border-radius:20px;
    padding:4px 12px; font-size:0.72rem; font-weight:600;
}}

/* Upload zones */
.upload-zone {{
    background: var(--upload-bg);
    border: 2px dashed {AZUL};
    border-radius: 10px; padding: 16px; text-align: center; margin-bottom: 4px;
}}
.upload-zone-title {{ color:{AZUL}; font-weight:700; font-size:0.9rem; }}
.upload-zone-sub   {{ color:var(--text-muted); font-size:0.78rem; margin-top:4px; }}

/* Botón principal */
div[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border:none; border-radius:8px;
    font-size:0.93rem; font-weight:700; letter-spacing:0.3px; padding:11px 0;
    transition: opacity 0.15s !important;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{ opacity:0.85 !important; }}

/* Botón descarga */
div[data-testid="stDownloadButton"] > button {{
    background: linear-gradient(135deg, {ROSA} 0%, #C41230 100%);
    color:white; border:none; border-radius:8px;
    font-size:0.9rem; font-weight:700; padding:10px 0;
    width:100%; cursor:pointer;
    transition: opacity 0.15s;
}}
div[data-testid="stDownloadButton"] > button:hover {{ opacity:0.87; }}

/* Métricas */
div[data-testid="metric-container"] {{
    background: var(--metric-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-top: 4px solid {AZUL} !important;
    border-radius: 10px; padding: 12px 16px;
}}
div[data-testid="metric-container"] label,
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    color: var(--text-primary) !important;
}}

/* Result banner */
.result-banner {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border-radius:10px; padding:14px 22px; color:white; margin-bottom:18px;
}}

/* Section label */
.sec-label {{
    color:{AZUL_OSCURO}; font-weight:700; font-size:0.87rem;
    border-left:4px solid {ROSA}; padding-left:9px; margin:18px 0 8px 0;
}}
@media (prefers-color-scheme: dark) {{
  .sec-label {{ color: #90CAF9 !important; }}
}}

/* Override rows */
.override-row {{
    background: var(--override-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px; padding:10px 14px; margin-bottom:6px;
    display:flex; align-items:center; gap:12px;
}}
.override-producto {{ font-weight:700; color:{AZUL_OSCURO}; flex:1; }}
.override-sucursal  {{ color:var(--text-secondary); font-size:0.87rem; }}
.override-zona      {{ font-size:0.76rem; background:var(--bg-secondary); border-radius:12px; padding:2px 9px; }}
.override-stock     {{ font-size:0.8rem; color:var(--text-muted); }}
@media (prefers-color-scheme: dark) {{
  .override-producto {{ color:#90CAF9 !important; }}
}}

/* Historial */
.hist-hdr {{
    background:{AZUL}; color:white;
    padding:9px 14px; border-radius:8px 8px 0 0;
    font-weight:700; font-size:0.85rem; display:flex;
}}
.hist-row {{
    background: var(--hist-row-bg);
    border-bottom: 1px solid var(--border-color);
    padding:9px 14px; font-size:0.84rem;
    display:flex; align-items:center;
    color: var(--text-primary);
}}
.hist-row:hover {{ background: var(--hist-row-hover); }}
.hist-row:last-child {{ border-bottom:none; border-radius:0 0 8px 8px; }}
.hc-id   {{ width:60px;  flex-shrink:0; color:{AZUL}; font-weight:700; }}
.hc-name {{ flex:1; color: var(--text-primary); }}
.hc-hora {{ width:120px; flex-shrink:0; color:var(--text-muted); font-size:0.77rem; }}
.hc-stat {{ width:160px; flex-shrink:0; text-align:center; }}
.hc-dl   {{ width:80px;  flex-shrink:0; text-align:right; }}

/* Config cards */
.cfg-card {{
    background: var(--cfg-card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px; padding:18px 22px; margin-bottom:14px;
}}
.cfg-card-title {{
    color:{AZUL_OSCURO}; font-weight:700; font-size:0.93rem;
    margin-bottom:10px; padding-bottom:7px;
    border-bottom:1px solid var(--border-color);
}}
@media (prefers-color-scheme: dark) {{
  .cfg-card-title {{ color:#90CAF9 !important; }}
  .cfg-card {{ border-color: var(--border-color) !important; }}
}}

/* Ayuda */
.help-step {{
    display:flex; gap:14px; align-items:flex-start;
    background: var(--help-bg);
    border: 1px solid var(--border-color);
    border-radius:10px; padding:14px 18px; margin-bottom:10px;
}}
.help-num {{
    background:{AZUL}; color:white; border-radius:50%;
    width:30px; height:30px; display:flex; align-items:center;
    justify-content:center; font-weight:700; flex-shrink:0;
}}
.help-body strong {{ color:{AZUL_OSCURO}; }}
.help-body p {{ color:var(--text-secondary); font-size:0.84rem; margin:3px 0 0 0; }}
@media (prefers-color-scheme: dark) {{
  .help-body strong {{ color:#90CAF9 !important; }}
}}

/* Expanders */
[data-testid="stExpander"] {{
    background: var(--expander-bg) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] p {{
    color: var(--text-primary) !important;
}}

/* Zona chips */
.zona-0 {{ background:#E3F2FD; color:{AZUL_OSCURO}; border-radius:12px; padding:2px 9px; font-size:0.76rem; font-weight:600; }}
.zona-1 {{ background:#E8F5E9; color:{VERDE};        border-radius:12px; padding:2px 9px; font-size:0.76rem; font-weight:600; }}
.zona-2 {{ background:#FFF8E1; color:#F57F17;        border-radius:12px; padding:2px 9px; font-size:0.76rem; font-weight:600; }}
.zona-3 {{ background:#FFF3E0; color:#E65100;        border-radius:12px; padding:2px 9px; font-size:0.76rem; font-weight:600; }}
.zona-4 {{ background:#FFEBEE; color:#C62828;        border-radius:12px; padding:2px 9px; font-size:0.76rem; font-weight:600; }}
@media (prefers-color-scheme: dark) {{
  .zona-0 {{ background:#0D2E5A; color:#90CAF9; }}
  .zona-1 {{ background:#0D3320; color:#81C784; }}
  .zona-2 {{ background:#3D2E00; color:#FFD54F; }}
  .zona-3 {{ background:#3D1F00; color:#FFB74D; }}
  .zona-4 {{ background:#3D0A0A; color:#EF9A9A; }}
}}

/* ══════════════════════════════════════════
   VISTA CADETE — diseño móvil
   ══════════════════════════════════════════ */
.cadete-progress-wrap {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;
}}
.cadete-progress-title {{
    font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;
}}
.cadete-farmacia-hdr {{
    background: {AZUL};
    color: white; border-radius: 8px 8px 0 0;
    padding: 10px 16px; font-weight: 700; font-size: 0.95rem;
    margin-top: 16px; display: flex; align-items: center; gap: 10px;
}}
.cadete-farmacia-badge {{
    background: rgba(255,255,255,0.25); border-radius: 10px;
    padding: 2px 9px; font-size: 0.78rem; margin-left: auto;
}}
.cadete-item {{
    background: var(--bg-card);
    border: 1px solid var(--border-color); border-top: none;
    padding: 12px 16px; font-size: 0.9rem;
}}
.cadete-item:last-child {{ border-radius: 0 0 8px 8px; }}
.cadete-producto {{ font-weight: 700; color: var(--text-primary); font-size: 0.95rem; }}
.cadete-meta {{ color: var(--text-muted); font-size: 0.78rem; margin-top: 2px; }}
.cadete-qty {{
    background: {AZUL}; color: white; border-radius: 8px;
    padding: 3px 10px; font-weight: 700; font-size: 0.85rem; display: inline-block;
}}
/* Estado chips en cadete */
.est-busqueda     {{ background:#E3F2FD; color:{AZUL_OSCURO}; border-radius:10px; padding:3px 10px; font-size:0.8rem; font-weight:600; }}
.est-encontrado   {{ background:#E8F5E9; color:{VERDE};        border-radius:10px; padding:3px 10px; font-size:0.8rem; font-weight:600; }}
.est-malstock     {{ background:#FFF8E1; color:#F57F17;        border-radius:10px; padding:3px 10px; font-size:0.8rem; font-weight:600; }}
.est-llamar       {{ background:#FFF3E0; color:#E65100;        border-radius:10px; padding:3px 10px; font-size:0.8rem; font-weight:600; }}
.est-llamarcliente{{ background:#FFEBEE; color:#C62828;        border-radius:10px; padding:3px 10px; font-size:0.8rem; font-weight:600; }}
@media (prefers-color-scheme: dark) {{
  .est-busqueda      {{ background:#0D2E5A; color:#90CAF9; }}
  .est-encontrado    {{ background:#0D3320; color:#81C784; }}
  .est-malstock      {{ background:#3D2E00; color:#FFD54F; }}
  .est-llamar        {{ background:#3D1F00; color:#FFB74D; }}
  .est-llamarcliente {{ background:#3D0A0A; color:#EF9A9A; }}
}}

/* ── Misc ── */
#MainMenu, footer, header {{ visibility:hidden; }}
.block-container {{ padding-top:22px; padding-bottom:36px; }}
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
        "pagina":              "nuevo_cruce",
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
        st.markdown(f"""
        <div class="sb-logo">
          <div class="sb-logo-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <!-- Cruz farmacia -->
              <rect x="11" y="3" width="6" height="22" rx="2" fill="{AZUL}"/>
              <rect x="3" y="11" width="22" height="6" rx="2" fill="{AZUL}"/>
              <!-- G encima -->
              <circle cx="19" cy="19" r="8" fill="{ROSA}"/>
              <text x="19" y="23" text-anchor="middle" font-family="Arial" font-size="9"
                    font-weight="900" fill="white">G</text>
            </svg>
          </div>
          <div class="sb-brand-text">
            <div class="sb-brand-name">Farmacias & Perfumerías</div>
            <div class="sb-brand-sub">GLOBAL · Stock Ecommerce</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        pagina_actual = st.session_state.pagina

        # ── OPERACIONES
        st.markdown('<div class="sb-section-label">OPERACIONES</div>', unsafe_allow_html=True)
        for key, icon, label in [
            ("nuevo_cruce", "⚡", "Nuevo Cruce"),
            ("historial",   "📋", "Historial"),
        ]:
            if pagina_actual == key:
                st.markdown(f'<span class="nav-active">{icon}&nbsp;&nbsp;{label}</span>',
                            unsafe_allow_html=True)
            else:
                st.button(f"{icon}  {label}", key=f"nav_{key}",
                          use_container_width=True,
                          on_click=_ir_a, args=(key,))

        # ── CADETE
        st.markdown('<div class="sb-section-label">CADETE</div>', unsafe_allow_html=True)
        for key, icon, label in [
            ("cadete", "🚴", "Vista Cadete"),
        ]:
            if pagina_actual == key:
                st.markdown(f'<span class="nav-active">{icon}&nbsp;&nbsp;{label}</span>',
                            unsafe_allow_html=True)
            else:
                st.button(f"{icon}  {label}", key=f"nav_{key}",
                          use_container_width=True,
                          on_click=_ir_a, args=(key,))

        # ── SISTEMA
        st.markdown('<div class="sb-section-label">SISTEMA</div>', unsafe_allow_html=True)
        for key, icon, label in [
            ("configuracion", "⚙️",  "Configuración"),
            ("ayuda",         "❓",  "Ayuda"),
        ]:
            if pagina_actual == key:
                st.markdown(f'<span class="nav-active">{icon}&nbsp;&nbsp;{label}</span>',
                            unsafe_allow_html=True)
            else:
                st.button(f"{icon}  {label}", key=f"nav_{key}",
                          use_container_width=True,
                          on_click=_ir_a, args=(key,))

        # Contador de sesión
        if st.session_state.historial:
            n = len(st.session_state.historial)
            st.markdown(f"""
            <div style="margin:20px 6px 0 6px; background:rgba(255,255,255,0.12);
                        border-radius:8px; padding:9px 12px; font-size:0.8rem;">
              📊 <strong>{n}</strong> cruce(s) esta sesión
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="position:absolute;bottom:14px;left:0;right:0;
                    text-align:center;opacity:0.45;font-size:0.7rem;padding:0 10px;">
          Operaciones Ecommerce · v1.1
        </div>
        """, unsafe_allow_html=True)


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
        st.markdown(f"""
        <div class="result-banner">
          <strong>✅ Último cruce generado · {res['hora']}</strong><br>
          <span style="opacity:0.85;font-size:0.86rem">{res['filename']}</span>
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

        # ── Toggle de vista ────────────────────────────────
        st.markdown('<p class="sec-label">👁️ Vista de la planilla</p>', unsafe_allow_html=True)
        col_v1, col_v2, _ = st.columns([1, 1, 3])
        with col_v1:
            if st.button("📦  Por pedido",
                         type="primary" if st.session_state.vista_planilla == "pedido" else "secondary",
                         use_container_width=True,
                         help="Agrupa todos los productos del mismo pedido juntos"):
                st.session_state.vista_planilla = "pedido"
        with col_v2:
            if st.button("🗺️  Ruta cadete",
                         type="primary" if st.session_state.vista_planilla == "ruta" else "secondary",
                         use_container_width=True,
                         help="Agrupa por sucursal para minimizar paradas"):
                st.session_state.vista_planilla = "ruta"

        # ── Aplicar overrides y ordenamiento ──────────────
        from src.optimizer import ordenar_por_pedido, ordenar_por_ruta
        df_con_overrides = _aplicar_overrides(df_editable) if df_editable is not None \
                           else res.get("df_ruta", pd.DataFrame())

        if st.session_state.vista_planilla == "ruta":
            df_final = ordenar_por_ruta(df_con_overrides)
            st.caption("🗺️ **Vista Ruta:** ordenado por sucursal → N° pedido. "
                       "El cadete va a una sucursal y busca todos los productos de una vez.")
        else:
            df_final = ordenar_por_pedido(df_con_overrides)
            st.caption("📦 **Vista Pedido:** ordenado por N° pedido → zona. "
                       "Todos los productos de un mismo pedido aparecen juntos.")

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
        excel_dl = _excel_a_bytes(df_final, res["df_sin_stock"], cfg["estados_busqueda"])
        st.download_button(
            label="📥  Descargar Planilla Excel",
            data=excel_dl,
            file_name=res["filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # ── Vista previa ───────────────────────────────────
        cols_ocultas = ["_gtin_key", "prioridad"]
        df_preview   = df_final.drop(columns=cols_ocultas, errors="ignore")

        if not df_preview.empty:
            st.markdown('<p class="sec-label">📋 Vista previa — Planilla Cadete</p>',
                        unsafe_allow_html=True)
            st.dataframe(df_preview, use_container_width=True, height=280)

        if not res["df_sin_stock"].empty:
            st.markdown('<p class="sec-label">⚠️ Productos sin cobertura en sucursales</p>',
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
                 else '<span style="background:#E8F5E9;color:#2E7D32;border-radius:10px;'
                      'padding:2px 8px;font-size:0.75rem;">✅ Completo</span>')

        st.markdown(f"""
        <div class="hist-row">
          <span class="hc-id">{item["id"]}</span>
          <span class="hc-name">
            <strong style="color:{AZUL_OSCURO}">{item["pedidos"]}</strong><br>
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
        <p class="page-sub">Planilla de búsqueda — actualizar estado en tiempo real</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    df_ruta = st.session_state.df_ruta_editable
    if df_ruta is None or df_ruta.empty:
        st.info("Todavía no generaste ningún cruce. "
                "Andá a ⚡ Nuevo Cruce, cargá los archivos y generá la planilla.")
        return

    from src.optimizer import ordenar_por_ruta
    df = _aplicar_overrides(df_ruta)
    df = ordenar_por_ruta(df)

    estados_opciones = cfg.get("estados_busqueda",
        ["Búsqueda", "Encontrado", "Mal stock", "Llamar a suc",
         "Mal stock - Resuelto", "Llamar cliente"])

    # ── Resumen de progreso ────────────────────────────────
    total   = len(df[df["Farmacia"] != "— SIN COBERTURA —"])
    enc_set = {"Encontrado", "Mal stock - Resuelto"}
    estados_actuales = {
        idx: st.session_state.estados_cadete.get(idx,
              df.at[idx, "Estado de búsqueda"] if "Estado de búsqueda" in df.columns else "Búsqueda")
        for idx in df.index
    }
    encontrados = sum(1 for v in estados_actuales.values() if v in enc_set)
    pct = int(encontrados / total * 100) if total > 0 else 0

    # Conteo por estado
    conteos: dict[str, int] = {}
    for v in estados_actuales.values():
        conteos[v] = conteos.get(v, 0) + 1

    st.markdown(f"""
    <div class="cadete-progress-wrap">
      <div class="cadete-progress-title">
        Progreso: {encontrados} / {total} productos encontrados &nbsp;
        <span style="color:{'#2E7D32' if pct == 100 else '#1565C0'};font-size:1.1rem">
          {pct}%
        </span>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;font-size:0.82rem">
    """, unsafe_allow_html=True)
    for est, cnt in conteos.items():
        st.markdown(
            f'<span style="background:var(--bg-secondary);border:1px solid var(--border-color);'
            f'border-radius:10px;padding:2px 10px">{est}: <strong>{cnt}</strong></span>',
            unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Botón para descargar Excel con estados actualizados
    col_dl, col_reset = st.columns([3, 1])
    with col_dl:
        res = st.session_state.ultimo_resultado
        if res:
            excel_bytes = _excel_a_bytes(df, res["df_sin_stock"], estados_opciones)
            st.download_button(
                label="📥  Descargar Excel con estados actualizados",
                data=excel_bytes,
                file_name=res.get("filename", "planilla_cadete.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with col_reset:
        if st.button("↩️ Resetear", use_container_width=True,
                     help="Volver todos los estados al valor original"):
            st.session_state.estados_cadete = {}

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Agrupar por farmacia ───────────────────────────────
    farmacias = df["Farmacia"].unique().tolist() if "Farmacia" in df.columns else []

    for farmacia in farmacias:
        df_farm = df[df["Farmacia"] == farmacia]
        es_sin_cob = farmacia == "— SIN COBERTURA —"

        # Conteo de encontrados en esta farmacia
        enc_farm = sum(
            1 for idx in df_farm.index
            if estados_actuales.get(idx, "") in enc_set
        )
        total_farm = len(df_farm)
        pct_farm = int(enc_farm / total_farm * 100) if total_farm > 0 else 0

        zona_label = df_farm.iloc[0].get("Zona", "") if not df_farm.empty else ""

        zona_cls = {
            "Deposito":             "zona-0",
            "NQN Capital":          "zona-1",
            "Centenario/Plottier":  "zona-2",
            "Cercana":              "zona-3",
            "Remota":               "zona-4",
        }.get(zona_label, "zona-1") if not es_sin_cob else "zona-4"

        hdr_color = "#C62828" if es_sin_cob else AZUL
        st.markdown(f"""
        <div class="cadete-farmacia-hdr" style="background:{hdr_color}">
          🏪 {farmacia}
          &nbsp;<span class="{zona_cls}">{zona_label}</span>
          <span class="cadete-farmacia-badge">{enc_farm}/{total_farm} ✓ {pct_farm}%</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, row in df_farm.iterrows():
            producto  = str(row.get("Producto", ""))[:50]
            variante  = str(row.get("Tipo / Variante", "") or "")
            nro_ped   = str(row.get("N° Pedido", "") or "")
            cantidad  = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
            sosp      = "⚠️ " if row.get("⚠️ Stock") == "⚠️ Verificar" else ""
            estado_og = str(row.get("Estado de búsqueda", "Búsqueda"))
            estado_actual = st.session_state.estados_cadete.get(idx, estado_og)

            col_info, col_sel = st.columns([3, 2])
            with col_info:
                st.markdown(f"""
                <div class="cadete-item">
                  <div class="cadete-producto">{sosp}{producto}</div>
                  <div class="cadete-meta">
                    {'<span style="color:#888">Variante: ' + variante + '</span> &nbsp;' if variante and variante not in ("nan","None") else ''}
                    {'Pedido: <strong>#' + nro_ped + '</strong> &nbsp;' if nro_ped and nro_ped not in ("nan","None","") else ''}
                    <span class="cadete-qty">× {cantidad}</span>
                    {'&nbsp; <span style="color:#C62828;font-size:0.78rem">Stock a verificar</span>' if sosp else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col_sel:
                if es_sin_cob:
                    st.markdown(
                        f'<div style="padding:10px 0"><span class="est-llamarcliente">'
                        f'Llamar cliente</span></div>',
                        unsafe_allow_html=True)
                else:
                    default_idx = estados_opciones.index(estado_actual) \
                        if estado_actual in estados_opciones else 0
                    nuevo_estado = st.selectbox(
                        "Estado", options=estados_opciones,
                        index=default_idx,
                        key=f"cad_est_{idx}",
                        label_visibility="collapsed",
                    )
                    if nuevo_estado != estado_actual:
                        st.session_state.estados_cadete[idx] = nuevo_estado

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init_session()
    cfg = _cargar_config()
    _render_sidebar()

    pagina = st.session_state.pagina
    if   pagina == "nuevo_cruce":    _page_nuevo_cruce(cfg)
    elif pagina == "historial":      _page_historial()
    elif pagina == "cadete":         _page_cadete(cfg)
    elif pagina == "configuracion":  _page_configuracion(cfg)
    elif pagina == "ayuda":          _page_ayuda()


if __name__ == "__main__":
    main()
