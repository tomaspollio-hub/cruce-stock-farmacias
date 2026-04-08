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

    _agregar_historial(archivo_pedidos.name, archivo_stock.name,
                       len(df_ruta), len(df_sin_stock), excel_bytes, filename)

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
            cantidad  = row.get("Unidades a buscar", row.get("Cantidad pedida", "?"))
            gtin_raw  = str(row.get("GTIN", "") or "")
            zetti_id  = str(row.get("Zetti (ID)", "") or "")
            gtin_key  = str(row.get("_gtin_key", gtin_raw or zetti_id) or "")
            sosp      = row.get("⚠️ Stock", "") == "⚠️ Verificar"
            zona_r    = zona_label == "Remota"
            estado_og = str(row.get("Estado de búsqueda", "Búsqueda"))
            estado_act = estados_actuales.get(idx, estado_og)
            encontrado = estado_act in ENC_SET
            problema   = estado_act in {"Mal stock", "No encontrado", "Llamar cliente"}

            # Fondo por estado
            if encontrado:
                item_bg    = "#F0FDF4"; prod_style = "color:#059669;text-decoration:line-through"
            elif problema:
                item_bg    = "#FFF8E1"; prod_style = "color:#B45309"
            elif estado_act in {"Requiere revisión", "En revisión"}:
                item_bg    = "#FFFBEB"; prod_style = "color:#92400E"
            else:
                item_bg    = "var(--bg-card)"; prod_style = "color:var(--text-primary)"

            # Chips de código
            chips = ""
            if gtin_raw and gtin_raw not in ("nan", "None", ""):
                chips += f'<span class="cadete-codigo-chip">GTIN {gtin_raw[:20]}</span>'
            if zetti_id and zetti_id not in ("nan", "None", ""):
                chips += f'<span class="cadete-codigo-chip">Z: {zetti_id}</span>'
            if nro_ped and nro_ped not in ("", "nan", "None"):
                chips += f'<span class="cadete-codigo-chip">Ped. #{nro_ped}</span>'

            alertas_html = ""
            if sosp:
                alertas_html += '<div class="cadete-alerta-warn">⚠️ Stock sospechoso — verificar cantidad</div>'
            if zona_r:
                alertas_html += '<div class="cadete-alerta-info">📞 Sucursal remota — llamar antes de ir</div>'

            obs_guardada = obs_cadete.get(idx, "")

            st.markdown(f"""
            <div class="cadete-item" style="background:{item_bg}">
              <div style="display:flex;justify-content:space-between;
                          align-items:flex-start;gap:10px">
                <div style="flex:1;min-width:0">
                  <div class="cadete-producto" style="{prod_style}">{producto}</div>
                  {"<div class='cadete-variante'>" + variante + "</div>"
                    if variante and variante not in ("nan","None","") else ""}
                  <div class="cadete-codigos">
                    <span class="cadete-qty">× {cantidad}</span>
                    {"&nbsp;" + chips if chips else ""}
                  </div>
                  {alertas_html}
                  {"<div style='font-size:0.78rem;color:#64748B;margin-top:3px'>💬 " + obs_guardada + "</div>"
                    if obs_guardada and encontrado else ""}
                </div>
                <div style="flex-shrink:0;padding-top:2px">{_badge_estado(estado_act)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

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
    elif pagina == "cadete":         _page_cadete(cfg)
    elif pagina == "configuracion":  _page_configuracion(cfg)
    elif pagina == "ayuda":          _page_ayuda()


if __name__ == "__main__":
    main()
