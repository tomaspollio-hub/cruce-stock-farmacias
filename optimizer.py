"""
optimizer.py
Algoritmo greedy de cobertura mínima de sucursales.

Prioridades de zona (0 = mayor prioridad):
  0 — Depósito ecommerce (APT-ECOMMERCE-NQN)
  1 — Neuquén Capital
  2 — Centenario / Plottier
  3 — Zonas cercanas (Añelo, El Chañar)
  4 — Remotas (Cutral Co, Zapala, Puerto Madryn) → estado "Llamar a suc"
"""

from __future__ import annotations
import pandas as pd
from src.logger import get_logger
from src.normalizer import normalizar_texto

logger = get_logger(__name__)

PRIORIDAD_DEFAULT = 1          # si el nodo no matchea ninguna lista → NQN Capital
PRIORIDAD_REMOTA  = 4          # prioridades >= este valor → "Llamar a suc"


def _prioridad_zona(nodo: str, zonas_cfg: dict) -> int:
    """
    Devuelve la prioridad numérica (0-4) del nodo.
    Recorre las listas en orden y retorna la primera que tenga match.
    El matching es por substring: si el nodo CONTIENE el fragmento → match.
    Sin match → PRIORIDAD_DEFAULT.
    """
    nodo_n = normalizar_texto(nodo)

    keys_ordenadas = [
        "prioridad_0_deposito",
        "prioridad_1_nqn_capital",
        "prioridad_2_centenario_plottier",
        "prioridad_3_cercanas",
        "prioridad_4_remotas",
    ]

    for prioridad, key in enumerate(keys_ordenadas):
        fragmentos = zonas_cfg.get(key, [])
        for frag in fragmentos:
            if normalizar_texto(frag) in nodo_n:
                return prioridad

    logger.warning(
        f"Nodo '{nodo}' no coincide con ninguna zona configurada. "
        f"Se asigna prioridad {PRIORIDAD_DEFAULT} (NQN Capital) por defecto."
    )
    return PRIORIDAD_DEFAULT


def _zona_label(prioridad: int, labels_cfg: dict) -> str:
    """Devuelve la etiqueta legible de la zona según su prioridad."""
    return labels_cfg.get(prioridad, labels_cfg.get(str(prioridad), f"Zona {prioridad}"))


def optimizar_producto(
    gtin_key: str,
    unidades_requeridas: int,
    df_stock_producto: pd.DataFrame,
    col_nodo: str,
    col_stock: str,
    zonas_cfg: dict,
    zona_labels: dict,
    max_sucursales: int = 3,
) -> list[dict]:
    """
    Dado el stock disponible por nodo para UN producto, devuelve
    la lista mínima de sucursales necesarias para cubrir la demanda.

    Orden: prioridad ASC (0 primero), luego stock_total DESC.
    """
    if df_stock_producto.empty or unidades_requeridas <= 0:
        return []

    # Agregar stock por nodo si hay duplicados
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

    # Clasificar y ordenar
    tabla["prioridad"] = tabla["_nodo_raw"].apply(
        lambda n: _prioridad_zona(n, zonas_cfg)
    )
    tabla["zona_label"] = tabla["prioridad"].apply(
        lambda p: _zona_label(p, zona_labels)
    )
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

        nodo_nombre  = fila["_nodo_raw"]
        stock_disp   = int(fila["stock_total"])
        prioridad    = int(fila["prioridad"])
        zona_lbl     = fila["zona_label"]

        unidades_tomar = min(stock_disp, restante)
        restante -= unidades_tomar

        estado_sugerido = "Llamar a suc" if prioridad >= PRIORIDAD_REMOTA else "Búsqueda"

        asignaciones.append({
            "farmacia":           nodo_nombre,
            "stock_sucursal":     stock_disp,
            "unidades_asignadas": unidades_tomar,
            "prioridad":          prioridad,
            "zona":               zona_lbl,
            "estado_busqueda":    estado_sugerido,
        })

    if restante > 0:
        logger.warning(
            f"GTIN '{gtin_key}': quedan {restante} unidades sin cobertura "
            f"(pedido={unidades_requeridas}, cubierto={unidades_requeridas - restante})"
        )
        asignaciones.append({
            "farmacia":           "— SIN COBERTURA —",
            "stock_sucursal":     0,
            "unidades_asignadas": restante,
            "prioridad":          99,
            "zona":               "—",
            "estado_busqueda":    "Llamar cliente",
        })

    return asignaciones


def obtener_opciones_sucursal(
    df_stock_producto: pd.DataFrame,
    col_nodo: str,
    col_stock: str,
    zonas_cfg: dict,
    zona_labels: dict,
    max_opciones: int = 5,
) -> list[dict]:
    """
    Devuelve las top N sucursales disponibles para un producto,
    ordenadas por prioridad ASC y stock DESC.
    Usado para el selector manual de sucursal en la UI.

    Cada elemento: {"nodo": str, "stock": int, "prioridad": int, "zona": str, "label": str}
    """
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

    tabla["prioridad"] = tabla["_nodo_raw"].apply(
        lambda n: _prioridad_zona(n, zonas_cfg)
    )
    tabla["zona_label"] = tabla["prioridad"].apply(
        lambda p: _zona_label(p, zona_labels)
    )
    tabla = (
        tabla[tabla["stock_total"] > 0]
        .sort_values(["prioridad", "stock_total"], ascending=[True, False])
        .head(max_opciones)
        .reset_index(drop=True)
    )

    opciones = []
    for _, fila in tabla.iterrows():
        opciones.append({
            "nodo":      fila["_nodo_raw"],
            "stock":     int(fila["stock_total"]),
            "prioridad": int(fila["prioridad"]),
            "zona":      fila["zona_label"],
            "label":     f"{fila['_nodo_raw']} — {int(fila['stock_total'])} uds ({fila['zona_label']})",
        })

    return opciones


def construir_planilla(
    df_pedidos: pd.DataFrame,
    df_stock: pd.DataFrame,
    mapa_pedidos: dict,
    mapa_stock: dict,
    cfg: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Procesa todos los pedidos activos y devuelve:
      - df_ruta          : planilla completa para el cadete
      - df_sin_stock     : productos sin cobertura
      - stock_por_producto: dict {gtin_key → df de stock del producto}
                            para uso en el override manual de sucursal
    """
    zonas_cfg    = cfg["zonas"]
    zona_labels  = {int(k): v for k, v in cfg.get("zona_labels", {}).items()}
    max_suc      = cfg["optimizacion"]["max_sucursales_por_producto"]
    estado_activo = cfg["pedidos"]["estado_activo"].lower()

    col_estado   = mapa_pedidos["estado"]
    col_sku_ped  = mapa_pedidos["sku"]
    col_gtin_ped = mapa_pedidos["gtin"]
    col_unidades = mapa_pedidos["unidades"]
    col_producto = mapa_pedidos["producto"]

    col_id_stock  = mapa_stock["id"]
    col_sku_stock = mapa_stock["sku"]
    col_nodo      = mapa_stock["nodo"]
    col_stk       = mapa_stock["stock"]

    # Filtrar pedidos activos
    df_activos = df_pedidos[
        df_pedidos[col_estado].apply(lambda v: str(v).strip().lower()) == estado_activo
    ].copy()

    if df_activos.empty:
        logger.warning("No se encontraron pedidos con estado 'abierta'.")
        return pd.DataFrame(), pd.DataFrame(), {}

    logger.info(f"Pedidos activos encontrados: {len(df_activos)} filas")

    filas_ruta: list[dict] = []
    filas_sin_stock: list[dict] = []
    stock_por_producto: dict = {}   # gtin_key → df

    for _, pedido in df_activos.iterrows():
        sku_pedido  = str(pedido[col_sku_ped]).strip()  if pd.notna(pedido[col_sku_ped])  else ""
        gtin_pedido = str(pedido[col_gtin_ped]).strip() if pd.notna(pedido[col_gtin_ped]) else ""

        try:
            unidades = int(float(str(pedido[col_unidades]).strip()))
        except (ValueError, TypeError):
            unidades = 1
            logger.warning(f"Unidades no legibles para '{pedido[col_producto]}', asumiendo 1")

        nombre_producto = str(pedido[col_producto]) if pd.notna(pedido[col_producto]) else ""
        variante = ""
        if mapa_pedidos.get("variante") and mapa_pedidos["variante"] in pedido.index:
            variante = str(pedido[mapa_pedidos["variante"]]) if pd.notna(pedido[mapa_pedidos["variante"]]) else ""

        # Múltiples GTINs separados por coma
        gtins_pedido = [g.strip().lower() for g in gtin_pedido.split(",") if g.strip()]

        # Buscar en stock (3 llaves)
        mask1 = df_stock[col_id_stock].apply(lambda v: str(v).strip().lower()) == sku_pedido.lower()
        mask2 = df_stock[col_sku_stock].apply(lambda v: str(v).strip().lower() in gtins_pedido) \
                if gtins_pedido else pd.Series(False, index=df_stock.index)
        mask3 = df_stock[col_id_stock].apply(lambda v: str(v).strip().lower() in gtins_pedido) \
                if gtins_pedido else pd.Series(False, index=df_stock.index)

        df_encontrado = df_stock[mask1 | mask2 | mask3]
        gtin_key = sku_pedido or gtin_pedido

        if df_encontrado.empty:
            logger.warning(f"Sin match en stock: '{nombre_producto}' (SKU={sku_pedido}, GTIN={gtin_pedido})")
            filas_sin_stock.append({
                "Producto": nombre_producto,
                "Variante": variante,
                "SKU":      sku_pedido,
                "GTIN":     gtin_pedido,
                "Unidades": unidades,
                "Motivo":   "Sin match en archivo de stock",
            })
            continue

        # Guardar para override manual
        stock_por_producto[gtin_key] = df_encontrado.copy()

        # Optimizar sucursales
        asignaciones = optimizar_producto(
            gtin_key=gtin_key,
            unidades_requeridas=unidades,
            df_stock_producto=df_encontrado,
            col_nodo=col_nodo,
            col_stock=col_stk,
            zonas_cfg=zonas_cfg,
            zona_labels=zona_labels,
            max_sucursales=max_suc,
        )

        if not asignaciones:
            filas_sin_stock.append({
                "Producto": nombre_producto,
                "Variante": variante,
                "SKU":      sku_pedido,
                "GTIN":     gtin_pedido,
                "Unidades": unidades,
                "Motivo":   "Stock 0 en todas las sucursales",
            })
            continue

        nombre_zetti = ""
        col_nombre_stock = mapa_stock.get("nombre")
        if col_nombre_stock and col_nombre_stock in df_encontrado.columns:
            nombre_zetti = str(df_encontrado.iloc[0][col_nombre_stock])

        for asig in asignaciones:
            filas_ruta.append({
                "Producto":          nombre_producto,
                "Tipo / Variante":   variante,
                "Zetti (ID)":        sku_pedido,
                "GTIN":              gtin_pedido,
                "Nombre Zetti":      nombre_zetti,
                "Cantidad pedida":   unidades,
                "Farmacia":          asig["farmacia"],
                "Stock sucursal":    asig["stock_sucursal"],
                "Unidades a buscar": asig["unidades_asignadas"],
                "Zona":              asig["zona"],
                "Estado de búsqueda": asig["estado_busqueda"],
                # clave interna para override (no va al Excel)
                "_gtin_key":         gtin_key,
            })

    df_ruta      = pd.DataFrame(filas_ruta)
    df_sin_stock = pd.DataFrame(filas_sin_stock)

    logger.info(f"Filas generadas en planilla: {len(df_ruta)}")
    logger.info(f"Productos sin cobertura total: {len(df_sin_stock)}")

    return df_ruta, df_sin_stock, stock_por_producto
