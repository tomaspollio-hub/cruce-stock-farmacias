"""
optimizer.py
Algoritmo greedy de cobertura mínima de sucursales.

Prioridades de zona (0 = mayor prioridad):
  0 — Depósito ecommerce (APT-ECOMMERCE-NQN)
  1 — Neuquén Capital
  2 — Centenario / Plottier
  3 — Zonas cercanas (Añelo, El Chañar)
  4 — Remotas (Cutral Co, Zapala, Puerto Madryn) → estado "Llamar a suc"

Mejoras incluidas:
  - N° de pedido visible en cada fila
  - Agrupación por pedido y por sucursal (ruta cadete)
  - Flag de stock sospechoso (umbral configurable)
"""

from __future__ import annotations
import unicodedata
import logging
import pandas as pd

# Logger estándar — sin dependencia de src.logger
logger = logging.getLogger(__name__)

PRIORIDAD_DEFAULT = 1
PRIORIDAD_REMOTA  = 4


def _normalizar(valor) -> str:
    """Strip, lowercase, quitar tildes. Sin dependencias externas."""
    if valor is None:
        return ""
    try:
        import pandas as _pd
        if _pd.isna(valor):
            return ""
    except Exception:
        pass
    nfkd = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ════════════════════════════════════════════════════════════
#  CLASIFICACIÓN DE ZONA
# ════════════════════════════════════════════════════════════

def _prioridad_zona(nodo: str, zonas_cfg: dict) -> int:
    nodo_n = _normalizar(nodo)
    keys_ordenadas = [
        "prioridad_0_deposito",
        "prioridad_1_nqn_capital",
        "prioridad_2_centenario_plottier",
        "prioridad_3_cercanas",
        "prioridad_4_remotas",
    ]
    for prioridad, key in enumerate(keys_ordenadas):
        for frag in zonas_cfg.get(key, []):
            if _normalizar(frag) in nodo_n:
                return prioridad

    logger.warning(
        f"Nodo '{nodo}' no coincide con ninguna zona. "
        f"Asignado prioridad {PRIORIDAD_DEFAULT} (NQN Capital) por defecto."
    )
    return PRIORIDAD_DEFAULT


def _zona_label(prioridad: int, labels_cfg: dict) -> str:
    return (
        labels_cfg.get(prioridad)
        or labels_cfg.get(str(prioridad))
        or labels_cfg.get(int(prioridad))
        or f"Zona {prioridad}"
    )


# ════════════════════════════════════════════════════════════
#  OPTIMIZACIÓN POR PRODUCTO
# ════════════════════════════════════════════════════════════

def optimizar_producto(
    gtin_key: str,
    unidades_requeridas: int,
    df_stock_producto: pd.DataFrame,
    col_nodo: str,
    col_stock: str,
    zonas_cfg: dict,
    zona_labels: dict,
    max_sucursales: int = 3,
    umbral_stock_sospechoso: int = 200,
) -> list[dict]:
    """
    Devuelve la lista mínima de sucursales para cubrir la demanda de un producto.
    Incluye flag de stock sospechoso si el stock supera el umbral configurado.
    """
    if df_stock_producto.empty or unidades_requeridas <= 0:
        return []

    tabla = (
        df_stock_producto
        .copy()
        .assign(
            _stock=pd.to_numeric(df_stock_producto[col_stock], errors="coerce").fillna(0).astype(int),
        )
        .groupby(col_nodo, as_index=False)
        .agg(
            _nodo_raw=(col_nodo, "first"),
            stock_total=("_stock", "sum"),
        )
    )

    tabla["prioridad"]  = tabla["_nodo_raw"].apply(lambda n: _prioridad_zona(n, zonas_cfg))
    tabla["zona_label"] = tabla["prioridad"].apply(lambda p: _zona_label(p, zona_labels))
    tabla = tabla.sort_values(["prioridad", "stock_total"], ascending=[True, False])
    tabla = tabla[tabla["stock_total"] > 0].reset_index(drop=True)

    if tabla.empty:
        logger.warning(f"Sin stock disponible en ningún nodo para GTIN '{gtin_key}'")
        return []

    restante = unidades_requeridas
    asignaciones: list[dict] = []

    for _, fila in tabla.iterrows():
        if restante <= 0:
            break
        if len(asignaciones) >= max_sucursales:
            break

        nodo_nombre = fila["_nodo_raw"]
        stock_disp  = int(fila["stock_total"])
        prioridad   = int(fila["prioridad"])
        zona_lbl    = fila["zona_label"]

        unidades_tomar  = min(stock_disp, restante)
        restante       -= unidades_tomar

        estado_sugerido   = "Llamar a suc" if prioridad >= PRIORIDAD_REMOTA else "Búsqueda"
        stock_sospechoso  = stock_disp > umbral_stock_sospechoso

        asignaciones.append({
            "farmacia":            nodo_nombre,
            "stock_sucursal":      stock_disp,
            "unidades_asignadas":  unidades_tomar,
            "prioridad":           prioridad,
            "zona":                zona_lbl,
            "estado_busqueda":     estado_sugerido,
            "stock_sospechoso":    stock_sospechoso,
        })

    if restante > 0:
        logger.warning(
            f"GTIN '{gtin_key}': {restante} unidades sin cobertura "
            f"(pedido={unidades_requeridas}, cubierto={unidades_requeridas - restante})"
        )
        asignaciones.append({
            "farmacia":            "— SIN COBERTURA —",
            "stock_sucursal":      0,
            "unidades_asignadas":  restante,
            "prioridad":           99,
            "zona":                "—",
            "estado_busqueda":     "Llamar cliente",
            "stock_sospechoso":    False,
        })

    return asignaciones


# ════════════════════════════════════════════════════════════
#  OPCIONES PARA OVERRIDE MANUAL
# ════════════════════════════════════════════════════════════

def obtener_opciones_sucursal(
    df_stock_producto: pd.DataFrame,
    col_nodo: str,
    col_stock: str,
    zonas_cfg: dict,
    zona_labels: dict,
    max_opciones: int = 5,
) -> list[dict]:
    tabla = (
        df_stock_producto
        .copy()
        .assign(
            _stock=pd.to_numeric(df_stock_producto[col_stock], errors="coerce").fillna(0).astype(int),
        )
        .groupby(col_nodo, as_index=False)
        .agg(
            _nodo_raw=(col_nodo, "first"),
            stock_total=("_stock", "sum"),
        )
    )
    tabla["prioridad"]  = tabla["_nodo_raw"].apply(lambda n: _prioridad_zona(n, zonas_cfg))
    tabla["zona_label"] = tabla["prioridad"].apply(lambda p: _zona_label(p, zona_labels))
    tabla = (
        tabla[tabla["stock_total"] > 0]
        .sort_values(["prioridad", "stock_total"], ascending=[True, False])
        .head(max_opciones)
        .reset_index(drop=True)
    )

    return [
        {
            "nodo":      r["_nodo_raw"],
            "stock":     int(r["stock_total"]),
            "prioridad": int(r["prioridad"]),
            "zona":      r["zona_label"],
            "label":     f"{r['_nodo_raw']} — {int(r['stock_total'])} uds ({r['zona_label']})",
        }
        for _, r in tabla.iterrows()
    ]


# ════════════════════════════════════════════════════════════
#  ORDENAMIENTO DE LA PLANILLA
# ════════════════════════════════════════════════════════════

def ordenar_por_pedido(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vista 'por pedido': agrupa todos los productos del mismo
    pedido juntos. Dentro de cada pedido, ordena por prioridad
    de zona para que el cadete vea primero la sucursal más cercana.
    """
    if df.empty:
        return df
    cols_sort = []
    if "N° Pedido" in df.columns:
        cols_sort.append("N° Pedido")
    if "prioridad" in df.columns:
        cols_sort.append("prioridad")
    if "Farmacia" in df.columns:
        cols_sort.append("Farmacia")
    return df.sort_values(cols_sort).reset_index(drop=True) if cols_sort else df


def ordenar_por_ruta(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vista 'ruta del cadete': agrupa por sucursal para minimizar
    las paradas. Dentro de cada sucursal ordena por N° pedido.
    El resultado es la hoja de ruta óptima: el cadete va a una
    sucursal y busca TODOS los productos que necesita ahí.
    """
    if df.empty:
        return df
    cols_sort = []
    if "prioridad" in df.columns:
        cols_sort.append("prioridad")
    if "Farmacia" in df.columns:
        cols_sort.append("Farmacia")
    if "N° Pedido" in df.columns:
        cols_sort.append("N° Pedido")
    return df.sort_values(cols_sort).reset_index(drop=True) if cols_sort else df


# ════════════════════════════════════════════════════════════
#  PIPELINE PRINCIPAL
# ════════════════════════════════════════════════════════════

def construir_planilla(
    df_pedidos: pd.DataFrame,
    df_stock: pd.DataFrame,
    mapa_pedidos: dict,
    mapa_stock: dict,
    cfg: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Procesa todos los pedidos activos. Devuelve:
      - df_ruta            : planilla completa (ordenada por pedido por defecto)
      - df_sin_stock       : productos sin cobertura
      - stock_por_producto : {gtin_key → df} para override manual de sucursal
    """
    zonas_cfg    = cfg["zonas"]
    zona_labels  = {int(k): v for k, v in cfg.get("zona_labels", {}).items()}
    max_suc      = cfg["optimizacion"]["max_sucursales_por_producto"]
    umbral_sosp  = cfg["optimizacion"].get("stock_sospechoso_umbral", 200)
    estado_activo = cfg["pedidos"]["estado_activo"].lower()

    col_estado      = mapa_pedidos["estado"]
    col_nro_pedido  = mapa_pedidos.get("nro_pedido")   # puede ser None
    col_sku_ped     = mapa_pedidos["sku"]
    col_gtin_ped    = mapa_pedidos["gtin"]
    col_unidades    = mapa_pedidos["unidades"]
    col_producto    = mapa_pedidos["producto"]

    col_id_stock    = mapa_stock["id"]
    col_sku_stock   = mapa_stock["sku"]
    col_nodo        = mapa_stock["nodo"]
    col_stk         = mapa_stock["stock"]

    # ── Filtrar pedidos activos ──────────────────────────
    df_activos = df_pedidos[
        df_pedidos[col_estado].apply(lambda v: str(v).strip().lower()) == estado_activo
    ].copy()

    if df_activos.empty:
        logger.warning("No se encontraron pedidos con estado 'abierta'.")
        return pd.DataFrame(), pd.DataFrame(), {}

    logger.info(f"Pedidos activos: {len(df_activos)} filas | "
                f"Pedidos únicos: {df_activos[col_nro_pedido].nunique() if col_nro_pedido else 'N/D'}")

    from src.services.asignacion import asignar_producto_inteligente

    filas_ruta: list[dict]       = []
    filas_sin_stock: list[dict]  = []
    stock_por_producto: dict     = {}

    # Consolidación: registro de nodos ya asignados por pedido
    # {nro_pedido → set de nombres de farmacia asignadas}
    nodos_por_pedido: dict[str, set[str]] = {}

    for _, pedido in df_activos.iterrows():
        # N° de pedido
        nro_pedido = ""
        if col_nro_pedido and col_nro_pedido in pedido.index:
            nro_pedido = str(pedido[col_nro_pedido]).strip() if pd.notna(pedido[col_nro_pedido]) else ""

        sku_pedido  = str(pedido[col_sku_ped]).strip()  if pd.notna(pedido[col_sku_ped])  else ""
        gtin_pedido = str(pedido[col_gtin_ped]).strip() if pd.notna(pedido[col_gtin_ped]) else ""

        # Usar la columna pre-normalizada si existe (normalizar_pedidos la agrega)
        if "_unidades_int" in pedido.index:
            unidades = int(pedido["_unidades_int"])
        else:
            try:
                unidades = int(float(str(pedido[col_unidades]).strip()))
            except (ValueError, TypeError):
                unidades = 1
                logger.warning(f"Unidades no legibles para '{pedido[col_producto]}', asumiendo 1")

        nombre_producto = str(pedido[col_producto]) if pd.notna(pedido[col_producto]) else ""
        variante = ""
        if mapa_pedidos.get("variante") and mapa_pedidos["variante"] in pedido.index:
            val = pedido[mapa_pedidos["variante"]]
            variante = str(val) if pd.notna(val) else ""

        # ── Buscar en stock usando columnas normalizadas ─────
        # Precondición: df_pedidos y df_stock pasaron por normalizar_pedidos()
        # / normalizar_stock() de src.services.normalizacion.
        gtin_norm = str(pedido.get("_gtin_norm", "") or "").strip()
        sku_norm  = str(pedido.get("_sku_norm",  "") or "").strip()

        # Soporte GTINs múltiples separados por coma
        gtins_norm = [g.strip() for g in gtin_norm.split(",") if g.strip()]

        # Prioridad 1: match por GTIN (pedido) vs _id_norm / _sku_norm (stock)
        if gtins_norm:
            df_encontrado = df_stock[
                df_stock["_id_norm"].isin(gtins_norm) |
                df_stock["_sku_norm"].isin(gtins_norm)
            ]
        else:
            df_encontrado = pd.DataFrame(columns=df_stock.columns)

        # Prioridad 2: fallback por SKU si no hubo match por GTIN
        if df_encontrado.empty and sku_norm:
            df_encontrado = df_stock[
                (df_stock["_id_norm"] == sku_norm) |
                (df_stock["_sku_norm"] == sku_norm)
            ]

        gtin_key = gtin_norm or sku_norm or gtin_pedido or sku_pedido

        if df_encontrado.empty:
            logger.warning(
                f"Sin match: '{nombre_producto}' (SKU={sku_pedido}, GTIN={gtin_pedido})"
            )
            filas_sin_stock.append({
                "N° Pedido": nro_pedido,
                "Producto":  nombre_producto,
                "Variante":  variante,
                "SKU":       sku_pedido,
                "GTIN":      gtin_pedido,
                "Unidades":  unidades,
                "Motivo":    "Sin match en archivo de stock",
            })
            continue

        stock_por_producto[gtin_key] = df_encontrado.copy()

        # ── Asignación inteligente de sucursales ─────────
        nodos_ya = nodos_por_pedido.get(nro_pedido, set())
        asignaciones = asignar_producto_inteligente(
            gtin_key=gtin_key,
            unidades_requeridas=unidades,
            df_stock_producto=df_encontrado,
            col_nodo=col_nodo,
            col_stock=col_stk,
            zonas_cfg=zonas_cfg,
            zona_labels=zona_labels,
            cfg=cfg,
            max_sucursales=max_suc,
            umbral_stock_sospechoso=umbral_sosp,
            nodos_ya_asignados=nodos_ya,
        )

        # Actualizar nodos asignados para este pedido
        for asig in asignaciones:
            if asig["farmacia"] != "— SIN COBERTURA —":
                nodos_por_pedido.setdefault(nro_pedido, set()).add(asig["farmacia"])

        if not asignaciones:
            filas_sin_stock.append({
                "N° Pedido": nro_pedido,
                "Producto":  nombre_producto,
                "Variante":  variante,
                "SKU":       sku_pedido,
                "GTIN":      gtin_pedido,
                "Unidades":  unidades,
                "Motivo":    "Stock 0 en todas las sucursales",
            })
            continue

        nombre_zetti = ""
        col_nombre_stock = mapa_stock.get("nombre")
        if col_nombre_stock and col_nombre_stock in df_encontrado.columns:
            nombre_zetti = str(df_encontrado.iloc[0][col_nombre_stock])

        for asig in asignaciones:
            filas_ruta.append({
                "N° Pedido":          nro_pedido,
                "Producto":           nombre_producto,
                "Tipo / Variante":    variante,
                "Zetti (ID)":         sku_pedido,
                "GTIN":               gtin_pedido,
                "Nombre Zetti":       nombre_zetti,
                "Cantidad pedida":    unidades,
                "Farmacia":           asig["farmacia"],
                "Stock sucursal":     asig["stock_sucursal"],
                "Unidades a buscar":  asig["unidades_asignadas"],
                "Zona":               asig["zona"],
                "⚠️ Stock":           "⚠️ Verificar" if asig["stock_sospechoso"] else "",
                "Estado de búsqueda": asig["estado_busqueda"],
                # internos (no van al Excel)
                "_gtin_key":          gtin_key,
                "prioridad":          asig["prioridad"],
                "_criterio":          asig.get("criterio_asignacion", ""),
                "_tier":              asig.get("tier", 2),
                "_consolida_pedido":  asig.get("consolida_pedido", False),
            })

    df_ruta      = pd.DataFrame(filas_ruta)
    df_sin_stock = pd.DataFrame(filas_sin_stock)

    # Ordenar por pedido por defecto
    if not df_ruta.empty:
        df_ruta = ordenar_por_pedido(df_ruta)

    n_sosp = (df_ruta["⚠️ Stock"] == "⚠️ Verificar").sum() if not df_ruta.empty else 0
    if n_sosp:
        logger.warning(
            f"{n_sosp} fila(s) con stock sospechoso (>{umbral_sosp} uds). "
            f"Verificar antes de enviar al cadete."
        )

    logger.info(f"Filas en planilla: {len(df_ruta)} | Sin cobertura: {len(df_sin_stock)}")

    return df_ruta, df_sin_stock, stock_por_producto
