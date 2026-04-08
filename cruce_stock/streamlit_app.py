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

from src.ui.tokens import (
    AZUL, AZUL_OSCURO, AZUL_CLARO,
    ROSA, VERDE, AMARILLO, GRIS, SLATE,
)
from src.ui.styles import CSS
from src.ui.components import (
    _badge_estado,
    _badge_zona,
    _render_tabla_mejorada,
)
from src.state import (
    _servidor_estado,
    _set_estado_cadete,
    _sincronizar_desde_servidor,
    _init_session,
    _inicializar_gestor,
    _ir_a,
    _agregar_historial,
    _aplicar_overrides,
)
from src.services.exportador import (
    excel_a_bytes as _excel_a_bytes_svc,
    excel_a_bytes_pro as _excel_a_bytes_pro_svc,
)


# ════════════════════════════════════════════════════════════
#  HELPERS LOCALES
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


def _excel_a_bytes(df_ruta, df_sin_stock, estados_busqueda, gestor_estados=None) -> bytes:
    return _excel_a_bytes_svc(
        df_ruta=df_ruta,
        df_sin_stock=df_sin_stock,
        estados_busqueda=estados_busqueda,
        estados_cadete=st.session_state.get("estados_cadete", {}),
        gestor_estados=gestor_estados or st.session_state.get("gestor_estados"),
        observaciones_cadete=st.session_state.get("observaciones_cadete", {}),
    )


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
        _nav_item("analitica",   "▲", "Analítica")

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
#  PÁGINA: DASHBOARD
# ════════════════════════════════════════════════════════════

def _page_dashboard(cfg):
    dias_es  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    meses_es = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    ahora      = datetime.now()
    dia_semana = dias_es[ahora.weekday()]
    hora_fmt   = ahora.strftime("%H:%M")
    fecha_fmt  = f"{ahora.day} {meses_es[ahora.month]} {ahora.year}"

    res      = st.session_state.ultimo_resultado
    df_ruta  = st.session_state.df_ruta_editable
    hist     = st.session_state.historial

    # ── Métricas ───────────────────────────────────────────
    pedidos_unicos = 0
    filas_planilla = 0
    sin_cobertura  = 0
    stock_sosp     = 0
    pct_cubierto   = 100
    sucursales_uso: dict = {}
    zonas_resumen: dict  = {}
    n_remotas = 0

    if res:
        pedidos_unicos = res.get("pedidos_unicos", res.get("pedidos_activos", 0))
        filas_planilla = res.get("filas", 0)
        sin_cobertura  = res.get("sin_cob", 0)

    if df_ruta is not None and not df_ruta.empty:
        stock_sosp  = int((df_ruta.get("⚠️ Stock", pd.Series()) == "⚠️ Verificar").sum())
        total_asig  = len(df_ruta[df_ruta.get("Farmacia", pd.Series()) != "— SIN COBERTURA —"])
        pct_cubierto = int(total_asig / len(df_ruta) * 100) if len(df_ruta) > 0 else 100
        if "Farmacia" in df_ruta.columns:
            for farm, cnt in df_ruta["Farmacia"].value_counts().items():
                if farm != "— SIN COBERTURA —":
                    sucursales_uso[str(farm)] = int(cnt)
        if "Zona" in df_ruta.columns:
            for zona, cnt in df_ruta["Zona"].value_counts().items():
                zonas_resumen[str(zona)] = int(cnt)
            remotas = df_ruta[df_ruta["Zona"] == "Remota"]
            n_remotas = len(remotas["Farmacia"].unique()) if "Farmacia" in remotas.columns else len(remotas)

    estados_cadete = st.session_state.get("estados_cadete", {})
    enc_cadete     = sum(1 for v in estados_cadete.values() if v in {"Encontrado","Mal stock - Resuelto"})
    pct_cadete     = int(enc_cadete / filas_planilla * 100) if filas_planilla > 0 else 0

    # ── Alertas priorizadas (calculadas antes de renderizar) ──
    alertas = []
    if sin_cobertura > 0:
        alertas.append(("crit", "🔴", f"{sin_cobertura} producto(s) sin cobertura",
                        "Requieren gestión manual antes de enviar al cadete", "nuevo_cruce"))
    if stock_sosp > 0:
        alertas.append(("warn", "⚠️", f"{stock_sosp} ítem(s) con stock sospechoso",
                        f"Stock > {cfg['optimizacion'].get('stock_sospechoso_umbral',200)} uds — verificar con la sucursal", None))
    if n_remotas > 0:
        alertas.append(("info", "📞", f"{n_remotas} sucursal(es) remota(s) asignada(s)",
                        "Coordinar por teléfono antes de enviar el cadete", "cadete"))
    if not hist:
        alertas.append(("info", "⚡", "Sin planilla generada en esta sesión",
                        "Cargá los archivos de pedidos y stock para comenzar", "nuevo_cruce"))

    tiene_actividad = res is not None

    # ═══════════════════════════════════════════════════════
    #  HEADER — saludo + estado operativo
    # ═══════════════════════════════════════════════════════
    dot_color    = VERDE if tiene_actividad else "#94A3B8"
    estado_label = "Operación activa" if tiene_actividad else "Sin actividad"
    alerta_badge = (f'<span style="background:#BE123C;color:#fff;font-size:0.7rem;'
                    f'font-weight:700;border-radius:10px;padding:2px 8px;margin-left:8px">'
                    f'{len([a for a in alertas if a[0]=="crit"])} crítica(s)</span>'
                    if any(a[0] == "crit" for a in alertas) else "")

    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;
                margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border-color)">
      <div>
        <div class="dash-greeting">Buen día — {dia_semana} {fecha_fmt}</div>
        <div class="dash-sub" style="margin-top:3px">
          {hora_fmt} &nbsp;·&nbsp;
          {"<strong>" + str(filas_planilla) + " líneas en planilla</strong> · " + str(pedidos_unicos) + " pedidos"
           if tiene_actividad else "Sin planilla activa"}
          {alerta_badge}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:6px;
                  background:var(--bg-card);border:1px solid var(--border-color);
                  border-radius:20px;padding:5px 13px;font-size:0.77rem;
                  font-weight:600;color:var(--text-secondary);margin-top:4px;flex-shrink:0">
        <span style="width:7px;height:7px;border-radius:50%;
                     background:{dot_color};display:inline-block"></span>
        {estado_label}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    #  ACCIÓN PRINCIPAL (si no hay actividad, ocupa la atención)
    # ═══════════════════════════════════════════════════════
    if not tiene_actividad:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{AZUL} 0%,{AZUL_OSCURO} 100%);
                    border-radius:14px;padding:24px 28px;margin-bottom:24px;
                    display:flex;align-items:center;justify-content:space-between;gap:16px">
          <div>
            <div style="color:#fff;font-size:1.1rem;font-weight:700;margin-bottom:4px">
              ⚡ Generá la planilla del cadete
            </div>
            <div style="color:rgba(255,255,255,0.75);font-size:0.85rem">
              Cargá el archivo de pedidos y el stock de sucursales para comenzar
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.button("⚡  Ir a Nuevo Cruce", type="primary",
                  use_container_width=True, on_click=_ir_a, args=("nuevo_cruce",))
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    #  KPI CARDS
    # ═══════════════════════════════════════════════════════
    c1, c2, c3, c4 = st.columns(4)

    # Card 1 — Pedidos
    with c1:
        det1 = f"{filas_planilla} líneas · {len(sucursales_uso)} sucursales" if tiene_actividad else "Cargá un cruce"
        st.markdown(f"""
        <div class="kpi-card kpi-info">
          <span class="kpi-icon">📦</span>
          <div class="kpi-label">Pedidos únicos</div>
          <div class="kpi-value">{pedidos_unicos if tiene_actividad else "—"}</div>
          <div class="kpi-detail">{det1}</div>
        </div>""", unsafe_allow_html=True)

    # Card 2 — Cobertura con mini-barra
    with c2:
        cls2 = "kpi-crit" if sin_cobertura > 0 else "kpi-ok"
        icn2 = "🔴" if sin_cobertura > 0 else "✅"
        bar2_w = max(4, pct_cubierto) if tiene_actividad else 0
        bar2_c = VERDE if pct_cubierto == 100 else (ROSA if sin_cobertura > 0 else AZUL)
        det2   = f"{sin_cobertura} sin cobertura" if sin_cobertura > 0 else "Todos cubiertos"
        st.markdown(f"""
        <div class="kpi-card {cls2}">
          <span class="kpi-icon">{icn2}</span>
          <div class="kpi-label">Cobertura</div>
          <div class="kpi-value">{pct_cubierto}%</div>
          <div style="background:var(--border-color);border-radius:4px;height:4px;margin:5px 0">
            <div style="height:4px;border-radius:4px;width:{bar2_w}%;background:{bar2_c}"></div>
          </div>
          <div class="kpi-detail">{det2 if tiene_actividad else "Sin datos"}</div>
        </div>""", unsafe_allow_html=True)

    # Card 3 — Stock sospechoso
    with c3:
        cls3 = "kpi-warn" if stock_sosp > 0 else "kpi-ok"
        icn3 = "⚠️" if stock_sosp > 0 else "✅"
        det3 = f"Umbral: {cfg['optimizacion'].get('stock_sospechoso_umbral',200)} uds" if stock_sosp > 0 else "Sin alertas de stock"
        st.markdown(f"""
        <div class="kpi-card {cls3}">
          <span class="kpi-icon">{icn3}</span>
          <div class="kpi-label">Stock a verificar</div>
          <div class="kpi-value">{stock_sosp if tiene_actividad else "—"}</div>
          <div class="kpi-detail">{det3}</div>
        </div>""", unsafe_allow_html=True)

    # Card 4 — Progreso cadete con mini-barra
    with c4:
        icn4 = "✅" if (enc_cadete >= filas_planilla > 0) else "🚴"
        cls4 = "kpi-ok" if (enc_cadete >= filas_planilla > 0) else "kpi-info"
        bar4_w = max(4, pct_cadete) if estados_cadete else 0
        det4   = f"{enc_cadete}/{filas_planilla} · {pct_cadete}%" if filas_planilla else "Sin actividad"
        st.markdown(f"""
        <div class="kpi-card {cls4}">
          <span class="kpi-icon">{icn4}</span>
          <div class="kpi-label">Cadete</div>
          <div class="kpi-value">{enc_cadete if estados_cadete else "—"}</div>
          <div style="background:var(--border-color);border-radius:4px;height:4px;margin:5px 0">
            <div style="height:4px;border-radius:4px;width:{bar4_w}%;
                 background:{VERDE if pct_cadete==100 else AZUL}"></div>
          </div>
          <div class="kpi-detail">{det4}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════
    #  COLUMNAS PRINCIPALES
    # ═══════════════════════════════════════════════════════
    col_izq, col_der = st.columns([3, 2])

    with col_izq:
        # ── Alertas priorizadas ────────────────────────────
        if alertas:
            st.markdown('<div class="dash-section-title">Alertas del día</div>',
                        unsafe_allow_html=True)
            for tipo, icon, titulo, detalle, dest in alertas:
                border_c = {"crit":"#E11D48","warn":"#D97706","info":AZUL}.get(tipo, AZUL)
                bg_c     = {"crit":"#FFF1F2","warn":"#FFFBEB","info":"#EFF6FF"}.get(tipo,"#EFF6FF")
                st.markdown(f"""
                <div style="border-left:3px solid {border_c};background:{bg_c};
                            border-radius:0 8px 8px 0;padding:10px 14px;
                            margin-bottom:7px;display:flex;align-items:flex-start;gap:10px">
                  <span style="font-size:1.1rem;flex-shrink:0">{icon}</span>
                  <div style="flex:1;min-width:0">
                    <div style="font-weight:600;font-size:0.87rem;
                                color:var(--text-primary)">{titulo}</div>
                    <div style="font-size:0.79rem;color:var(--text-muted);
                                margin-top:1px">{detalle}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if dest:
                    dest_label = {"nuevo_cruce":"⚡ Ir a Nuevo Cruce",
                                  "cadete":"🚴 Abrir Vista Cadete"}.get(dest, "→")
                    # Solo mostrar botón para la primera alerta con destino
                    break
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # ── Barras de progreso ─────────────────────────────
        if tiene_actividad:
            st.markdown('<div class="dash-section-title">Estado operativo</div>',
                        unsafe_allow_html=True)
            bar_cob_w = max(4, pct_cubierto)
            color_cob = VERDE if pct_cubierto == 100 else AZUL
            st.markdown(f"""
            <div class="dash-progress-wrap">
              <div style="display:flex;justify-content:space-between;
                          align-items:center;margin-bottom:5px">
                <span class="dash-progress-label" style="margin:0">
                  Cobertura de pedidos
                </span>
                <span style="font-size:0.88rem;font-weight:700;color:{color_cob}">
                  {pct_cubierto}%
                </span>
              </div>
              <div class="dash-progress-bar-bg">
                <div class="dash-progress-bar" style="width:{bar_cob_w}%;background:{color_cob}"></div>
              </div>
              <div style="font-size:0.76rem;color:var(--text-muted);margin-top:4px">
                {filas_planilla - sin_cobertura} productos con sucursal asignada
                {"· <strong style='color:#BE123C'>" + str(sin_cobertura) + " sin cobertura</strong>" if sin_cobertura > 0 else "· todos cubiertos"}
              </div>
            </div>
            """, unsafe_allow_html=True)

            if estados_cadete and filas_planilla > 0:
                st.markdown(f"""
                <div class="dash-progress-wrap">
                  <div style="display:flex;justify-content:space-between;
                              align-items:center;margin-bottom:5px">
                    <span class="dash-progress-label" style="margin:0">Progreso cadete</span>
                    <span style="font-size:0.88rem;font-weight:700;
                                 color:{VERDE if pct_cadete==100 else AZUL}">
                      {pct_cadete}%
                    </span>
                  </div>
                  <div class="dash-progress-bar-bg">
                    <div class="dash-progress-bar"
                         style="width:{max(4,pct_cadete)}%;
                                background:{VERDE if pct_cadete==100 else AZUL}"></div>
                  </div>
                  <div style="font-size:0.76rem;color:var(--text-muted);margin-top:4px">
                    {enc_cadete} encontrados · {filas_planilla - enc_cadete} pendientes
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Acciones rápidas ───────────────────────────────
        st.markdown('<div class="dash-section-title">Acciones</div>', unsafe_allow_html=True)
        if tiene_actividad:
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
        else:
            st.button("⚡  Nuevo Cruce", type="primary", use_container_width=True,
                      on_click=_ir_a, args=("nuevo_cruce",))
            qa2, qa3 = st.columns(2)
            with qa2:
                st.button("🚴  Vista Cadete", use_container_width=True,
                          on_click=_ir_a, args=("cadete",))
            with qa3:
                st.button("📋  Historial", use_container_width=True,
                          on_click=_ir_a, args=("historial",))

    with col_der:
        # ── Último cruce + descarga ────────────────────────
        if hist:
            ultimo = hist[0]
            sin_u  = ultimo["sin_cob"]
            badge_cob = (f'<span style="color:#BE123C;font-weight:700">⚠️ {sin_u} sin cob.</span>'
                         if sin_u > 0 else
                         '<span style="color:#059669;font-weight:700">✅ Completo</span>')
            st.markdown(f"""
            <div class="dash-section-title">Último cruce</div>
            <div class="dash-ultimo-cruce">
              <span class="dash-uc-icon">📁</span>
              <div style="flex:1;min-width:0">
                <div class="dash-uc-name" style="white-space:nowrap;overflow:hidden;
                     text-overflow:ellipsis">{ultimo["pedidos"]}</div>
                <div class="dash-uc-meta">
                  {ultimo["hora"]} &nbsp;·&nbsp;
                  {ultimo["filas"]} filas &nbsp;·&nbsp;
                  {badge_cob}
                </div>
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
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ── Distribución por zona ──────────────────────────
        if zonas_resumen:
            st.markdown('<div class="dash-section-title">Distribución por zona</div>',
                        unsafe_allow_html=True)
            zona_icons = {"Deposito":"🏭","NQN Capital":"🏙️",
                          "Centenario/Plottier":"🏘️","Cercana":"📍","Remota":"🗺️"}
            zona_cls_m = {"Deposito":"zona-0","NQN Capital":"zona-1",
                          "Centenario/Plottier":"zona-2","Cercana":"zona-3","Remota":"zona-4"}
            max_z = max(zonas_resumen.values()) if zonas_resumen else 1
            for zona, cnt in sorted(zonas_resumen.items(),
                                    key=lambda x: x[1], reverse=True):
                icn_z  = zona_icons.get(zona, "📍")
                zcls   = zona_cls_m.get(zona, "zona-1")
                pct_z  = int(cnt / max_z * 100)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;
                            margin-bottom:6px;font-size:0.82rem">
                  <span style="width:20px;text-align:center">{icn_z}</span>
                  <span class="{zcls}" style="width:130px;flex-shrink:0">{zona}</span>
                  <div style="flex:1;background:var(--border-color);
                              border-radius:4px;height:6px">
                    <div style="height:6px;border-radius:4px;
                                width:{pct_z}%;background:{AZUL}"></div>
                  </div>
                  <span style="width:26px;text-align:right;font-weight:600;
                               color:var(--text-secondary)">{cnt}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── Top sucursales ─────────────────────────────────
        if sucursales_uso:
            st.markdown('<div class="dash-section-title">Top sucursales</div>',
                        unsafe_allow_html=True)
            max_cnt = max(sucursales_uso.values())
            top6    = sorted(sucursales_uso.items(), key=lambda x: x[1], reverse=True)[:6]
            for nombre, cnt in top6:
                pct_bar     = int(cnt / max_cnt * 100)
                nombre_corto = nombre[:26] + "…" if len(nombre) > 26 else nombre
                st.markdown(f"""
                <div class="dash-suc-row">
                  <span class="dash-suc-name">{nombre_corto}</span>
                  <span class="dash-suc-bar-wrap">
                    <span class="dash-suc-bar" style="width:{pct_bar}%"></span>
                  </span>
                  <span class="dash-suc-cnt">{cnt}</span>
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

        # ── Asignación de nodos — top-5 por producto ──────────
        if df_editable is not None and not df_editable.empty:
            n_overrides = len(st.session_state.overrides)
            st.markdown(
                f'<p class="sec-label">🏪 Asignación de sucursales'
                f'{"&nbsp; · &nbsp;<strong>" + str(n_overrides) + " cambiados</strong>" if n_overrides else ""}'
                f'</p>',
                unsafe_allow_html=True)
            st.caption("El sistema sugiere la mejor sucursal según prioridad de zona y stock. "
                       "Expandí cualquier fila para ver las top 5 opciones y elegir otra.")

            mapa_stk      = st.session_state.get("mapa_stock_guardado", {})
            col_nodo_stk  = mapa_stk.get("nodo",  "nodo")
            col_stock_stk = mapa_stk.get("stock", "stock")

            zona_cls_map = {
                "Deposito": "zona-0", "NQN Capital": "zona-1",
                "Centenario/Plottier": "zona-2", "Cercana": "zona-3", "Remota": "zona-4",
            }

            for idx, row in df_editable.iterrows():
                if row.get("Farmacia", "") == "— SIN COBERTURA —":
                    continue

                gtin_key        = row.get("_gtin_key", "")
                override_actual = st.session_state.overrides.get(idx)
                farmacia_actual = override_actual if override_actual else row["Farmacia"]
                zona_actual     = str(row.get("Zona", ""))
                stock_actual    = row.get("Stock sucursal", 0)
                nro_ped         = str(row.get("N° Pedido", "") or "")
                sosp_flag       = "⚠️ " if row.get("⚠️ Stock") == "⚠️ Verificar" else ""
                changed         = idx in st.session_state.overrides
                zona_cls        = zona_cls_map.get(zona_actual, "zona-1")
                border_c        = AZUL if changed else "var(--border)"

                # Fila resumen: producto → nodo asignado → [↕ opciones]
                col_info, col_btn = st.columns([6, 1])
                with col_info:
                    st.markdown(f"""
                    <div class="override-row" style="border-color:{border_c}">
                      <span style="color:var(--text-muted);font-size:0.75rem;
                                   width:74px;flex-shrink:0">#{nro_ped}</span>
                      <span class="override-producto">
                        {sosp_flag}{str(row.get('Producto',''))[:38]}
                      </span>
                      <span class="override-sucursal">
                        {"✏️ " if changed else "🏪 "}{farmacia_actual}
                      </span>
                      <span class="{zona_cls}">{zona_actual}</span>
                      <span class="override-stock">Stock: {stock_actual}</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    btn_label = "↩️" if changed else "↕"
                    btn_help  = "Revertir al nodo original" if changed else "Ver top 5 opciones"
                    if st.button(btn_label, key=f"btn_cambiar_{idx}",
                                 use_container_width=True, help=btn_help):
                        if changed:
                            # Revertir directamente
                            del st.session_state.overrides[idx]
                            st.session_state.pop(f"_zona_override_{idx}", None)
                            st.session_state.pop(f"editando_{idx}", None)
                        else:
                            st.session_state[f"editando_{idx}"] = not st.session_state.get(f"editando_{idx}", False)

                # Panel top-5 + override manual
                if st.session_state.get(f"editando_{idx}"):
                    opciones_df = st.session_state.stock_por_producto.get(gtin_key)
                    from src.optimizer import obtener_opciones_sucursal
                    max_op = cfg["optimizacion"].get("max_opciones_override", 5)
                    opciones: list[dict] = []
                    if opciones_df is not None and col_nodo_stk in opciones_df.columns:
                        opciones = obtener_opciones_sucursal(
                            df_stock_producto=opciones_df,
                            col_nodo=col_nodo_stk,
                            col_stock=col_stock_stk,
                            zonas_cfg=cfg["zonas"],
                            zona_labels={int(k): v for k, v in cfg.get("zona_labels", {}).items()},
                            max_opciones=max_op,
                        )

                    with st.container():
                        st.markdown(
                            f'<div style="margin:0 0 4px 8px;font-size:0.77rem;'
                            f'color:var(--text-muted);font-weight:600;'
                            f'letter-spacing:0.5px">TOP {len(opciones)} OPCIONES</div>',
                            unsafe_allow_html=True)

                        if opciones:
                            labels   = [o["label"] for o in opciones]
                            zonas_op = {o["nodo"]: o["zona"] for o in opciones}
                            default_i = next(
                                (i for i, o in enumerate(opciones)
                                 if o["nodo"] == farmacia_actual), 0)

                            # Cards visuales con radio button
                            for i_op, op in enumerate(opciones):
                                zcls  = zona_cls_map.get(op["zona"], "zona-1")
                                is_sel = (i_op == default_i)
                                sel_style = (f"border-color:{AZUL};background:{AZUL}08"
                                             if is_sel else "")
                                st.markdown(f"""
                                <div class="nodo-card {'nodo-selected' if is_sel else ''}"
                                     style="{sel_style}">
                                  <span style="font-size:0.78rem;color:var(--text-muted);
                                               width:22px;text-align:center">
                                    {"●" if is_sel else "○"}
                                  </span>
                                  <span class="nodo-nombre">{op['nodo']}</span>
                                  <span class="{zcls}">{op['zona']}</span>
                                  <span class="nodo-stock">{op['stock']} uds</span>
                                </div>
                                """, unsafe_allow_html=True)

                            col_sel, col_ok, col_cancel = st.columns([4, 1, 1])
                            with col_sel:
                                seleccion = st.selectbox(
                                    "Elegir nodo:", options=labels,
                                    index=default_i,
                                    key=f"sel_{idx}",
                                    label_visibility="collapsed")
                            with col_ok:
                                if st.button("✅ Ok", key=f"ok_{idx}",
                                             use_container_width=True):
                                    nodo_elegido = opciones[labels.index(seleccion)]["nodo"]
                                    st.session_state.overrides[idx] = nodo_elegido
                                    st.session_state[f"_zona_override_{idx}"] = zonas_op[nodo_elegido]
                                    st.session_state[f"editando_{idx}"] = False
                            with col_cancel:
                                if st.button("✖", key=f"cancel_{idx}",
                                             use_container_width=True):
                                    st.session_state[f"editando_{idx}"] = False
                        else:
                            st.warning("Sin opciones disponibles para este producto.")

                        # Override manual libre
                        with st.expander("✏️ Ingresar nodo manualmente", expanded=False):
                            col_mn, col_mok = st.columns([4, 1])
                            with col_mn:
                                nodo_manual = st.text_input(
                                    "Nodo:", placeholder="Ej: APT-ECOMMERCE-NQN",
                                    key=f"manual_{idx}", label_visibility="collapsed")
                            with col_mok:
                                if st.button("Aplicar", key=f"manual_ok_{idx}",
                                             use_container_width=True):
                                    if nodo_manual.strip():
                                        st.session_state.overrides[idx] = nodo_manual.strip()
                                        st.session_state[f"editando_{idx}"] = False

                    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

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

        # ── Panel de sincronización cadete ↔ oficina ─────────
        srv = _servidor_estado()
        if srv["sesion_activa"] or srv["estados_cadete"]:
            ua  = srv["ultima_actualizacion"] or "—"
            n_e = sum(1 for v in srv["estados_cadete"].values()
                      if v in {"Encontrado", "Mal stock - Resuelto"})
            n_t = len(df_con_overrides) if not df_con_overrides.empty else 0
            pct_s = int(n_e / n_t * 100) if n_t > 0 else 0
            col_sinfo, col_sbtn = st.columns([5, 1])
            with col_sinfo:
                st.markdown(f"""
                <div class="sync-badge">
                  <span class="sync-dot"></span>
                  <span>
                    <strong>Cadete activo</strong> &nbsp;·&nbsp;
                    Última actualización: <strong>{ua}</strong> &nbsp;·&nbsp;
                    {n_e}/{n_t} encontrados ({pct_s}%)
                  </span>
                </div>
                """, unsafe_allow_html=True)
            with col_sbtn:
                if st.button("🔄 Sincronizar", use_container_width=True,
                             help="Traer estados actuales del cadete a esta vista"):
                    _sincronizar_desde_servidor()
                    st.success("✅ Estados sincronizados")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

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

    # ── Flujo guiado por pasos ────────────────────────────────
    tiene_pedidos = False
    tiene_stock   = False
    df_prev_p: pd.DataFrame | None = None
    df_prev_s: pd.DataFrame | None = None

    def _leer_preview(uf) -> pd.DataFrame | None:
        try:
            uf.seek(0)
            ext = pathlib.Path(uf.name).suffix.lower()
            df = pd.read_excel(uf) if ext in (".xlsx", ".xls") \
                 else pd.read_csv(uf, sep=None, engine="python", dtype=str)
            uf.seek(0)
            return df
        except Exception:
            try: uf.seek(0)
            except Exception: pass
            return None

    def _paso_dot(n, label, activo, listo):
        color_dot = VERDE if listo else (AZUL if activo else "var(--border)")
        color_txt = "var(--text)" if (activo or listo) else "var(--text-muted)"
        icon      = "✓" if listo else str(n)
        return (
            f'<div style="display:flex;align-items:center;gap:6px">'
            f'<div style="width:22px;height:22px;border-radius:50%;background:{color_dot};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:0.7rem;font-weight:700;color:#fff;flex-shrink:0">{icon}</div>'
            f'<span style="font-size:0.8rem;font-weight:600;color:{color_txt}">{label}</span>'
            f'</div>'
        )

    # ── PASO 1: Carga de archivos ─────────────────────────────
    st.markdown('<p class="sec-label">📂 Archivos de entrada</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        archivo_pedidos = st.file_uploader(
            "📋 Archivo de Pedidos",
            type=["xlsx", "xls", "csv", "txt"],
            key="up_pedidos",
            help="Exportá los pedidos con estado Abierta desde el sistema",
        )
        if archivo_pedidos:
            df_prev_p = _leer_preview(archivo_pedidos)
            if df_prev_p is not None:
                tiene_pedidos = True
                n_f = len(df_prev_p); n_c = len(df_prev_p.columns)
                cols_str = ", ".join(df_prev_p.columns[:4].tolist())
                if n_c > 4: cols_str += f" +{n_c - 4} más"
                st.markdown(f"""
                <div style="background:{VERDE}12;border:1px solid {VERDE}40;
                            border-radius:8px;padding:10px 14px;margin-top:4px">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    <span style="color:{VERDE};font-size:1rem">✓</span>
                    <span style="font-weight:600;font-size:0.85rem;
                                 color:var(--text)">{archivo_pedidos.name}</span>
                  </div>
                  <div style="font-size:0.75rem;color:var(--text-muted);
                               display:flex;gap:16px;flex-wrap:wrap">
                    <span>🗂 <strong>{n_f}</strong> filas</span>
                    <span>📐 <strong>{n_c}</strong> columnas</span>
                  </div>
                  <div style="font-size:0.72rem;color:var(--text-muted);
                               margin-top:4px;font-style:italic">{cols_str}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ No se pudo leer el archivo.")
        else:
            st.markdown(f"""
            <div style="border:2px dashed var(--border);border-radius:8px;
                        padding:18px 14px;text-align:center;
                        color:var(--text-muted);font-size:0.8rem;margin-top:4px">
              <div style="font-size:1.4rem;margin-bottom:4px">📋</div>
              Pedidos con estado <em>Abierta</em><br>
              <span style="font-size:0.72rem;opacity:0.7">.xlsx · .xls · .csv</span>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        archivo_stock = st.file_uploader(
            "🏪 Stock de Sucursales",
            type=["xlsx", "xls", "csv", "txt"],
            key="up_stock",
            help="Exportá el stock actualizado desde la base de datos",
        )
        if archivo_stock:
            df_prev_s = _leer_preview(archivo_stock)
            if df_prev_s is not None:
                tiene_stock = True
                n_f_s = len(df_prev_s); n_c_s = len(df_prev_s.columns)
                cols_str_s = ", ".join(df_prev_s.columns[:4].tolist())
                if n_c_s > 4: cols_str_s += f" +{n_c_s - 4} más"
                st.markdown(f"""
                <div style="background:{VERDE}12;border:1px solid {VERDE}40;
                            border-radius:8px;padding:10px 14px;margin-top:4px">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    <span style="color:{VERDE};font-size:1rem">✓</span>
                    <span style="font-weight:600;font-size:0.85rem;
                                 color:var(--text)">{archivo_stock.name}</span>
                  </div>
                  <div style="font-size:0.75rem;color:var(--text-muted);
                               display:flex;gap:16px;flex-wrap:wrap">
                    <span>🗂 <strong>{n_f_s}</strong> filas</span>
                    <span>📐 <strong>{n_c_s}</strong> columnas</span>
                  </div>
                  <div style="font-size:0.72rem;color:var(--text-muted);
                               margin-top:4px;font-style:italic">{cols_str_s}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ No se pudo leer el archivo.")
        else:
            st.markdown(f"""
            <div style="border:2px dashed var(--border);border-radius:8px;
                        padding:18px 14px;text-align:center;
                        color:var(--text-muted);font-size:0.8rem;margin-top:4px">
              <div style="font-size:1.4rem;margin-bottom:4px">🏪</div>
              Stock actual de sucursales<br>
              <span style="font-size:0.72rem;opacity:0.7">.xlsx · .xls · .csv</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── PASO 2: Mini resumen pre-cruce ────────────────────────
    if tiene_pedidos and tiene_stock and df_prev_p is not None and df_prev_s is not None:
        from src.matcher import mapear_columnas_pedidos, mapear_columnas_stock
        _est_activo = cfg["pedidos"].get("estado_activo", "")
        _n_ped_unicos = _n_lineas = _n_sucs = _n_prods = "—"
        try:
            _mp = mapear_columnas_pedidos(df_prev_p, cfg)
            _ms = mapear_columnas_stock(df_prev_s, cfg)
            if _mp.get("estado") and _mp["estado"] in df_prev_p.columns:
                _df_act = df_prev_p[
                    df_prev_p[_mp["estado"]]
                    .apply(lambda v: str(v).strip().lower()) == _est_activo.lower()
                ]
                _n_lineas = len(_df_act)
                _col_nro  = _mp.get("nro_pedido")
                if _col_nro and _col_nro in _df_act.columns:
                    _n_ped_unicos = int(_df_act[_col_nro].nunique())
            _col_nodo = _ms.get("nodo")
            if _col_nodo and _col_nodo in df_prev_s.columns:
                _n_sucs = df_prev_s[_col_nodo].nunique()
            _col_id = _ms.get("gtin") or _ms.get("sku")
            if _col_id and _col_id in df_prev_s.columns:
                _n_prods = df_prev_s[_col_id].nunique()
        except Exception:
            pass

        st.markdown(f"""
        <div style="background:var(--card-bg);border:1px solid var(--border);
                    border-radius:10px;padding:14px 18px;margin-bottom:12px">
          <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.6px;
                      color:var(--text-muted);margin-bottom:10px">RESUMEN PRE-CRUCE</div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
            <div style="text-align:center;padding:8px;background:var(--bg);
                        border-radius:6px;border:1px solid var(--border)">
              <div style="font-size:1.3rem;font-weight:700;color:{AZUL}">{_n_ped_unicos}</div>
              <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px">Pedidos únicos</div>
            </div>
            <div style="text-align:center;padding:8px;background:var(--bg);
                        border-radius:6px;border:1px solid var(--border)">
              <div style="font-size:1.3rem;font-weight:700;color:{AZUL}">{_n_lineas}</div>
              <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px">Líneas activas</div>
            </div>
            <div style="text-align:center;padding:8px;background:var(--bg);
                        border-radius:6px;border:1px solid var(--border)">
              <div style="font-size:1.3rem;font-weight:700;color:{SLATE}">{_n_sucs}</div>
              <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px">Sucursales</div>
            </div>
            <div style="text-align:center;padding:8px;background:var(--bg);
                        border-radius:6px;border:1px solid var(--border)">
              <div style="font-size:1.3rem;font-weight:700;color:{SLATE}">{_n_prods}</div>
              <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px">Productos en stock</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Indicador de pasos ────────────────────────────────────
    _p1_ok  = tiene_pedidos and tiene_stock
    _sep    = '<div style="flex:1;height:1px;background:var(--border);margin:0 6px"></div>'
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:4px;margin-bottom:12px">'
        f'{_paso_dot(1,"Archivos cargados", True, _p1_ok)}'
        f'{_sep}'
        f'{_paso_dot(2,"Resumen validado", _p1_ok, _p1_ok)}'
        f'{_sep}'
        f'{_paso_dot(3,"Generar planilla", _p1_ok, False)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not (tiene_pedidos and tiene_stock):
        faltan = []
        if not tiene_pedidos: faltan.append("pedidos")
        if not tiene_stock:   faltan.append("stock")
        st.info(f"⬆️  Falta cargar: **{' y '.join(faltan)}**.")
        return

    # ── PASO 3: CTA ───────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{AZUL} 0%,{AZUL_OSCURO} 100%);
                border-radius:10px;padding:16px 20px;margin-bottom:8px;
                display:flex;align-items:center;justify-content:space-between">
      <div>
        <div style="color:#fff;font-weight:700;font-size:0.95rem">
          Listo para generar la planilla del cadete
        </div>
        <div style="color:rgba(255,255,255,0.75);font-size:0.78rem;margin-top:2px">
          El sistema asignará las sucursales óptimas y generará el Excel de despacho
        </div>
      </div>
      <div style="font-size:1.8rem">⚡</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.button("⚡  GENERAR PLANILLA DEL CADETE", type="primary",
                     use_container_width=True):
        return

    # ── Pipeline ───────────────────────────────────────────
    from src.logger import limpiar_log, get_log_records
    from src.loader import cargar_archivo
    from src.matcher import mapear_columnas_pedidos, mapear_columnas_stock
    from src.optimizer import construir_planilla
    from src.services.normalizacion import normalizar_pedidos, normalizar_stock
    from src.services.matching import ejecutar_matching

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

        barra.progress(45, text="Normalizando datos...")
        df_pedidos = normalizar_pedidos(df_pedidos, mapa_pedidos)
        df_stock   = normalizar_stock(df_stock,   mapa_stock)

        barra.progress(55, text="Analizando cobertura...")
        resultado_matching = ejecutar_matching(
            df_pedidos, df_stock, mapa_pedidos, mapa_stock, cfg
        )
        st.session_state["resultado_matching"] = resultado_matching

        barra.progress(60, text="Asignando sucursales (tiers + consolidación)...")
        df_ruta, df_sin_stock, stock_por_producto = construir_planilla(
            df_pedidos=df_pedidos, df_stock=df_stock,
            mapa_pedidos=mapa_pedidos, mapa_stock=mapa_stock, cfg=cfg,
        )

        from src.services.asignacion import calcular_resumenes_pedidos
        resumenes_ped = calcular_resumenes_pedidos(df_ruta)
        st.session_state["resumenes_pedidos"] = resumenes_ped

        _inicializar_gestor(df_ruta)

        # Calcular pedidos_unicos dentro del try (necesario para el Excel)
        _df_act = df_pedidos[
            df_pedidos[mapa_pedidos["estado"]]
            .apply(lambda v: str(v).strip().lower()) == cfg["pedidos"]["estado_activo"].lower()
        ]
        _col_nro = mapa_pedidos.get("nro_pedido")
        _pedidos_unicos = int(_df_act[_col_nro].nunique()) if _col_nro else len(_df_act)

        barra.progress(85, text="Generando Excel profesional...")
        excel_bytes = _excel_a_bytes_pro_svc(
            df_ruta            = df_ruta,
            df_sin_stock       = df_sin_stock,
            estados_busqueda   = cfg["estados_busqueda"],
            gestor_estados     = st.session_state.get("gestor_estados"),
            resultado_matching = st.session_state.get("resultado_matching"),
            resumenes_pedidos  = resumenes_ped,
            archivo_pedidos    = archivo_pedidos.name,
            archivo_stock      = archivo_stock.name,
            pedidos_unicos     = _pedidos_unicos,
        )
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

    from src.services.analytics import extraer_snapshot
    _snap = extraer_snapshot(
        df_ruta            = df_ruta,
        df_sin_stock       = df_sin_stock,
        resultado_matching = st.session_state.get("resultado_matching"),
        pedidos_unicos     = pedidos_unicos,
    )
    _agregar_historial(archivo_pedidos.name, archivo_stock.name,
                       len(df_ruta), len(df_sin_stock), excel_bytes, filename,
                       analytics=_snap)

    # ── Resumen de matching ──────────────────────────────────
    rm = st.session_state.get("resultado_matching")
    if rm:
        rs = rm.resumen
        pct = rs.pct_cobertura()
        color_cob = "#059669" if pct >= 90 else "#D97706" if pct >= 70 else "#E11D48"
        with st.expander(
            f"📊 Cobertura del cruce: **{pct}%** "
            f"({rs.con_match_gtin} GTIN · {rs.con_match_sku} SKU · {rs.sin_match} sin match)",
            expanded=(rs.sin_match > 0 or rs.ambiguos > 0),
        ):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total líneas",    rs.total_lineas)
            c2.metric("Match GTIN",      rs.con_match_gtin,  delta=None)
            c3.metric("Match SKU",       rs.con_match_sku,   delta=None)
            c4.metric("Sin match",       rs.sin_match,       delta=None)
            c5.metric("Ambiguos",        rs.ambiguos,        delta=None)

            if rs.gtin_duplicados or rs.sku_duplicados:
                st.caption(
                    f"⚠️ GTINs con filas duplicadas en stock: **{rs.gtin_duplicados}** · "
                    f"SKUs con filas duplicadas: **{rs.sku_duplicados}**"
                )
            if rs.sin_match > 0:
                sin_match_items = [
                    f"- {l.producto} (GTIN: {l.gtin or '—'} / SKU: {l.sku or '—'})"
                    for l in rm.lineas if not l.match_encontrado
                ]
                st.markdown("**Líneas sin match:**\n" + "\n".join(sin_match_items[:20]))
                if len(sin_match_items) > 20:
                    st.caption(f"… y {len(sin_match_items) - 20} más.")

    # ── Resumen por pedido (asignación inteligente) ──────────
    resumenes = st.session_state.get("resumenes_pedidos", [])
    if resumenes:
        hay_problemas = any(r.filas_sin_cobertura > 0 for r in resumenes)
        with st.expander(
            f"🗂 Resumen por pedido ({len(resumenes)} pedido(s))",
            expanded=hay_problemas,
        ):
            for rp in resumenes:
                icon = "✅" if rp.filas_sin_cobertura == 0 else "⚠️"
                tier_desc = ""
                if rp.tiers_usados:
                    partes = []
                    nombres = {0: "prioritarias", 1: "segunda opción", 2: "resto", 3: "último recurso"}
                    for t in sorted(rp.tiers_usados):
                        partes.append(f"{rp.tiers_usados[t]}× {nombres.get(t, f'tier {t}')}")
                    tier_desc = " · ".join(partes)
                consolida_txt = (
                    f" · {rp.filas_consolidadas} consolidada(s)" if rp.filas_consolidadas else ""
                )
                st.markdown(
                    f"{icon} **Pedido #{rp.nro_pedido}** — "
                    f"{rp.total_sucursales} sucursal(es): "
                    f"`{'`, `'.join(rp.sucursales_involucradas) or '—'}`  \n"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Productos: {rp.filas_con_cobertura} con cobertura"
                    f"{', **' + str(rp.filas_sin_cobertura) + ' sin cobertura**' if rp.filas_sin_cobertura else ''}"
                    + (f"  \n&nbsp;&nbsp;&nbsp;&nbsp;Tiers: {tier_desc}{consolida_txt}" if tier_desc else "")
                )

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
#  PÁGINA: ANALÍTICA
# ════════════════════════════════════════════════════════════

def _page_analitica():
    from src.services.analytics import (
        agregar_historial,
        top_productos_problematicos,
        top_sucursales_carga,
        tendencia_cobertura,
    )

    items = st.session_state.historial
    items_con_analytics = [i for i in items if i.get("analytics")]

    st.markdown(f"""
    <div class="page-hdr">
      <div>
        <p class="page-title">📊 Analítica Operativa</p>
        <p class="page-sub">Patrones detectados en los cruces de esta sesión</p>
      </div>
      <span class="badge-azul">{len(items_con_analytics)} cruce(s)</span>
    </div>
    """, unsafe_allow_html=True)

    if not items_con_analytics:
        st.info(
            "Todavía no hay datos para analizar. "
            "Generá al menos un cruce para ver las métricas."
        )
        if st.button("⚡ Ir a Nuevo Cruce", on_click=_ir_a, args=("nuevo_cruce",)):
            pass
        return

    # ── KPIs globales ─────────────────────────────────────────
    agg = agregar_historial(items_con_analytics)
    pct_avg = agg.get("pct_cobertura_avg", 0)
    color_pct = VERDE if pct_avg >= 90 else (AMARILLO if pct_avg >= 70 else ROSA)

    st.markdown('<p class="sec-label">Resumen de la sesión</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    k1.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Cruces realizados</div>
      <div class="kpi-value" style="color:{AZUL}">{agg['total_cruces']}</div>
    </div>
    """, unsafe_allow_html=True)

    k2.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Cobertura promedio</div>
      <div class="kpi-value" style="color:{color_pct}">{pct_avg}%</div>
      <div class="kpi-detail">min {agg['pct_cobertura_min']}% · max {agg['pct_cobertura_max']}%</div>
    </div>
    """, unsafe_allow_html=True)

    k3.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Sin cobertura acumulado</div>
      <div class="kpi-value" style="color:{ROSA if agg['sin_cob_acum'] > 0 else VERDE}">
        {agg['sin_cob_acum']}
      </div>
      <div class="kpi-detail">líneas sin stock</div>
    </div>
    """, unsafe_allow_html=True)

    k4.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Mejor cruce</div>
      <div class="kpi-value" style="color:{VERDE}">{agg['mejor_cruce_id']}</div>
      <div class="kpi-detail">{agg['mejor_cruce_pct']}% cobertura</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Tendencia de cobertura ────────────────────────────────
    if len(items_con_analytics) > 1:
        st.markdown('<p class="sec-label">Tendencia de cobertura</p>', unsafe_allow_html=True)
        tendencia = tendencia_cobertura(items_con_analytics)
        max_pct = max((t["pct"] for t in tendencia), default=100) or 100
        for t in tendencia:
            pct_t  = t["pct"]
            bar_w  = max(4, int(pct_t / max_pct * 100))
            c_bar  = VERDE if pct_t >= 90 else (AMARILLO if pct_t >= 70 else ROSA)
            sin_badge = (
                f'<span style="background:{ROSA}22;color:{ROSA};'
                f'border-radius:10px;padding:1px 7px;font-size:0.72rem;margin-left:6px">'
                f'⚠️ {t["sin_cob"]} sin cob.</span>'
            ) if t["sin_cob"] > 0 else ""
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;
                        margin-bottom:6px;font-size:0.82rem">
              <span style="color:var(--text-muted);width:38px;
                           text-align:right;flex-shrink:0">{t['id']}</span>
              <div style="flex:1;background:var(--border);border-radius:4px;height:10px">
                <div style="width:{bar_w}%;background:{c_bar};
                            border-radius:4px;height:10px"></div>
              </div>
              <span style="font-weight:600;width:38px;color:{c_bar}">{pct_t}%</span>
              <span style="color:var(--text-muted);font-size:0.75rem;
                           width:120px;flex-shrink:0">{t['hora']}</span>
              {sin_badge}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Productos problemáticos + Sucursales ──────────────────
    col_prod, col_sucs = st.columns(2)

    with col_prod:
        st.markdown('<p class="sec-label">Productos sin cobertura frecuentes</p>',
                    unsafe_allow_html=True)
        prods = top_productos_problematicos(items_con_analytics, top_n=10)
        if prods:
            max_v = prods[0]["veces"]
            for i, p in enumerate(prods):
                bar_w = max(6, int(p["veces"] / max_v * 100))
                rank_color = ROSA if i < 3 else AMARILLO if i < 6 else "var(--text-muted)"
                st.markdown(f"""
                <div style="margin-bottom:6px">
                  <div style="display:flex;align-items:center;
                              justify-content:space-between;margin-bottom:2px">
                    <span style="font-size:0.8rem;color:var(--text);
                                 flex:1;min-width:0;overflow:hidden;
                                 text-overflow:ellipsis;white-space:nowrap"
                          title="{p['producto']}">{p['producto'][:40]}</span>
                    <span style="font-size:0.75rem;font-weight:700;
                                 color:{rank_color};margin-left:8px;
                                 flex-shrink:0">{p['veces']}×</span>
                  </div>
                  <div style="background:var(--border);border-radius:3px;height:5px">
                    <div style="width:{bar_w}%;background:{rank_color};
                                border-radius:3px;height:5px"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.82rem">'
                '✅ Sin faltantes registrados.</p>',
                unsafe_allow_html=True,
            )

    with col_sucs:
        st.markdown('<p class="sec-label">Sucursales con más carga</p>',
                    unsafe_allow_html=True)
        sucs = top_sucursales_carga(items_con_analytics, top_n=10)
        if sucs:
            max_l = sucs[0]["lineas"]
            for i, s in enumerate(sucs):
                bar_w = max(6, int(s["lineas"] / max_l * 100))
                c_bar = AZUL if i < 3 else AZUL_CLARO
                st.markdown(f"""
                <div style="margin-bottom:6px">
                  <div style="display:flex;align-items:center;
                              justify-content:space-between;margin-bottom:2px">
                    <span style="font-size:0.8rem;color:var(--text);
                                 flex:1;min-width:0;overflow:hidden;
                                 text-overflow:ellipsis;white-space:nowrap"
                          title="{s['sucursal']}">{s['sucursal'][:38]}</span>
                    <span style="font-size:0.75rem;font-weight:700;
                                 color:{c_bar};margin-left:8px;
                                 flex-shrink:0">{s['lineas']} líns.</span>
                  </div>
                  <div style="background:var(--border);border-radius:3px;height:5px">
                    <div style="width:{bar_w}%;background:{c_bar};
                                border-radius:3px;height:5px"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<p style="color:var(--text-muted);font-size:0.82rem">'
                'Sin datos de sucursales.</p>',
                unsafe_allow_html=True,
            )

    # ── Detalle por cruce (expandible) ────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    with st.expander("Ver detalle por cruce"):
        for item in items_con_analytics:
            snap = item.get("analytics", {})
            pct_i = snap.get("pct_cobertura", 0)
            c_i   = VERDE if pct_i >= 90 else (AMARILLO if pct_i >= 70 else ROSA)
            n_sin = len(snap.get("productos_sin_cob", []))
            multi = snap.get("pedidos_multisucursal", 0)
            st.markdown(f"""
            <div style="border-left:3px solid {c_i};padding:8px 12px;
                        margin-bottom:8px;background:var(--card-bg);border-radius:4px">
              <div style="display:flex;align-items:center;
                          justify-content:space-between;margin-bottom:4px">
                <span style="font-weight:700;font-size:0.85rem">{item['id']}
                  &nbsp;·&nbsp;
                  <span style="color:{c_i}">{pct_i}% cobertura</span>
                </span>
                <span style="font-size:0.75rem;color:var(--text-muted)">{item['hora']}</span>
              </div>
              <div style="font-size:0.77rem;color:var(--text-muted);
                          display:flex;gap:16px;flex-wrap:wrap">
                <span>📦 {snap.get('pedidos_unicos','—')} pedidos</span>
                <span>🏪 {snap.get('n_sucursales','—')} sucursales</span>
                <span>{'⚠️ ' + str(n_sin) + ' sin cob.' if n_sin else '✅ Sin faltantes'}</span>
                {'<span>🔀 ' + str(multi) + ' pedidos multi-sucursal</span>' if multi else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)


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
#  IMAGEN DE PRODUCTO — Open Food Facts / Open Beauty Facts
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=86400, show_spinner=False)
def _imagen_producto(gtin_raw: str) -> str | None:
    """
    Busca la imagen frontal del producto en Open Food Facts (o Open Beauty Facts)
    usando el GTIN/EAN. Resultado cacheado 24 h para no repetir llamadas.
    Retorna la URL de la imagen o None si no se encuentra.
    """
    if not gtin_raw or gtin_raw in ("nan", "None", ""):
        return None
    # Si hay múltiples GTINs separados por coma, usar solo el primero
    gtin = gtin_raw.split(",")[0].strip()
    if not gtin:
        return None
    try:
        import urllib.request, json as _json
        for base in (
            "https://world.openfoodfacts.org",
            "https://world.openbeautyfacts.org",
        ):
            url = f"{base}/api/v2/product/{gtin}?fields=image_front_url,image_url"
            req = urllib.request.Request(url, headers={"User-Agent": "GlobalFarmacias/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = _json.loads(resp.read().decode())
            if data.get("status") == 1:
                prod = data.get("product", {})
                img = prod.get("image_front_url") or prod.get("image_url")
                if img:
                    return img
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════
#  PÁGINA: VISTA CADETE
# ════════════════════════════════════════════════════════════

def _page_cadete(cfg):
    # ── Marcar sesión cadete activa en servidor ────────────
    srv = _servidor_estado()
    srv["sesion_activa"] = True

    df_ruta = st.session_state.df_ruta_editable
    if df_ruta is None or df_ruta.empty:
        st.markdown("""
        <div class="page-hdr">
          <div><p class="page-title">🚴 Vista Cadete</p></div>
        </div>
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
        ["Búsqueda", "Encontrado", "Mal stock", "No encontrado",
         "Llamar a suc", "Requiere revisión", "Mal stock - Resuelto", "Llamar cliente"])

    ENC_SET = {"Encontrado", "Mal stock - Resuelto"}

    # ── Estado actual de cada ítem ─────────────────────────
    estados_actuales = {
        idx: st.session_state.estados_cadete.get(
            idx, str(df.at[idx, "Estado de búsqueda"])
            if "Estado de búsqueda" in df.columns else "Búsqueda")
        for idx in df.index
    }
    obs_cadete: dict = st.session_state.get("observaciones_cadete", {})

    # ── Métricas globales ──────────────────────────────────
    farmacias_validas = [f for f in df["Farmacia"].unique()
                         if f != "— SIN COBERTURA —"] if "Farmacia" in df.columns else []
    total       = len([i for i in df.index if df.at[i, "Farmacia"] != "— SIN COBERTURA —"])
    encontrados = sum(1 for i, v in estados_actuales.items()
                      if v in ENC_SET and df.at[i, "Farmacia"] != "— SIN COBERTURA —")
    pendientes  = sum(1 for i, v in estados_actuales.items()
                      if v not in ENC_SET and v not in {"No encontrado","Mal stock","Sin cobertura"}
                      and df.at[i, "Farmacia"] != "— SIN COBERTURA —")
    pct         = int(encontrados / total * 100) if total > 0 else 0
    color_pct   = VERDE if pct == 100 else (AZUL if pct > 0 else "#888")

    # ── Header compacto ────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:10px 0 6px;border-bottom:1px solid var(--border-color);margin-bottom:10px">
      <span style="font-size:1.05rem;font-weight:700;color:var(--text-primary)">
        🚴 Vista Cadete
      </span>
      <span style="font-size:1.5rem;font-weight:800;color:{color_pct}">{pct}%</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Progreso top ───────────────────────────────────────
    bar_w = max(3, pct)
    st.markdown(f"""
    <div style="background:var(--border-color);border-radius:6px;height:8px;
                overflow:hidden;margin-bottom:6px">
      <div style="height:8px;border-radius:6px;width:{bar_w}%;
           background:linear-gradient(90deg,{AZUL},{VERDE});transition:width 0.4s"></div>
    </div>
    <div style="display:flex;gap:20px;font-size:0.8rem;color:var(--text-muted);margin-bottom:12px">
      <span>✅ <strong style="color:{VERDE}">{encontrados}</strong> encontrados</span>
      <span>⏳ <strong>{pendientes}</strong> pendientes</span>
      <span>🏪 <strong>{len(farmacias_validas)}</strong> farmacias</span>
    </div>
    """, unsafe_allow_html=True)

    # ── CSS: padding inferior para la barra sticky ─────────
    st.markdown("<style>.block-container{padding-bottom:72px!important}</style>",
                unsafe_allow_html=True)

    # ── Filtros ────────────────────────────────────────────
    opciones_farm = ["Todas"] + [f for f in farmacias_validas]
    pedidos_lista = sorted({str(v) for v in df.get("N° Pedido", pd.Series()).unique()
                            if str(v) not in ("", "nan", "None")})
    opciones_ped  = ["Todos"] + pedidos_lista
    opciones_est  = ["Todos"] + [
        "Pendiente", "Encontrado", "No encontrado", "Mal stock",
        "Requiere revisión", "Llamar a suc",
    ]

    fc, pc, ec = st.columns(3)
    filtro_farm  = fc.selectbox("🏪 Sucursal",  opciones_farm, key="cad_filtro_farm")
    filtro_ped   = pc.selectbox("📋 Pedido",     opciones_ped,  key="cad_filtro_ped")
    filtro_est   = ec.selectbox("🔵 Estado",     opciones_est,  key="cad_filtro_est")

    # ── Acciones: descarga y reset ─────────────────────────
    res_data = st.session_state.ultimo_resultado
    col_dl, col_reset = st.columns([5, 1])
    with col_dl:
        if res_data:
            excel_bytes = _excel_a_bytes(df, res_data.get("df_sin_stock", pd.DataFrame()),
                                         estados_opciones)
            st.download_button(
                label="📥  Descargar Excel",
                data=excel_bytes,
                file_name=res_data.get("filename", "planilla_cadete.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    with col_reset:
        if st.button("↩️ Reset", use_container_width=True, help="Resetear todos los estados"):
            _inicializar_gestor(st.session_state.get("df_ruta_editable"))
            st.session_state["observaciones_cadete"] = {}
            srv["estados_cadete"] = {}
            srv["ultima_actualizacion"] = None
            srv["sesion_activa"] = True

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Helpers locales ────────────────────────────────────
    def _estado_para_filtro(estado: str) -> str:
        """Normaliza un estado al valor del filtro."""
        if estado in ENC_SET:           return "Encontrado"
        if estado == "Búsqueda":        return "Pendiente"
        if estado == "Requiere revisión": return "Requiere revisión"
        return estado

    def _confirmar_con_obs(idx: int, nuevo_estado: str):
        """Aplica el estado y guarda la observación actual del campo."""
        obs = st.session_state.get(f"obs_{idx}", "").strip()
        if obs:
            st.session_state.setdefault("observaciones_cadete", {})[idx] = obs
        _set_estado_cadete(idx, nuevo_estado, motivo=obs)

    # ── Loop por farmacia ──────────────────────────────────
    todas_farmacias = list(df["Farmacia"].unique()) if "Farmacia" in df.columns else []

    for i_farm, farmacia in enumerate(todas_farmacias):
        es_sin_cob = farmacia == "— SIN COBERTURA —"

        # Aplicar filtro de sucursal
        if filtro_farm != "Todas" and farmacia != filtro_farm:
            continue

        df_farm    = df[df["Farmacia"] == farmacia]
        zona_label = str(df_farm.iloc[0].get("Zona", "")) if not df_farm.empty else ""

        # Aplicar filtro de pedido
        if filtro_ped != "Todos" and "N° Pedido" in df_farm.columns:
            df_farm = df_farm[df_farm["N° Pedido"].astype(str) == filtro_ped]
            if df_farm.empty:
                continue

        # Aplicar filtro de estado
        if filtro_est != "Todos":
            df_farm = df_farm[df_farm.index.map(
                lambda i: _estado_para_filtro(estados_actuales.get(i, "Búsqueda")) == filtro_est
            )]
            if df_farm.empty:
                continue

        enc_farm   = sum(1 for i in df_farm.index
                         if estados_actuales.get(i, "") in ENC_SET)
        total_farm = len(df_farm)
        farm_lista = enc_farm >= total_farm and not es_sin_cob

        zona_cls = {"Deposito":"zona-0","NQN Capital":"zona-1",
                    "Centenario/Plottier":"zona-2","Cercana":"zona-3",
                    "Remota":"zona-4"}.get(zona_label, "zona-1")
        if es_sin_cob:
            zona_cls = "zona-4"

        hdr_bg    = "#059669" if farm_lista else ("#BE123C" if es_sin_cob else AZUL)
        check_icon = "✅" if farm_lista else "🏪"
        pct_farm   = int(enc_farm / total_farm * 100) if total_farm > 0 else 0

        st.markdown(f"""
        <div class="cadete-farmacia-hdr" style="background:{hdr_bg}">
          {check_icon} &nbsp; <strong>{farmacia}</strong>
          &nbsp; <span class="{zona_cls}" style="flex-shrink:0">{zona_label}</span>
          <span class="cadete-farmacia-badge">{enc_farm}/{total_farm} &nbsp; {pct_farm}%</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Ítems sin cobertura ────────────────────────────
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
                  <span class="est-badge eb-llamarcliente">Sin cobertura</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            continue

        # ── Ítems normales ─────────────────────────────────
        for idx, row in df_farm.iterrows():
            producto  = str(row.get("Producto", ""))[:60]
            variante  = str(row.get("Tipo / Variante", "") or "")
            nro_ped   = str(row.get("N° Pedido", "") or "")
            fecha_ped = str(row.get("Fecha Pedido", "") or "")
            hora_ped  = str(row.get("Hora Pedido",  "") or "")
            cantidad  = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
            gtin_raw  = str(row.get("GTIN", "") or "")
            zetti_id  = str(row.get("Zetti (ID)", "") or "")
            gtin_key  = str(row.get("_gtin_key", gtin_raw or zetti_id) or "")
            sosp      = row.get("⚠️ Stock", "") == "⚠️ Verificar"
            zona_r    = zona_label == "Remota"
            estado_og  = str(row.get("Estado de búsqueda", "Búsqueda"))
            estado_act = estados_actuales.get(idx, estado_og)
            encontrado = estado_act in ENC_SET
            problema   = estado_act in {"Mal stock", "No encontrado", "Llamar cliente"}
            obs_guardada = obs_cadete.get(idx, "")

            # Colores por estado
            if encontrado:
                border_c = VERDE
                name_style = f"font-size:1rem;font-weight:700;color:{VERDE};text-decoration:line-through;margin:0"
            elif problema:
                border_c = AMARILLO
                name_style = "font-size:1rem;font-weight:700;color:#B45309;margin:0"
            elif estado_act in {"Requiere revisión", "En revisión"}:
                border_c = AMARILLO
                name_style = "font-size:1rem;font-weight:700;color:#92400E;margin:0"
            else:
                border_c = "var(--border)"
                name_style = "font-size:1rem;font-weight:700;color:var(--text-primary);margin:0"

            # ── Card container ─────────────────────────────
            with st.container():
                st.markdown(
                    f'<div style="border-left:4px solid {border_c};'
                    f'background:var(--card-bg);border-radius:8px;'
                    f'padding:10px 12px 6px;margin-bottom:2px">',
                    unsafe_allow_html=True,
                )

                # Fila 1: imagen + nombre + badge
                col_img, col_info = st.columns([1, 7])
                with col_img:
                    img_url = _imagen_producto(gtin_raw)
                    if img_url:
                        st.image(img_url, width=62)
                    else:
                        st.markdown(
                            '<div style="width:62px;height:62px;border-radius:6px;'
                            'background:var(--border);display:flex;align-items:center;'
                            'justify-content:center;font-size:1.6rem">💊</div>',
                            unsafe_allow_html=True,
                        )
                with col_info:
                    # Nombre + badge en la misma fila
                    badge = _badge_estado(estado_act)
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:flex-start;gap:8px">'
                        f'<p style="{name_style}">{producto}</p>'
                        f'<div style="flex-shrink:0">{badge}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    # Variante
                    if variante and variante not in ("nan", "None", ""):
                        st.markdown(
                            f'<p style="margin:0 0 4px;font-size:0.78rem;'
                            f'color:var(--text-muted)">{variante}</p>',
                            unsafe_allow_html=True,
                        )
                    # Cantidad + códigos
                    chip_parts = [f'<span class="cadete-qty">× {cantidad}</span>']
                    if nro_ped and nro_ped not in ("", "nan", "None"):
                        chip_parts.append(f'<span class="cadete-codigo-chip">Ped. #{nro_ped}</span>')
                    if gtin_raw and gtin_raw not in ("nan", "None", ""):
                        chip_parts.append(f'<span class="cadete-codigo-chip">GTIN {gtin_raw[:22]}</span>')
                    if zetti_id and zetti_id not in ("nan", "None", ""):
                        chip_parts.append(f'<span class="cadete-codigo-chip">SKU {zetti_id}</span>')
                    if fecha_ped and fecha_ped not in ("", "nan", "None"):
                        hora_txt = f" {hora_ped}" if hora_ped and hora_ped not in ("", "nan", "None") else ""
                        chip_parts.append(f'<span class="cadete-codigo-chip">📅 {fecha_ped}{hora_txt}</span>')
                    st.markdown(
                        '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">'
                        + " ".join(chip_parts) + "</div>",
                        unsafe_allow_html=True,
                    )
                    # Alertas
                    if sosp:
                        st.markdown(
                            '<div class="cadete-alerta-warn">⚠️ Stock sospechoso — verificar cantidad</div>',
                            unsafe_allow_html=True,
                        )
                    if zona_r:
                        st.markdown(
                            '<div class="cadete-alerta-info">📞 Sucursal remota — llamar antes de ir</div>',
                            unsafe_allow_html=True,
                        )
                    # Observación guardada (estado encontrado)
                    if obs_guardada and encontrado:
                        st.caption(f"💬 {obs_guardada}")

                st.markdown("</div>", unsafe_allow_html=True)

            # ── Controles por estado ───────────────────────
            if encontrado:
                c_undo, c_obs_enc, _ = st.columns([2, 3, 2])
                with c_undo:
                    if st.button("↩️ Deshacer", key=f"undo_{idx}", use_container_width=True):
                        _set_estado_cadete(idx, "Búsqueda", forzar=True)
                with c_obs_enc:
                    if obs_guardada:
                        st.caption(f"💬 {obs_guardada}")
            else:
                # Campo de observación
                obs_val = st.text_input(
                    "💬 Observación (opcional)",
                    value=st.session_state.get(f"obs_{idx}", ""),
                    key=f"obs_{idx}",
                    placeholder="Ej: Stock en estante B, llamar a Marta...",
                    label_visibility="collapsed",
                )

                # Botones de acción
                if zona_r:
                    b1, b2, b3, b4 = st.columns(4)
                    with b1:
                        if st.button("✅ Encontrado", key=f"enc_{idx}",
                                     use_container_width=True, type="primary"):
                            _confirmar_con_obs(idx, "Encontrado")
                    with b2:
                        if st.button("📦 Mal stock", key=f"mal_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "Mal stock")
                    with b3:
                        if st.button("📞 Llamar", key=f"call_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "Llamar a suc")
                    with b4:
                        if st.button("🔍 Revisar", key=f"rev_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "Requiere revisión")
                else:
                    b1, b2, b3, b4 = st.columns(4)
                    with b1:
                        if st.button("✅ Encontrado", key=f"enc_{idx}",
                                     use_container_width=True, type="primary"):
                            _confirmar_con_obs(idx, "Encontrado")
                    with b2:
                        if st.button("📦 Mal stock", key=f"mal_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "Mal stock")
                    with b3:
                        if st.button("❌ No encontrado", key=f"noenc_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "No encontrado")
                    with b4:
                        if st.button("🔍 Revisar", key=f"rev_{idx}",
                                     use_container_width=True):
                            _confirmar_con_obs(idx, "Requiere revisión")

                # ── Ver alternativas ───────────────────────
                if estado_act in {"No encontrado", "Mal stock", "Requiere revisión"}:
                    stk_por_prod = st.session_state.get("stock_por_producto", {})
                    mapa_stk     = st.session_state.get("mapa_stock_guardado", {})
                    col_nodo     = mapa_stk.get("nodo", "nodo")
                    col_stk_c    = mapa_stk.get("stock", "stock")
                    df_alt       = stk_por_prod.get(gtin_key)

                    if df_alt is not None and not df_alt.empty and col_nodo in df_alt.columns:
                        key_alt = f"ver_alt_{idx}"
                        if st.session_state.get(key_alt, False):
                            from src.optimizer import obtener_opciones_sucursal
                            zonas_cfg   = cfg.get("zonas", {})
                            zona_labels = {int(k): v for k, v in
                                           cfg.get("zona_labels", {}).items()}
                            opciones = obtener_opciones_sucursal(
                                df_alt, col_nodo, col_stk_c,
                                zonas_cfg, zona_labels, max_opciones=5,
                            )
                            if opciones:
                                st.markdown(
                                    "<div style='font-size:0.82rem;font-weight:600;"
                                    "color:var(--text-muted);margin:4px 0 2px'>"
                                    "🔄 Alternativas disponibles:</div>",
                                    unsafe_allow_html=True
                                )
                                for op in opciones:
                                    zona_op = op.get("zona", "")
                                    stock_op = op.get("stock", 0)
                                    nodo_op  = op.get("nodo", "")
                                    st.markdown(
                                        f"<div style='font-size:0.83rem;padding:3px 8px;"
                                        f"background:var(--bg-card);border-radius:6px;"
                                        f"border:1px solid var(--border-color);margin-bottom:3px'>"
                                        f"🏪 <strong>{nodo_op}</strong> — "
                                        f"{stock_op} uds · {zona_op}</div>",
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.caption("Sin alternativas con stock disponible.")
                            if st.button("▲ Cerrar alternativas", key=f"cerrar_alt_{idx}",
                                         use_container_width=True):
                                st.session_state[key_alt] = False
                        else:
                            if st.button("🔄 Ver alternativas", key=f"abrir_alt_{idx}",
                                         use_container_width=True):
                                st.session_state[key_alt] = True

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Auto-avance al completar farmacia
        if farm_lista and i_farm < len(todas_farmacias) - 1:
            siguiente_farm = next(
                (f for f in todas_farmacias[i_farm + 1:] if f != "— SIN COBERTURA —"), None
            )
            if siguiente_farm:
                st.success(f"✅ Farmacia completa — siguiente: **{siguiente_farm}**")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

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
    elif pagina == "analitica":      _page_analitica()
    elif pagina == "cadete":         _page_cadete(cfg)
    elif pagina == "configuracion":  _page_configuracion(cfg)
    elif pagina == "ayuda":          _page_ayuda()


if __name__ == "__main__":
    main()
