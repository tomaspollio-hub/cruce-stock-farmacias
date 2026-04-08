"""
asignacion.py
Asignación inteligente de sucursal por producto, con:

  - Tier de nodo (0→preferida, 1→segunda, 2→resto, 3→último recurso)
  - Bonus de consolidación: preferir sucursal que ya cubre otro
    producto del mismo pedido (minimiza paradas del cadete)
  - Trazabilidad: campo criterio_asignacion en cada resultado

Sort key: [consolida_pedido DESC, tier ASC, stock DESC]

No importa de src.optimizer — duplica las funciones de zona que
necesita para evitar dependencia circular.
Pendiente: mover _prioridad_zona/_zona_label a src/services/zonas.py
en una futura limpieza.
"""
from __future__ import annotations
import unicodedata
import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)

PRIORIDAD_REMOTA = 4  # zonas con este valor o mayor → "Llamar a suc"


# ════════════════════════════════════════════════════════════
#  ESTRUCTURAS DE RESULTADO
# ════════════════════════════════════════════════════════════

@dataclass
class ResumenPedido:
    """Métricas de cobertura para un pedido completo."""
    nro_pedido:              str
    total_productos:         int   = 0
    filas_con_cobertura:     int   = 0
    filas_sin_cobertura:     int   = 0
    sucursales_involucradas: list[str] = field(default_factory=list)
    total_sucursales:        int   = 0
    filas_consolidadas:      int   = 0   # asignaciones que consolidan con otra del pedido
    tiers_usados:            dict  = field(default_factory=dict)  # {tier → count}


# ════════════════════════════════════════════════════════════
#  LÓGICA DE TIER
# ════════════════════════════════════════════════════════════

def calcular_tier_nodo(nombre_nodo: str, cfg: dict) -> int:
    """
    Devuelve el tier de prioridad de un nodo según config.yaml:

      0 → sucursales preferidas (nodos_tier_0, nombre exacto)
      1 → segunda opción       (nodos_tier_1 + palabras_clave_tier_1)
      2 → resto (default)
      3 → último recurso       (palabras_clave_tier_3)

    Matching es case-insensitive, sin tildes.
    """
    asig = cfg.get("asignacion", {})
    nodo_n = _norm(nombre_nodo)

    # Tier 0 — nombre exacto
    for entrada in asig.get("nodos_tier_0", []):
        if _norm(entrada) == nodo_n:
            return 0

    # Tier 1 — nombre exacto o palabra clave
    for entrada in asig.get("nodos_tier_1", []):
        if _norm(entrada) == nodo_n:
            return 1
    for kw in asig.get("palabras_clave_tier_1", []):
        if _norm(kw) in nodo_n:
            return 1

    # Tier 3 — palabra clave (se evalúa antes de dar default tier 2)
    for kw in asig.get("palabras_clave_tier_3", []):
        if _norm(kw) in nodo_n:
            return 3

    return 2  # default


# ════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL DE ASIGNACIÓN
# ════════════════════════════════════════════════════════════

def asignar_producto_inteligente(
    gtin_key: str,
    unidades_requeridas: int,
    df_stock_producto: pd.DataFrame,
    col_nodo: str,
    col_stock: str,
    zonas_cfg: dict,
    zona_labels: dict,
    cfg: dict,
    max_sucursales: int = 3,
    umbral_stock_sospechoso: int = 200,
    nodos_ya_asignados: set[str] | None = None,
) -> list[dict]:
    """
    Reemplaza optimizar_producto() con la lógica de tiers + consolidación.

    Args:
        nodos_ya_asignados: Sucursales que ya tienen al menos un producto
                            del mismo pedido asignado. Usadas para el
                            bonus de consolidación.

    Returns:
        Lista de dicts con las mismas claves que optimizar_producto()
        MÁS: criterio_asignacion, tier, consolida_pedido.
    """
    if df_stock_producto.empty or unidades_requeridas <= 0:
        return []

    if nodos_ya_asignados is None:
        nodos_ya_asignados = set()

    # ── Tabla de candidatos ──────────────────────────────────
    tabla = (
        df_stock_producto
        .copy()
        .assign(
            _stock=pd.to_numeric(
                df_stock_producto[col_stock], errors="coerce"
            ).fillna(0).astype(int)
        )
        .groupby(col_nodo, as_index=False)
        .agg(
            _nodo_raw=(col_nodo, "first"),
            stock_total=("_stock", "sum"),
        )
    )

    # Info de zona (para display, no para sort)
    tabla["zona_prioridad"] = tabla["_nodo_raw"].apply(
        lambda n: _prioridad_zona(n, zonas_cfg)
    )
    tabla["zona_label"] = tabla["zona_prioridad"].apply(
        lambda p: _zona_label(p, zona_labels)
    )

    # Tier (para sort de prioridad)
    tabla["tier"] = tabla["_nodo_raw"].apply(
        lambda n: calcular_tier_nodo(n, cfg)
    )

    # Consolidación: True si este nodo ya cubre otro producto del pedido
    nodos_norm = {_norm(n) for n in nodos_ya_asignados}
    tabla["consolida"] = tabla["_nodo_raw"].apply(
        lambda n: _norm(n) in nodos_norm
    )

    # Solo nodos con stock > 0
    tabla = tabla[tabla["stock_total"] > 0].copy()

    if tabla.empty:
        logger.warning(f"Sin stock disponible en ningún nodo para '{gtin_key}'")
        return []

    # ── Sort: consolida DESC · tier ASC · stock DESC ─────────
    tabla = tabla.sort_values(
        ["consolida", "tier", "stock_total"],
        ascending=[False, True, False],
    ).reset_index(drop=True)

    # ── Asignación greedy ────────────────────────────────────
    restante   = unidades_requeridas
    resultado: list[dict] = []

    for _, fila in tabla.iterrows():
        if restante <= 0 or len(resultado) >= max_sucursales:
            break

        nodo      = fila["_nodo_raw"]
        stock     = int(fila["stock_total"])
        tier      = int(fila["tier"])
        zona_lbl  = fila["zona_label"]
        zona_prio = int(fila["zona_prioridad"])
        consolida = bool(fila["consolida"])

        tomar     = min(stock, restante)
        restante -= tomar

        estado = "Llamar a suc" if zona_prio >= PRIORIDAD_REMOTA else "Búsqueda"
        sosp   = stock > umbral_stock_sospechoso

        resultado.append({
            # Campos compatibles con optimizar_producto()
            "farmacia":            nodo,
            "stock_sucursal":      stock,
            "unidades_asignadas":  tomar,
            "prioridad":           zona_prio,
            "zona":                zona_lbl,
            "estado_busqueda":     estado,
            "stock_sospechoso":    sosp,
            # Campos nuevos
            "criterio_asignacion": _criterio_texto(tier, consolida, stock),
            "tier":                tier,
            "consolida_pedido":    consolida,
        })

    # ── Sin cobertura completa ───────────────────────────────
    if restante > 0:
        logger.warning(
            f"'{gtin_key}': {restante} unidades sin cobertura "
            f"(pedido={unidades_requeridas}, cubierto={unidades_requeridas - restante})"
        )
        resultado.append({
            "farmacia":            "— SIN COBERTURA —",
            "stock_sucursal":      0,
            "unidades_asignadas":  restante,
            "prioridad":           99,
            "zona":                "—",
            "estado_busqueda":     "Llamar cliente",
            "stock_sospechoso":    False,
            "criterio_asignacion": "Sin stock suficiente",
            "tier":                99,
            "consolida_pedido":    False,
        })

    return resultado


# ════════════════════════════════════════════════════════════
#  RESÚMENES POR PEDIDO
# ════════════════════════════════════════════════════════════

def calcular_resumenes_pedidos(df_ruta: pd.DataFrame) -> list[ResumenPedido]:
    """
    Genera un ResumenPedido por cada número de pedido en df_ruta.
    Llama después de construir_planilla().
    """
    if df_ruta.empty or "N° Pedido" not in df_ruta.columns:
        return []

    resumenes = []
    for nro_ped in df_ruta["N° Pedido"].unique():
        resumenes.append(calcular_resumen_pedido(df_ruta, str(nro_ped)))
    return resumenes


def calcular_resumen_pedido(df_ruta: pd.DataFrame, nro_pedido: str) -> ResumenPedido:
    """Métricas de cobertura para un pedido específico."""
    df_ped = df_ruta[df_ruta["N° Pedido"].astype(str) == nro_pedido]

    sin_cob   = df_ped["Farmacia"] == "— SIN COBERTURA —"
    con_cob   = ~sin_cob
    sucursales = sorted(set(df_ped.loc[con_cob, "Farmacia"].unique()))

    tiers_usados: dict[int, int] = {}
    consolidas = 0
    if "_tier" in df_ped.columns:
        for t in df_ped.loc[con_cob, "_tier"].dropna():
            t_int = int(t)
            tiers_usados[t_int] = tiers_usados.get(t_int, 0) + 1
    if "_consolida_pedido" in df_ped.columns:
        consolidas = int(df_ped["_consolida_pedido"].sum())

    return ResumenPedido(
        nro_pedido              = nro_pedido,
        total_productos         = int(df_ped["Producto"].nunique()),
        filas_con_cobertura     = int(con_cob.sum()),
        filas_sin_cobertura     = int(sin_cob.sum()),
        sucursales_involucradas = sucursales,
        total_sucursales        = len(sucursales),
        filas_consolidadas      = consolidas,
        tiers_usados            = tiers_usados,
    )


# ════════════════════════════════════════════════════════════
#  HELPERS INTERNOS
# ════════════════════════════════════════════════════════════

def _norm(valor: str) -> str:
    """Lowercase + strip + sin tildes. Para comparación de nombres."""
    nfkd = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _criterio_texto(tier: int, consolida: bool, stock: int) -> str:
    """Texto legible que explica por qué se eligió esta sucursal."""
    partes: list[str] = []
    if consolida:
        partes.append("consolida pedido")
    if tier == 0:
        partes.append("sucursal prioritaria")
    elif tier == 1:
        partes.append("segunda prioridad")
    elif tier == 3:
        partes.append("último recurso")
    partes.append(f"stock {stock}")
    return " · ".join(partes)


def _prioridad_zona(nodo: str, zonas_cfg: dict) -> int:
    """
    Copia de optimizer._prioridad_zona para evitar import circular.
    Pendiente: mover ambas a src/services/zonas.py.
    """
    nodo_n = _norm(nodo)
    keys = [
        "prioridad_0_deposito",
        "prioridad_1_nqn_capital",
        "prioridad_2_centenario_plottier",
        "prioridad_3_cercanas",
        "prioridad_4_remotas",
    ]
    for prioridad, key in enumerate(keys):
        for frag in zonas_cfg.get(key, []):
            if _norm(frag) in nodo_n:
                return prioridad
    return 1  # default: NQN Capital


def _zona_label(prioridad: int, labels_cfg: dict) -> str:
    """Copia de optimizer._zona_label para evitar import circular."""
    return (
        labels_cfg.get(prioridad)
        or labels_cfg.get(str(prioridad))
        or labels_cfg.get(int(prioridad))
        or f"Zona {prioridad}"
    )
