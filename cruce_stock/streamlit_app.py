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
#  CSS
# ════════════════════════════════════════════════════════════
CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: 'Segoe UI', sans-serif; }}

/* ── Sidebar siempre visible ── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {AZUL_OSCURO} 0%, {AZUL} 100%);
    min-width: 230px !important;
    max-width: 230px !important;
}}
section[data-testid="stSidebar"] * {{ color: white !important; }}
/* Ocultar botón de colapso */
button[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}

/* ── Logo sidebar ── */
.sb-logo {{
    text-align: center;
    padding: 20px 12px 12px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.18);
    margin-bottom: 10px;
}}
.sb-logo-circle {{
    background: white;
    border-radius: 50%;
    width: 50px; height: 50px;
    display: inline-flex;
    align-items: center; justify-content: center;
    font-size: 1.5rem; font-weight: 900;
    color: {AZUL_OSCURO};
    margin-bottom: 6px;
}}
.sb-brand {{ font-size: 0.75rem; opacity: 0.85; line-height: 1.3; }}

/* ── Botones de nav en sidebar ── */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.88) !important;
    text-align: left !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    margin: 1px 0 !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
    background: rgba(255,255,255,0.14) !important;
}}

/* Item activo del sidebar */
.nav-active {{
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 0.9rem;
    font-weight: 700;
    color: white;
    margin: 1px 0;
    display: block;
}}
.sb-section-label {{
    font-size: 0.65rem;
    opacity: 0.55;
    padding: 10px 14px 3px 14px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Header de página ── */
.page-hdr {{
    background: white;
    border-bottom: 3px solid {AZUL};
    padding: 16px 24px 12px 24px;
    margin: -24px -24px 20px -24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.page-title {{ color:{AZUL_OSCURO}; font-size:1.25rem; font-weight:700; margin:0; }}
.page-sub   {{ color:#666; font-size:0.82rem; margin:2px 0 0 0; }}
.badge-rosa {{
    background:{ROSA}; color:white; border-radius:20px;
    padding:4px 12px; font-size:0.73rem; font-weight:600;
}}
.badge-azul {{
    background:{AZUL}; color:white; border-radius:20px;
    padding:4px 12px; font-size:0.73rem; font-weight:600;
}}

/* ── Upload zones ── */
.upload-zone {{
    background:{GRIS}; border:2px dashed {AZUL};
    border-radius:10px; padding:16px; text-align:center; margin-bottom:4px;
}}
.upload-zone-title {{ color:{AZUL}; font-weight:700; font-size:0.92rem; }}
.upload-zone-sub   {{ color:#888; font-size:0.78rem; margin-top:4px; }}

/* ── Botón principal ejecutar ── */
div[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border:none; border-radius:8px;
    font-size:0.95rem; font-weight:700;
    letter-spacing:0.3px; padding:11px 0;
}}
div[data-testid="stButton"] > button[kind="primary"]:hover {{ opacity:0.87; }}

/* ── Botón descarga ── */
div[data-testid="stDownloadButton"] > button {{
    background: linear-gradient(135deg, {ROSA} 0%, #C41230 100%);
    color:white; border:none; border-radius:8px;
    font-size:0.92rem; font-weight:700; padding:10px 0;
    width:100%; cursor:pointer;
}}

/* ── Métricas ── */
div[data-testid="metric-container"] {{
    background:white; border:1px solid #dde4f0;
    border-top:4px solid {AZUL}; border-radius:10px; padding:12px 16px;
}}

/* ── Result banner ── */
.result-banner {{
    background: linear-gradient(135deg, {AZUL} 0%, {AZUL_OSCURO} 100%);
    border-radius:10px; padding:14px 22px; color:white; margin-bottom:18px;
}}

/* ── Section label ── */
.sec-label {{
    color:{AZUL_OSCURO}; font-weight:700; font-size:0.88rem;
    border-left:4px solid {ROSA}; padding-left:9px; margin:18px 0 8px 0;
}}

/* ── Tabla de override ── */
.override-row {{
    background:white; border:1px solid #dde4f0; border-radius:8px;
    padding:10px 14px; margin-bottom:6px;
    display:flex; align-items:center; gap:12px;
}}
.override-producto {{ font-weight:700; color:{AZUL_OSCURO}; flex:1; }}
.override-sucursal  {{ color:#333; font-size:0.88rem; }}
.override-zona      {{ font-size:0.78rem; background:{GRIS}; border-radius:12px; padding:2px 9px; }}
.override-stock     {{ font-size:0.82rem; color:#666; }}

/* ── Historial tabla ── */
.hist-hdr {{
    background:{AZUL}; color:white;
    padding:9px 14px; border-radius:8px 8px 0 0;
    font-weight:700; font-size:0.86rem;
    display:flex; gap:0;
}}
.hist-row {{
    background:white; border-bottom:1px solid #e8edf5;
    padding:9px 14px; font-size:0.85rem;
    display:flex; align-items:center; gap:0;
}}
.hist-row:hover {{ background:{GRIS}; }}
.hist-row:last-child {{ border-bottom:none; border-radius:0 0 8px 8px; }}
.hc-id   {{ width:60px;  flex-shrink:0; color:{AZUL}; font-weight:700; }}
.hc-name {{ flex:1; }}
.hc-hora {{ width:120px; flex-shrink:0; color:#888; font-size:0.78rem; }}
.hc-stat {{ width:160px; flex-shrink:0; text-align:center; }}
.hc-dl   {{ width:80px;  flex-shrink:0; text-align:right; }}

/* ── Config cards ── */
.cfg-card {{
    background:white; border:1px solid #dde4f0; border-radius:10px;
    padding:18px 22px; margin-bottom:14px;
}}
.cfg-card-title {{
    color:{AZUL_OSCURO}; font-weight:700; font-size:0.95rem;
    margin-bottom:10px; padding-bottom:7px; border-bottom:1px solid #eee;
}}

/* ── Ayuda steps ── */
.help-step {{
    display:flex; gap:14px; align-items:flex-start;
    background:white; border:1px solid #dde4f0; border-radius:10px;
    padding:14px 18px; margin-bottom:10px;
}}
.help-num {{
    background:{AZUL}; color:white; border-radius:50%;
    width:30px; height:30px; display:flex; align-items:center;
    justify-content:center; font-weight:700; flex-shrink:0;
}}
.help-body strong {{ color:{AZUL_OSCURO}; }}
.help-body p {{ color:#555; font-size:0.85rem; margin:3px 0 0 0; }}

/* ── Zona priority chips ── */
.zona-0 {{ background:#E3F2FD; color:{AZUL_OSCURO}; border-radius:12px; padding:2px 9px; font-size:0.78rem; font-weight:600; }}
.zona-1 {{ background:#E8F5E9; color:{VERDE};        border-radius:12px; padding:2px 9px; font-size:0.78rem; font-weight:600; }}
.zona-2 {{ background:#FFF8E1; color:#F57F17;        border-radius:12px; padding:2px 9px; font-size:0.78rem; font-weight:600; }}
.zona-3 {{ background:#FFF3E0; color:#E65100;        border-radius:12px; padding:2px 9px; font-size:0.78rem; font-weight:600; }}
.zona-4 {{ background:#FFEBEE; color:#C62828;        border-radius:12px; padding:2px 9px; font-size:0.78rem; font-weight:600; }}

/* ── Misc ── */
#MainMenu, footer, header {{ visibility:hidden; }}
.block-container {{ padding-top:22px; padding-bottom:36px; }}
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
    # Quitar columna interna _gtin_key antes de exportar
    df_exp = df_ruta.drop(columns=["_gtin_key"], errors="ignore")
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
        "pagina":             "nuevo_cruce",
        "historial":          [],
        "ultimo_resultado":   None,
        "stock_por_producto": {},
        "overrides":          {},   # {row_idx: nuevo_nodo}
        "df_ruta_editable":   None,
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
          <div class="sb-logo-circle">G</div><br>
          <div class="sb-brand"><strong>Farmacias & Perfumerías</strong><br>GLOBAL</div>
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
          <span style="opacity:0.85;font-size:0.86rem">
            {res['filename']}
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

        # ── Cambio manual de sucursal ──────────────────────
        df_editable = st.session_state.df_ruta_editable
        if df_editable is not None and not df_editable.empty:
            with st.expander("✏️  Cambiar sucursal asignada (opcional)", expanded=False):
                st.caption("Hacé clic en 'Cambiar' en cualquier fila para asignar una sucursal diferente.")

                mapa_stk = st.session_state.get("mapa_stock_guardado", {})
                col_nodo_stk  = mapa_stk.get("nodo",  "nodo")
                col_stock_stk = mapa_stk.get("stock", "stock")

                for idx, row in df_editable.iterrows():
                    if row.get("Farmacia", "") == "— SIN COBERTURA —":
                        continue

                    gtin_key = row.get("_gtin_key", "")
                    override_actual = st.session_state.overrides.get(idx)
                    farmacia_actual = override_actual if override_actual else row["Farmacia"]

                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        zona_cls = {
                            "Depósito": "zona-0",
                            "NQN Capital": "zona-1",
                            "Centenario / Plottier": "zona-2",
                            "Cercana": "zona-3",
                            "Remota": "zona-4",
                        }.get(row.get("Zona", ""), "zona-1")

                        st.markdown(f"""
                        <div class="override-row">
                          <span class="override-producto">
                            {row.get('Producto','')[:40]}
                          </span>
                          <span class="override-sucursal">🏪 {farmacia_actual}</span>
                          <span class="{zona_cls}">{row.get('Zona','')}</span>
                          <span class="override-stock">Stock: {row.get('Stock sucursal',0)}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        if st.button("✏️ Cambiar", key=f"btn_cambiar_{idx}",
                                     use_container_width=True):
                            st.session_state[f"editando_{idx}"] = True

                    # Panel de selección de sucursal alternativa
                    if st.session_state.get(f"editando_{idx}"):
                        opciones_df = st.session_state.stock_por_producto.get(gtin_key)
                        if opciones_df is not None and col_nodo_stk in opciones_df.columns:
                            from src.optimizer import obtener_opciones_sucursal
                            max_op = cfg["optimizacion"].get("max_opciones_override", 5)
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

                                # Pre-seleccionar la actual si está entre las opciones
                                default_idx = 0
                                for i, o in enumerate(opciones):
                                    if o["nodo"] == farmacia_actual:
                                        default_idx = i
                                        break

                                with st.container():
                                    col_sel, col_ok, col_cancel = st.columns([4, 1, 1])
                                    with col_sel:
                                        seleccion = st.selectbox(
                                            "Sucursal alternativa:",
                                            options=labels,
                                            index=default_idx,
                                            key=f"sel_{idx}",
                                            label_visibility="collapsed",
                                        )
                                    with col_ok:
                                        if st.button("✅ Aplicar", key=f"ok_{idx}",
                                                     use_container_width=True):
                                            nodo_elegido = opciones[labels.index(seleccion)]["nodo"]
                                            st.session_state.overrides[idx] = nodo_elegido
                                            st.session_state[f"_zona_override_{idx}"] = zonas_op[seleccion]
                                            st.session_state[f"editando_{idx}"] = False
                                    with col_cancel:
                                        if st.button("✖ Cancelar", key=f"cancel_{idx}",
                                                     use_container_width=True):
                                            st.session_state[f"editando_{idx}"] = False

        # ── Regenerar Excel con overrides ─────────────────
        df_final = _aplicar_overrides(st.session_state.df_ruta_editable) \
                   if st.session_state.df_ruta_editable is not None \
                   else res.get("df_ruta", pd.DataFrame())

        if st.session_state.overrides:
            st.info(f"📝 Hay {len(st.session_state.overrides)} cambio(s) manual(es) aplicado(s). "
                    f"El Excel que descargás refleja esos cambios.")

        excel_dl = _excel_a_bytes(df_final, res["df_sin_stock"], cfg["estados_busqueda"])

        st.download_button(
            label="📥  Descargar Planilla Excel",
            data=excel_dl,
            file_name=res["filename"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        # Vista previa de la planilla (sin col interna)
        if not df_final.empty:
            st.markdown('<p class="sec-label">📋 Vista previa — Planilla Cadete</p>',
                        unsafe_allow_html=True)
            st.dataframe(df_final.drop(columns=["_gtin_key"], errors="ignore"),
                         use_container_width=True, height=250)

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

    pedidos_activos = len(
        df_pedidos[
            df_pedidos[mapa_pedidos["estado"]]
            .apply(lambda v: str(v).strip().lower()) == cfg["pedidos"]["estado_activo"].lower()
        ]
    )
    filename = f"planilla_cadete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    # Guardar en session_state
    st.session_state.ultimo_resultado = {
        "hora":           datetime.now().strftime("%H:%M  %d/%m/%y"),
        "pedidos_activos": pedidos_activos,
        "filas":          len(df_ruta),
        "sin_cob":        len(df_sin_stock),
        "df_sin_stock":   df_sin_stock,
        "df_ruta":        df_ruta,
        "filename":       filename,
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
    if st.button("🗑️  Limpiar historial", use_container_width=False):
        st.session_state.historial = []
        st.session_state.ultimo_resultado = None
        st.session_state.overrides = {}


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

    pasos = [
        ("Exportá el archivo de pedidos",
         "Desde el ecommerce, exportá los pedidos del día. "
         "Solo se procesan los que tengan estado <strong>Abierta</strong>."),
        ("Exportá el stock de sucursales",
         "Desde la base de datos, ejecutá la consulta de stock y exportá en .csv o .xlsx."),
        ("Cargá los dos archivos",
         "En <strong>⚡ Nuevo Cruce</strong>, seleccioná cada archivo en su zona de carga."),
        ("Generá la planilla",
         "Hacé clic en <strong>GENERAR PLANILLA</strong>. "
         "El sistema prioriza el depósito propio, luego NQN Capital, Centenario/Plottier, "
         "zonas cercanas y por último sucursales remotas."),
        ("Cambiá la sucursal si hace falta",
         "Abrí <strong>✏️ Cambiar sucursal asignada</strong> para ver las 5 mejores opciones "
         "y elegir manualmente. El Excel descargado refleja los cambios."),
        ("Descargá y compartí el Excel",
         "3 pestañas: <strong>Planilla Cadete</strong> (con dropdown de estado), "
         "<strong>Sin Cobertura</strong> y <strong>Log</strong>."),
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
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Prioridad de sucursales:**
        - 🔵 **Depósito** — APT-ECOMMERCE-NQN (primero siempre)
        - 🟢 **NQN Capital** — todas las sucursales de Neuquén centro
        - 🟡 **Centenario / Plottier** — segunda zona
        - 🟠 **Cercanas** — Añelo, El Chañar
        - 🔴 **Remotas** — Cutral Co, Zapala, Puerto Madryn (llamado)
        """)
    with col2:
        st.markdown("""
        **Estados del dropdown en el Excel:**
        - 🔵 **Búsqueda** — estado inicial al salir
        - ✅ **Encontrado** — el cadete lo encontró
        - 🟡 **Mal stock** — la sucursal no tenía lo indicado
        - 📞 **Llamar a suc** — sucursal remota, llamar antes
        - 🟡 **Mal stock - Resuelto** — se resolvió en otra sucursal
        - 🔴 **Llamar cliente** — sin stock en ningún lado
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
    if   pagina == "nuevo_cruce":    _page_nuevo_cruce(cfg)
    elif pagina == "historial":      _page_historial()
    elif pagina == "configuracion":  _page_configuracion(cfg)
    elif pagina == "ayuda":          _page_ayuda()


if __name__ == "__main__":
    main()
