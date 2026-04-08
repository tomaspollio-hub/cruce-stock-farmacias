"""
analytics.py
Extracción y agregación de métricas operativas del historial de cruces.

Diseñado para crecer: todas las funciones reciben la lista de items del
historial y retornan estructuras simples (dicts / lists of dicts).
"""
from __future__ import annotations
from collections import Counter

import pandas as pd


# ════════════════════════════════════════════════════════════
#  EXTRACCIÓN — llamar una vez por cruce al guardar historial
# ════════════════════════════════════════════════════════════

def extraer_snapshot(
    df_ruta: pd.DataFrame,
    df_sin_stock: pd.DataFrame,
    resultado_matching,
    pedidos_unicos: int,
) -> dict:
    """
    Produce un dict con métricas del cruce.
    Se almacena en item["analytics"] dentro del historial de sesión.
    """
    snap: dict = {
        "pedidos_unicos":       pedidos_unicos,
        "pct_cobertura":        0,
        "sin_match":            0,
        "con_match_gtin":       0,
        "con_match_sku":        0,
        "n_sucursales":         0,
        "sucursales_carga":     {},   # {nombre: n_lineas}
        "productos_sin_cob":    [],   # [nombre_producto, ...]
        "pedidos_multisucursal": 0,
    }

    # ── Métricas de matching ───────────────────────────────
    if resultado_matching is not None:
        try:
            rs = resultado_matching.resumen
            snap["pct_cobertura"]  = rs.pct_cobertura()
            snap["sin_match"]      = rs.sin_match
            snap["con_match_gtin"] = rs.con_match_gtin
            snap["con_match_sku"]  = rs.con_match_sku
        except Exception:
            pass

    # ── Sucursales y cobertura desde df_ruta ──────────────
    if not df_ruta.empty and "Farmacia" in df_ruta.columns:
        validas = df_ruta["Farmacia"][df_ruta["Farmacia"] != "— SIN COBERTURA —"]
        snap["n_sucursales"]    = int(validas.nunique())
        snap["sucursales_carga"] = {
            str(k): int(v)
            for k, v in validas.value_counts().items()
        }

        # Pedidos que requieren más de una sucursal
        col_nro = next(
            (c for c in ("N° Pedido", "nro_pedido", "Nro Pedido")
             if c in df_ruta.columns), None
        )
        if col_nro:
            df_v = df_ruta[df_ruta["Farmacia"] != "— SIN COBERTURA —"]
            suc_por_ped = df_v.groupby(col_nro)["Farmacia"].nunique()
            snap["pedidos_multisucursal"] = int((suc_por_ped > 1).sum())

    # ── Productos sin cobertura ────────────────────────────
    if not df_sin_stock.empty:
        col_prod = next(
            (c for c in ("Producto", "producto", "Nombre", "nombre",
                         "descripcion", "Descripcion")
             if c in df_sin_stock.columns), None
        )
        if col_prod:
            snap["productos_sin_cob"] = (
                df_sin_stock[col_prod].dropna().astype(str).tolist()
            )

    return snap


# ════════════════════════════════════════════════════════════
#  AGREGACIÓN — sobre todos los items del historial
# ════════════════════════════════════════════════════════════

def agregar_historial(items: list[dict]) -> dict:
    """KPIs globales calculados sobre todos los cruces con analytics."""
    snaps = [i.get("analytics") for i in items if i.get("analytics")]
    if not snaps:
        return {}

    pcts = [s["pct_cobertura"] for s in snaps if "pct_cobertura" in s]
    sin_cob_total = sum(
        len(s.get("productos_sin_cob", [])) for s in snaps
    )
    mejor_idx = pcts.index(max(pcts)) if pcts else None

    return {
        "total_cruces":       len(items),
        "pct_cobertura_avg":  round(sum(pcts) / len(pcts), 1) if pcts else 0,
        "pct_cobertura_min":  round(min(pcts), 1) if pcts else 0,
        "pct_cobertura_max":  round(max(pcts), 1) if pcts else 0,
        "sin_cob_acum":       sin_cob_total,
        "mejor_cruce_id":     items[mejor_idx]["id"] if mejor_idx is not None else "—",
        "mejor_cruce_pct":    round(max(pcts), 1) if pcts else 0,
    }


def top_productos_problematicos(
    items: list[dict], top_n: int = 10
) -> list[dict]:
    """Productos que más veces aparecieron sin cobertura en el historial."""
    counter: Counter = Counter()
    for item in items:
        prods = item.get("analytics", {}).get("productos_sin_cob", [])
        counter.update(str(p) for p in prods)
    return [
        {"producto": p, "veces": n, "pct_cruces": 0}
        for p, n in counter.most_common(top_n)
    ]


def top_sucursales_carga(
    items: list[dict], top_n: int = 10
) -> list[dict]:
    """Sucursales que más líneas atendieron en el historial acumulado."""
    counter: Counter = Counter()
    for item in items:
        carga = item.get("analytics", {}).get("sucursales_carga", {})
        counter.update(carga)
    return [
        {"sucursal": s, "lineas": int(n)}
        for s, n in counter.most_common(top_n)
    ]


def tendencia_cobertura(items: list[dict]) -> list[dict]:
    """
    Lista de {id, hora, pct_cobertura, sin_cob} en orden cronológico
    (el historial se guarda en orden inverso → reversa).
    """
    resultado = []
    for item in reversed(items):
        snap = item.get("analytics", {})
        resultado.append({
            "id":           item.get("id", "—"),
            "hora":         item.get("hora", "—"),
            "pct":          snap.get("pct_cobertura", 0),
            "sin_cob":      len(snap.get("productos_sin_cob", [])),
            "n_sucursales": snap.get("n_sucursales", 0),
        })
    return resultado
