"""
matching.py
Cruce entre pedidos y stock con trazabilidad completa.

Jerarquía de matching:
  1. Match exacto por GTIN  (pedido._gtin_norm vs stock._id_norm / stock._sku_norm)
  2. Fallback por SKU       (pedido._sku_norm  vs stock._id_norm / stock._sku_norm)
  3. Sin match              → marcado con tipo_match="sin_match"

Requiere que ambos DataFrames hayan pasado por normalizar_pedidos() /
normalizar_stock() de normalizacion.py (columnas _gtin_norm, _sku_norm, etc.)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
#  ESTRUCTURAS DE RESULTADO
# ════════════════════════════════════════════════════════════

@dataclass
class LineaMatching:
    """Resultado de matching para una línea del pedido."""
    nro_pedido:        str
    producto:          str
    gtin:              str
    sku:               str
    cantidad_pedida:   int

    match_encontrado:  bool
    tipo_match:        str          # "gtin" | "sku" | "sin_match"

    registros_stock:   int          # filas de stock que matchearon
    nodos_disponibles: list[str]    # sucursales con stock > 0
    stock_total:       int          # suma de stock en todos los nodos

    observacion:       str = ""     # mensaje libre si hay advertencia/error
    gtin_duplicado:    bool = False  # mismo GTIN en > 1 nodo con stock
    sku_duplicado:     bool = False  # mismo SKU  en > 1 nodo con stock
    ambiguo:           bool = False  # GTIN matchea con > 1 producto distinto

    # Referencia al sub-DataFrame de stock para uso posterior (no serializable)
    df_stock: object = field(default=None, repr=False)


@dataclass
class ResumenMatching:
    """Métricas globales del cruce."""
    total_lineas:    int = 0
    con_match_gtin:  int = 0
    con_match_sku:   int = 0
    sin_match:       int = 0
    ambiguos:        int = 0
    gtin_duplicados: int = 0
    sku_duplicados:  int = 0

    def pct_cobertura(self) -> float:
        """Porcentaje de líneas con algún match."""
        if not self.total_lineas:
            return 0.0
        return round((self.con_match_gtin + self.con_match_sku) / self.total_lineas * 100, 1)


@dataclass
class ResultadoMatching:
    lineas:  list[LineaMatching] = field(default_factory=list)
    resumen: ResumenMatching     = field(default_factory=ResumenMatching)


# ════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ════════════════════════════════════════════════════════════

def ejecutar_matching(
    df_pedidos:   pd.DataFrame,
    df_stock:     pd.DataFrame,
    mapa_pedidos: dict,
    mapa_stock:   dict,
    cfg:          dict,
) -> ResultadoMatching:
    """
    Cruza pedidos activos con stock. Devuelve un ResultadoMatching con
    trazabilidad por línea y un resumen global.

    Precondiciones:
      - df_pedidos debe tener columnas _gtin_norm, _sku_norm, _unidades_int
        (agregadas por normalizar_pedidos())
      - df_stock debe tener columnas _id_norm, _sku_norm
        (agregadas por normalizar_stock())
    """
    col_estado   = mapa_pedidos["estado"]
    col_nro_ped  = mapa_pedidos.get("nro_pedido")
    col_producto = mapa_pedidos["producto"]
    col_gtin_ped = mapa_pedidos.get("gtin")
    col_sku_ped  = mapa_pedidos.get("sku")
    col_nodo     = mapa_stock["nodo"]
    col_stk      = mapa_stock["stock"]

    estado_activo = cfg["pedidos"]["estado_activo"].lower()

    # ── Filtrar pedidos activos ──────────────────────────────
    df_activos = df_pedidos[
        df_pedidos[col_estado].apply(lambda v: str(v).strip().lower()) == estado_activo
    ].copy()

    # ── Construir índices inversos sobre el stock ─────────────
    # {valor_norm → [índices de fila en df_stock]}
    idx_por_id  = _construir_indice(df_stock, "_id_norm")
    idx_por_sku = _construir_indice(df_stock, "_sku_norm")

    # Detectar GTIN ambiguos: un mismo _id_norm mapea a >1 nombre de producto
    col_nombre_stock = mapa_stock.get("nombre")
    gtins_ambiguos: set[str] = set()
    if col_nombre_stock and col_nombre_stock in df_stock.columns:
        for gtin_n, filas in idx_por_id.items():
            if gtin_n and df_stock.loc[filas, col_nombre_stock].nunique() > 1:
                gtins_ambiguos.add(gtin_n)

    resultado = ResultadoMatching()
    r = resultado.resumen
    r.total_lineas = len(df_activos)

    for _, pedido in df_activos.iterrows():
        gtin_norm = str(pedido.get("_gtin_norm", "") or "").strip()
        sku_norm  = str(pedido.get("_sku_norm",  "") or "").strip()
        cantidad  = int(pedido.get("_unidades_int", 1))

        nro_ped  = _str_o_vacio(pedido, col_nro_ped)
        producto = _str_o_vacio(pedido, col_producto)
        gtin_raw = _str_o_vacio(pedido, col_gtin_ped)
        sku_raw  = _str_o_vacio(pedido, col_sku_ped)

        # ── Intentar match GTIN ──────────────────────────────
        df_match, tipo_match, observacion = _intentar_match_gtin(
            gtin_norm, sku_norm, df_stock, idx_por_id, idx_por_sku
        )

        # ── Métricas del resultado ───────────────────────────
        gtin_dup = False
        sku_dup  = False
        ambiguo  = False
        nodos: list[str] = []
        stock_total = 0

        if not df_match.empty:
            stock_serie = pd.to_numeric(df_stock.loc[df_match.index, col_stk], errors="coerce").fillna(0)
            stock_total = int(stock_serie.sum())
            nodos = df_stock.loc[df_match.index, col_nodo].dropna().unique().tolist()

            # Duplicado: mismo nodo aparece en >1 fila para este producto
            conteo_por_nodo = df_stock.loc[df_match.index].groupby(col_nodo).size()
            if (conteo_por_nodo > 1).any():
                if tipo_match == "gtin":
                    gtin_dup = True
                else:
                    sku_dup = True

            # Ambiguo: GTIN matchea productos distintos en stock
            if tipo_match == "gtin" and gtin_norm in gtins_ambiguos:
                ambiguo = True
                observacion = "GTIN con múltiples productos en stock — verificar"

        # ── Actualizar resumen ───────────────────────────────
        if tipo_match == "gtin":
            r.con_match_gtin += 1
        elif tipo_match == "sku":
            r.con_match_sku += 1
        else:
            r.sin_match += 1

        if ambiguo:    r.ambiguos       += 1
        if gtin_dup:   r.gtin_duplicados += 1
        if sku_dup:    r.sku_duplicados  += 1

        resultado.lineas.append(LineaMatching(
            nro_pedido       = nro_ped,
            producto         = producto,
            gtin             = gtin_raw,
            sku              = sku_raw,
            cantidad_pedida  = cantidad,
            match_encontrado = not df_match.empty,
            tipo_match       = tipo_match,
            registros_stock  = len(df_match),
            nodos_disponibles= nodos,
            stock_total      = stock_total,
            observacion      = observacion,
            gtin_duplicado   = gtin_dup,
            sku_duplicado    = sku_dup,
            ambiguo          = ambiguo,
            df_stock         = df_match if not df_match.empty else None,
        ))

    logger.info(
        f"Matching: {r.con_match_gtin} GTIN | {r.con_match_sku} SKU | "
        f"{r.sin_match} sin match | {r.ambiguos} ambiguos | "
        f"cobertura {r.pct_cobertura()}%"
    )
    return resultado


# ════════════════════════════════════════════════════════════
#  HELPERS INTERNOS
# ════════════════════════════════════════════════════════════

def _construir_indice(df: pd.DataFrame, col: str) -> dict[str, list[int]]:
    """Construye {valor_norm → [índices de fila]} para búsqueda O(1)."""
    indice: dict[str, list[int]] = {}
    if col not in df.columns:
        return indice
    for idx, val in df[col].items():
        if val:  # omitir vacíos
            indice.setdefault(str(val), []).append(idx)
    return indice


def _intentar_match_gtin(
    gtin_norm: str,
    sku_norm:  str,
    df_stock:  pd.DataFrame,
    idx_por_id:  dict[str, list[int]],
    idx_por_sku: dict[str, list[int]],
) -> tuple[pd.DataFrame, str, str]:
    """
    Intenta match en orden de prioridad:
      1. GTIN  vs stock._id_norm  (columna principal del stock)
      2. GTIN  vs stock._sku_norm (columna secundaria del stock)
      3. SKU   vs stock._id_norm  (fallback: el SKU del pedido matchea el ID del stock)
      4. SKU   vs stock._sku_norm (fallback secundario)

    Retorna (df_match, tipo_match, observacion).
    """
    # Soporta GTINs múltiples separados por coma (algunos archivos los incluyen)
    gtins = [g.strip() for g in gtin_norm.split(",") if g.strip()] if gtin_norm else []

    if gtins:
        filas = _buscar_en_indices(gtins, idx_por_id, idx_por_sku)
        if filas:
            return df_stock.loc[sorted(set(filas))], "gtin", ""

    # Fallback por SKU
    if sku_norm:
        filas = _buscar_en_indices([sku_norm], idx_por_id, idx_por_sku)
        if filas:
            return df_stock.loc[sorted(set(filas))], "sku", "Match por SKU (GTIN no encontrado)"

    return pd.DataFrame(columns=df_stock.columns), "sin_match", "Sin match en archivo de stock"


def _buscar_en_indices(
    claves: list[str],
    idx_por_id:  dict[str, list[int]],
    idx_por_sku: dict[str, list[int]],
) -> list[int]:
    """Busca un conjunto de claves en ambos índices. Devuelve lista de índices."""
    filas: list[int] = []
    for clave in claves:
        filas.extend(idx_por_id.get(clave, []))
        filas.extend(idx_por_sku.get(clave, []))
    return filas


def _str_o_vacio(row: pd.Series, col: str | None) -> str:
    """Extrae un valor de la fila como string, o "" si la columna es None/NaN."""
    if not col or col not in row.index:
        return ""
    val = row[col]
    if pd.isna(val):
        return ""
    return str(val).strip()
