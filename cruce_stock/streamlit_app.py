"""
streamlit_app.py
Interfaz web — Farmacias & Perfumerías Global
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

# ── Página ───────────────────────────────────────────────────
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


# ════════════════════════════════════════════════════════════
#  CSS
# ════════════════════════════════════════════════════════════
CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: 'Segoe UI', sans-serif; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {AZUL_OSCURO} 0%, {AZUL} 100%);
    min-width: 220px !important;
    max-width: 220px !important;
}}
section[data-testid="stSidebar"] * {{ color: white !important; }}

.sidebar-logo {{
    text-align: center;
    padding: 24px 16px 8px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    margin-bottom: 16px;
}}
.sidebar-logo-circle {{
    background: white;
    border-radius: 50%;
    width: 52px; height: 52px;
    display: inline-flex;
    align-items: center; justify-content: center;
    font-size: 1.6rem; font-weight: 900;
    color: {AZUL_OSCURO};
    margin-bottom: 8px;
}}
.sidebar-brand {{ font-size: 0.78rem; opacity: 0.85; line-height: 1.3; }}

.nav-item {{
    display: flex; align-items: center; gap: 10px;
    padding: 10px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.92rem;
    font-weight: 500;
    margin: 2px 8px;
    transition: background 0.15s;
    color: rgba(255,255,255,0.88) !important;
    text-decoration: none;
}}
.nav-item:hover {{ background: rgba(255,255,255,0.15); }}
.nav-item.active {{
    background: rgba(255,255,255,0.22);
    color: white !important;
    font-weight: 700;
}}
.nav-section {{
    font-size: 0.68rem;
    opacity: 0.6;
    padding: 12px 16px 4px 16px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Header principal ── */
.page-header {{
    background: white;
    border-bottom: 3px solid {AZUL};
    padding: 18px 28px 14px 28px;
    margin: -24px -24px 24px -24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.page-title {{
    color: {AZUL_OSCURO};
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0;
}}
.page-subtitle {{
    color: #666;
    font-size: 0.85rem;
    margin: 2px 0 0 0;
}}
.badge {{
    background: {ROSA};
    color: white;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 600;
}}

/* ── Cards de upload ── */
.upload-zone {{
    background: {GRIS};
    border: 2px dashed {AZUL};
    border-radius: 10px;
    padding: 18px 16px;
    text-align: center;
    margin-bottom: 4px;
}}
.upload-zone-title {{
    color: {AZUL};
    font-weight: 700;
    font-size: 0.95rem;
}}
.upload-zone-sub {{
    color: #888;
    font-size: 0.8rem;
    margin-top: 4px;
}}

/* ── Botón ejecutar ── */
div[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border: none; border-radius: 8px;
    font-size: 0.98rem; font-weight: 700;
    letter-spacing: 0.4px; padding: 11px 0;
    width: 100%;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{ opacity: 0.87; }}

/* ── Botón descarga ── */
div[data-testid="stDownloadButton"] > button {{
    background: linear-gradient(135deg, {ROSA} 0%, #C41230 100%);
    color: white; border: none; border-radius: 8px;
    font-size: 0.95rem; font-weight: 700;
    padding: 10px 0; width: 100%; cursor: pointer;
}}

/* ── Tabla historial ── */
.hist-header {{
    display: flex; align-items: center;
    background: {AZUL};
    color: white;
    padding: 10px 16px;
    border-radius: 8px 8px 0 0;
    font-weight: 700; font-size: 0.9rem;
    gap: 0;
}}
.hist-row {{
    display: flex; align-items: center;
    padding: 10px 16px;
    border-bottom: 1px solid #e8edf5;
    background: white;
    font-size: 0.88rem;
    gap: 0;
}}
.hist-row:hover {{ background: {GRIS}; }}
.hist-row:last-child {{ border-bottom: none; border-radius: 0 0 8px 8px; }}
.hist-id {{ color: {AZUL}; font-weight: 700; width: 80px; flex-shrink: 0; }}
.hist-name {{ flex: 1; }}
.hist-meta {{ color: #888; font-size: 0.8rem; width: 140px; flex-shrink: 0; }}
.hist-stats {{ width: 180px; flex-shrink: 0; text-align: center; }}
.hist-actions {{ width: 100px; flex-shrink: 0; text-align: right; }}

/* ── Métrica card ── */
div[data-testid="metric-container"] {{
    background: white;
    border: 1px solid #dde4f0;
    border-top: 4px solid {AZUL};
    border-radius: 10px;
    padding: 14px 18px;
}}

/* ── Banner resultado ── */
.result-banner {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border-radius: 10px;
    padding: 16px 24px;
    color: white;
    margin-bottom: 20px;
}}
.result-banner strong {{ font-size: 1.05rem; }}

/* ── Sección label ── */
.sec-label {{
    color: {AZUL_OSCURO};
    font-weight: 700;
    font-size: 0.92rem;
    border-left: 4px solid {ROSA};
    padding-left: 10px;
    margin: 20px 0 10px 0;
}}

/* ── Config card ── */
.cfg-card {{
    background: white;
    border: 1px solid #dde4f0;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}}
.cfg-card-title {{
    color: {AZUL_OSCURO};
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eee;
}}

/* ── Ayuda ── */
.help-step {{
    display: flex; gap: 16px; align-items: flex-start;
    background: white;
    border: 1px solid #dde4f0;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}}
.help-step-num {{
    background: {AZUL};
    color: white;
    border-radius: 50%;
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem;
    flex-shrink: 0;
}}
.help-step-body strong {{ color: {AZUL_OSCURO}; }}
.help-step-body p {{ color: #555; font-size: 0.88rem; margin: 4px 0 0 0; }}

/* ── Estado badges ── */
.badge-ok    {{ background:#E8F5E9; color:#2E7D32; border-radius:12px; padding:2px 10px; font-size:0.8rem; font-weight:600; }}
.badge-warn  {{ background:#FFF3E0; color:#E65100; border-radius:12px; padding:2px 10px; font-size:0.8rem; font-weight:600; }}
.badge-error {{ background:#FFEBEE; color:#C62828; border-radius:12px; padding:2px 10px; font-size:0.8rem; font-weight:600; }}

/* Ocultar decoraciones de Streamlit */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 24px; padding-bottom: 40px; }}
</style>
"""


# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _cargar_config() -> dict:
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        path_tmp = tmp.name
    exportar_excel(
        path_salida=path_tmp,
        df_ruta=df_ruta,
        df_sin_stock=df_sin_stock,
        estados_busqueda=estados_busqueda,
    )
    with open(path_tmp, "rb") as f:
        data = f.read()
    os.unlink(path_tmp)
    return data


def _init_session():
    if "historial" not in st.session_state:
        st.session_state.historial = []        # lista de runs anteriores
    if "ultimo_resultado" not in st.session_state:
        st.session_state.ultimo_resultado = None
    if "pagina" not in st.session_state:
        st.session_state.pagina = "nuevo_cruce"


def _agregar_historial(nombre_ped, nombre_stk, resumen):
    n = len(st.session_state.historial) + 1
    st.session_state.historial.insert(0, {
        "id":        f"C{n:03d}",
        "pedidos":   nombre_ped,
        "stock":     nombre_stk,
        "hora":      datetime.now().strftime("%H:%M  %d/%m/%y"),
        "filas":     resumen["filas_planilla"],
        "sin_cob":   resumen["productos_sin_cobertura"],
        "bytes":     resumen["excel_bytes"],
        "filename":  resumen["filename"],
    })


# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════

def _render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown(f"""
        <div class="sidebar-logo">
          <div class="sidebar-logo-circle">G</div><br>
          <div class="sidebar-brand">
            <strong>Farmacias & Perfumerías</strong><br>GLOBAL
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Menú principal
        st.markdown('<div class="nav-section">OPERACIONES</div>', unsafe_allow_html=True)

        paginas = [
            ("nuevo_cruce",  "⚡",  "Nuevo Cruce"),
            ("historial",    "📋",  "Historial"),
        ]
        for key, icon, label in paginas:
            activo = "active" if st.session_state.pagina == key else ""
            if st.button(f"{icon}  {label}", key=f"nav_{key}",
                         use_container_width=True):
                st.session_state.pagina = key
                st.rerun()

        st.markdown('<div class="nav-section">SISTEMA</div>', unsafe_allow_html=True)

        paginas2 = [
            ("configuracion", "⚙️",  "Configuración"),
            ("ayuda",         "❓",  "Ayuda"),
        ]
        for key, icon, label in paginas2:
            if st.button(f"{icon}  {label}", key=f"nav_{key}",
                         use_container_width=True):
                st.session_state.pagina = key
                st.rerun()

        # Badge de historial
        if st.session_state.historial:
            n = len(st.session_state.historial)
            st.markdown(f"""
            <div style="margin:24px 8px 0 8px; background:rgba(255,255,255,0.12);
                        border-radius:8px; padding:10px 14px; font-size:0.82rem;">
              📊 <strong>{n}</strong> cruce(s) en esta sesión
            </div>
            """, unsafe_allow_html=True)

        # Footer sidebar
        st.markdown("""
        <div style="position:absolute; bottom:16px; left:0; right:0;
                    text-align:center; opacity:0.5; font-size:0.72rem; padding:0 12px;">
          Operaciones Ecommerce · v1.0
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: NUEVO CRUCE
# ════════════════════════════════════════════════════════════

def _page_nuevo_cruce(cfg):

    # Header
    st.markdown(f"""
    <div class="page-header">
      <div>
        <p class="page-title">⚡ Nuevo Cruce de Stock</p>
        <p class="page-subtitle">Pedidos Ecommerce → Planilla del Cadete</p>
      </div>
      <span class="badge">Ecommerce · Logística</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Si ya hay resultado disponible, mostrarlo primero ──
    res = st.session_state.ultimo_resultado
    if res:
        st.markdown(f"""
        <div class="result-banner">
          <strong>✅ Último cruce generado correctamente</strong><br>
          <span style="opacity:0.85; font-size:0.88rem">
            {res['filename']} · {res['hora']}
          </span>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Pedidos activos",   res["pedidos_activos"])
        col_b.metric("Filas en planilla", res["filas"])
        col_c.metric("Sin cobertura",     res["sin_cob"],
                     delta="⚠️ Revisar" if res["sin_cob"] > 0 else None,
                     delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥  Descargar Planilla Excel",
            data=res["bytes"],
            file_name=res["filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        if not res["df_ruta"].empty:
            st.markdown('<p class="sec-label">📋 Vista previa — Planilla Cadete</p>',
                        unsafe_allow_html=True)
            st.dataframe(res["df_ruta"], use_container_width=True, height=260)

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
        archivo_pedidos = st.file_uploader(
            "Pedidos", type=["xlsx","xls","csv","txt"],
            label_visibility="collapsed", key="up_pedidos"
        )
        if archivo_pedidos:
            st.success(f"✅ {archivo_pedidos.name}")

    with col2:
        st.markdown("""
        <div class="upload-zone">
          <div class="upload-zone-title">🏪 Stock de Sucursales</div>
          <div class="upload-zone-sub">Exportá desde la base de datos<br>.xlsx o .csv</div>
        </div>
        """, unsafe_allow_html=True)
        archivo_stock = st.file_uploader(
            "Stock", type=["xlsx","xls","csv","txt"],
            label_visibility="collapsed", key="up_stock"
        )
        if archivo_stock:
            st.success(f"✅ {archivo_stock.name}")

    # Vista previa colapsada
    if archivo_pedidos or archivo_stock:
        with st.expander("👁️  Ver vista previa de los datos cargados"):
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
                    st.warning(f"No se pudo previsualizar pedidos: {e}")

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
                    st.warning(f"No se pudo previsualizar stock: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Botón ejecutar ─────────────────────────────────────
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
        df_ruta, df_sin_stock = construir_planilla(
            df_pedidos=df_pedidos, df_stock=df_stock,
            mapa_pedidos=mapa_pedidos, mapa_stock=mapa_stock, cfg=cfg,
        )

        barra.progress(85, text="Generando Excel...")
        excel_bytes = _excel_a_bytes(df_ruta, df_sin_stock, cfg["estados_busqueda"])
        barra.progress(100, text="¡Listo!")

    except Exception as e:
        barra.empty()
        st.error(f"❌ Error durante el proceso: {e}")
        with st.expander("Ver detalle técnico"):
            import traceback; st.code(traceback.format_exc())
        return

    barra.empty()

    pedidos_activos = len(
        df_pedidos[
            df_pedidos[mapa_pedidos["estado"]]
            .apply(lambda v: str(v).strip().lower()) == cfg["pedidos"]["estado_activo"].lower()
        ]
    )
    filename = f"planilla_cadete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    resultado = {
        "hora":            datetime.now().strftime("%H:%M  %d/%m/%y"),
        "pedidos_activos": pedidos_activos,
        "filas":           len(df_ruta),
        "sin_cob":         len(df_sin_stock),
        "bytes":           excel_bytes,
        "filename":        filename,
        "df_ruta":         df_ruta,
        "df_sin_stock":    df_sin_stock,
    }
    st.session_state.ultimo_resultado = resultado
    _agregar_historial(archivo_pedidos.name, archivo_stock.name, {
        "filas_planilla": len(df_ruta),
        "productos_sin_cobertura": len(df_sin_stock),
        "excel_bytes": excel_bytes,
        "filename": filename,
    })

    # Mostrar advertencias si las hubo
    registros = get_log_records()
    warns = [r for r in registros if r["nivel"] in ("WARNING","ERROR")]
    if warns:
        with st.expander(f"⚠️ {len(warns)} advertencia(s) durante el proceso"):
            for r in warns:
                st.markdown(
                    f"<span style='font-size:0.85rem'>"
                    f"**{r['nivel']}** `{r['timestamp']}` — {r['mensaje']}</span>",
                    unsafe_allow_html=True
                )

    st.rerun()


# ════════════════════════════════════════════════════════════
#  PÁGINA: HISTORIAL
# ════════════════════════════════════════════════════════════

def _page_historial():
    st.markdown(f"""
    <div class="page-header">
      <div>
        <p class="page-title">📋 Historial de Cruces</p>
        <p class="page-subtitle">Planillas generadas en esta sesión</p>
      </div>
      <span class="badge">{len(st.session_state.historial)} cruce(s)</span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.historial:
        st.info("Todavía no generaste ningún cruce en esta sesión. Usá **⚡ Nuevo Cruce** para empezar.")
        return

    # Encabezado tabla
    st.markdown(f"""
    <div class="hist-header">
      <span class="hist-id">ID</span>
      <span class="hist-name">Archivos procesados</span>
      <span class="hist-meta">Hora</span>
      <span class="hist-stats">Resultados</span>
      <span class="hist-actions">Descargar</span>
    </div>
    """, unsafe_allow_html=True)

    for item in st.session_state.historial:
        sin_cob_badge = (
            f'<span class="badge-warn">⚠️ {item["sin_cob"]} sin cob.</span>'
            if item["sin_cob"] > 0
            else '<span class="badge-ok">✅ Completo</span>'
        )
        st.markdown(f"""
        <div class="hist-row">
          <span class="hist-id">{item["id"]}</span>
          <span class="hist-name">
            <strong style="color:{AZUL_OSCURO}">{item["pedidos"]}</strong><br>
            <span style="color:#888;font-size:0.8rem">{item["stock"]}</span>
          </span>
          <span class="hist-meta">{item["hora"]}</span>
          <span class="hist-stats">
            <strong>{item["filas"]}</strong> filas &nbsp; {sin_cob_badge}
          </span>
          <span class="hist-actions"></span>
        </div>
        """, unsafe_allow_html=True)

        # Botón de descarga por fila (Streamlit no permite dentro de HTML)
        col_spacer, col_btn = st.columns([5, 1])
        with col_btn:
            st.download_button(
                label="📥",
                data=item["bytes"],
                file_name=item["filename"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{item['id']}",
                help=f"Descargar {item['filename']}",
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️  Limpiar historial de la sesión", use_container_width=False):
        st.session_state.historial = []
        st.session_state.ultimo_resultado = None
        st.rerun()


# ════════════════════════════════════════════════════════════
#  PÁGINA: CONFIGURACIÓN
# ════════════════════════════════════════════════════════════

def _page_configuracion(cfg):
    st.markdown(f"""
    <div class="page-header">
      <div>
        <p class="page-title">⚙️ Configuración</p>
        <p class="page-subtitle">Parámetros del sistema de cruce</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("Esta es la configuración actual. Para modificarla editá el archivo **config.yaml** en la carpeta del proyecto.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="cfg-card">'
                    '<div class="cfg-card-title">🏪 Sucursales locales (Neuquén Capital)</div>',
                    unsafe_allow_html=True)
        for z in cfg["zonas"]["local"]:
            st.markdown(f"&nbsp;&nbsp;• {z.title()}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cfg-card">'
                    '<div class="cfg-card-title">📞 Sucursales remotas (requieren llamado)</div>',
                    unsafe_allow_html=True)
        for z in cfg["zonas"]["llamar"]:
            st.markdown(f"&nbsp;&nbsp;• {z.title()}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="cfg-card">'
                    '<div class="cfg-card-title">⚡ Reglas de optimización</div>',
                    unsafe_allow_html=True)
        opt = cfg["optimizacion"]
        st.markdown(f"&nbsp;&nbsp;• Priorizar sucursales locales: **{'Sí' if opt['priorizar_local'] else 'No'}**")
        st.markdown(f"&nbsp;&nbsp;• Máx. sucursales por producto: **{opt['max_sucursales_por_producto']}**")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="cfg-card">'
                    '<div class="cfg-card-title">📋 Estados de búsqueda (dropdown cadete)</div>',
                    unsafe_allow_html=True)
        for e in cfg["estados_busqueda"]:
            st.markdown(f"&nbsp;&nbsp;• {e}")
        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  PÁGINA: AYUDA
# ════════════════════════════════════════════════════════════

def _page_ayuda():
    st.markdown(f"""
    <div class="page-header">
      <div>
        <p class="page-title">❓ Guía de uso</p>
        <p class="page-subtitle">Instrucciones para el operador</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    pasos = [
        ("Exportá el archivo de pedidos",
         "Desde el sistema ecommerce, exportá los pedidos del día. "
         "El sistema solo va a procesar los que tengan estado <strong>Abierta</strong>."),
        ("Exportá el stock de sucursales",
         "Desde la base de datos, ejecutá la consulta de stock y exportá el resultado en .csv o .xlsx."),
        ("Cargá los dos archivos",
         "En la sección <strong>Nuevo Cruce</strong>, hacé clic en cada zona de carga "
         "y seleccioná el archivo correspondiente."),
        ("Generá la planilla",
         "Hacé clic en <strong>⚡ GENERAR PLANILLA DEL CADETE</strong>. "
         "El sistema cruza los datos, busca el stock en sucursales y arma la ruta óptima."),
        ("Descargá y compartí el Excel",
         "El archivo tiene 3 pestañas: <strong>Planilla Cadete</strong> (con dropdown de estado), "
         "<strong>Sin Cobertura</strong> y <strong>Log</strong>. "
         "Compartilo con el cadete antes de que salga a buscar los productos."),
    ]

    for i, (titulo, desc) in enumerate(pasos, 1):
        st.markdown(f"""
        <div class="help-step">
          <div class="help-step-num">{i}</div>
          <div class="help-step-body">
            <strong>{titulo}</strong>
            <p>{desc}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Sobre la Planilla Cadete")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Cómo leerla:**
        - Cada fila es una combinación producto → sucursal
        - Si un producto necesita buscarse en 2 sucursales, aparece en 2 filas
        - Las sucursales de Neuquén Capital van siempre primero
        - La columna **"Unidades a buscar"** dice cuánto buscar en cada sucursal
        """)
    with col2:
        st.markdown("""
        **Estados del dropdown:**
        - 🔵 **Búsqueda** — estado inicial al salir
        - ✅ **Encontrado** — el cadete lo encontró
        - 🟡 **Mal stock** — la sucursal no tenía lo que decía
        - 📞 **Llamar a suc** — sucursal fuera de Capital
        - 🔴 **Llamar cliente** — sin stock en ninguna sucursal
        """)


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init_session()
    cfg = _cargar_config()

    _render_sidebar()

    pagina = st.session_state.pagina

    if pagina == "nuevo_cruce":
        _page_nuevo_cruce(cfg)
    elif pagina == "historial":
        _page_historial()
    elif pagina == "configuracion":
        _page_configuracion(cfg)
    elif pagina == "ayuda":
        _page_ayuda()


if __name__ == "__main__":
    main()
