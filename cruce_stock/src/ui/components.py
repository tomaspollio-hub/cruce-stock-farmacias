"""
components.py
Componentes UI reutilizables: badges de estado/zona y tabla mejorada.
"""
import pandas as pd
import streamlit as st


def _badge_estado(estado: str) -> str:
    mapa = {
        "Búsqueda":              "eb-busqueda",
        "Encontrado":            "eb-encontrado",
        "Mal stock":             "eb-malstock",
        "No encontrado":         "eb-llamarcliente",
        "Requiere revisión":     "eb-malstock",
        "Llamar a suc":          "eb-llamarsuc",
        "Mal stock - Resuelto":  "eb-resuelto",
        "Llamar cliente":        "eb-llamarcliente",
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
