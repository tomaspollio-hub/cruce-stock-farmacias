"""
optimizer.py
Algoritmo greedy de cobertura mínima de sucursales.

Lógica:
  Para cada producto con N unidades requeridas:
  1. Obtener todas las sucursales que tienen stock del producto.
  2. Separar entre sucursales "locales" (Neuquén Capital) y "remotas" (requieren llamado).
  3. Dentro de cada grupo, ordenar por stock descendente.
  4. Asignar sucursales de forma greedy (primero locales):
     - Tomar la sucursal con más stock.
     - Restar las unidades cubiertas.
     - Continuar hasta cubrir el pedido o agotar opciones.
  5. Si no se cubre el total → marcar la diferencia como "sin cobertura".

Resultado: lista de filas listas para el Excel del cadete.
"""

from __future__ import annotations
import pandas as pd
from src.logger import get_logger
from src.normalizer import normalizar_texto

logger = get_logger(__name__)


def _clasificar_zona(nodo: str, zonas_local: list[str], zonas_llamar: list[str]) -> str:
    """
    Devuelve 'local' o 'llamar' según el nombre del nodo.
    Si no coincide con ninguna lista configurada, asume 'local'.
    """
    nodo_n = normalizar_texto(nodo)
    for z in zonas_llamar:
        if normalizar_texto(z) in nodo_n:
            return "llamar"
    return "local"


def optimizar_producto(
    gtin_key: str,
    unidades_requeridas: int,
    df_stock_producto: pd.DataFrame,   # filas del stock filtradas por este GTIN
    col_nodo: str,
    col_stock: str,
    zonas_local: list[str],
    zonas_llamar: list[str],
    max_sucursales: int = 3,
) -> list[dict]:
    """
    Dado el stock disponible por nodo para UN producto, devuelve
    la lista mínima de sucursales necesarias para cubrir la demanda.

    Cada elemento del resultado es un dict con:
      - nodo, stock_disponible, unidades_asignadas, zona, estado_sugerido
    """
    if df_stock_producto.empty or unidades_requeridas <= 0:
        return []

    # Construir tabla nodo → stock (sumar si hay duplicados)
    tabla = (
        df_stock_producto
        .copy()
        .assign(
            _nodo=df_stock_producto[col_nodo].apply(normalizar_texto),
            _stock=pd.to_numeric(df_stock_producto[col_stock], errors="coerce").fillna(0).astype(int),
        )
        .groupby(col_nodo, as_index=False)
        .agg(
            _nodo_raw=(col_nodo, "first"),
            stock_total=("_stock", "sum"),
        )
    )

    # Clasificar zona y ordenar: local primero, mayor stock primero
    tabla["zona"] = tabla["_nodo_raw"].apply(
        lambda n: _clasificar_zona(n, zonas_local, zonas_llamar)
    )
    tabla["zona_orden"] = tabla["zona"].map({"local": 0, "llamar": 1})
    tabla = tabla.sort_values(["zona_orden", "stock_total"], ascending=[True, False])
    tabla = tabla[tabla["stock_total"] > 0]

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
        zona        = fila["zona"]

        unidades_tomar = min(stock_disp, restante)
        restante -= unidades_tomar

        estado_sugerido = "Llamar a suc" if zona == "llamar" else "Búsqueda"

        asignaciones.append({
            "farmacia":            nodo_nombre,
            "stock_sucursal":      stock_disp,
            "unidades_asignadas":  unidades_tomar,
            "zona":                zona,
            "estado_busqueda":     estado_sugerido,
        })

    if restante > 0:
        logger.warning(
            f"GTIN '{gtin_key}': quedan {restante} unidades sin cobertura "
            f"(pedido={unidades_requeridas}, cubierto={unidades_requeridas - restante})"
        )
        # Agregar fila de aviso para el cadete
        asignaciones.append({
            "farmacia":            "— SIN COBERTURA —",
            "stock_sucursal":      0,
            "unidades_asignadas":  restante,
            "zona":                "—",
            "estado_busqueda":     "Llamar cliente",
        })

    return asignaciones


def construir_planilla(
    df_pedidos: pd.DataFrame,
    df_stock: pd.DataFrame,
    mapa_pedidos: dict,
    mapa_stock: dict,
    cfg: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa todos los pedidos activos y devuelve:
      - df_ruta   : planilla completa para el cadete (las 10 columnas)
      - df_sin_stock: productos que no se encontraron en ninguna sucursal
    """
    zonas_local  = [z.lower() for z in cfg["zonas"]["local"]]
    zonas_llamar = [z.lower() for z in cfg["zonas"]["llamar"]]
    max_suc      = cfg["optimizacion"]["max_sucursales_por_producto"]
    estado_activo = cfg["pedidos"]["estado_activo"].lower()

    # ── Filtrar pedidos activos ──────────────────────────────
    col_estado = mapa_pedidos["estado"]
    df_activos = df_pedidos[
        df_pedidos[col_estado].apply(lambda v: str(v).strip().lower()) == estado_activo
    ].copy()

    if df_activos.empty:
        logger.warning("No se encontraron pedidos con estado 'abierta'.")
        return pd.DataFrame(), pd.DataFrame()

    logger.info(f"Pedidos activos encontrados: {len(df_activos)} filas")

    # ── Preparar columnas clave de stock ────────────────────
    col_id_stock  = mapa_stock["id"]      # GTIN en stock
    col_sku_stock = mapa_stock["sku"]     # SKU/cod.barra en stock
    col_nodo      = mapa_stock["nodo"]
    col_stk       = mapa_stock["stock"]

    # Columnas clave de pedidos
    col_sku_ped   = mapa_pedidos["sku"]   # hace match con ID del stock
    col_gtin_ped  = mapa_pedidos["gtin"]  # hace match con SKU del stock
    col_unidades  = mapa_pedidos["unidades"]
    col_producto  = mapa_pedidos["producto"]

    filas_ruta: list[dict] = []
    filas_sin_stock: list[dict] = []

    for _, pedido in df_activos.iterrows():
        sku_pedido  = str(pedido[col_sku_ped]).strip()   if pd.notna(pedido[col_sku_ped])  else ""
        gtin_pedido = str(pedido[col_gtin_ped]).strip()  if pd.notna(pedido[col_gtin_ped]) else ""
        try:
            unidades = int(float(str(pedido[col_unidades]).strip()))
        except (ValueError, TypeError):
            unidades = 1
            logger.warning(f"Unidades no legibles para '{pedido[col_producto]}', asumiendo 1")

        nombre_producto = str(pedido[col_producto]) if pd.notna(pedido[col_producto]) else ""
        variante = str(pedido.get(mapa_pedidos.get("variante", ""), "")) if mapa_pedidos.get("variante") else ""

        # ── Buscar en stock por dos llaves ─────────────────
        # El campo GTIN del pedido puede tener múltiples códigos separados por coma
        # Ej: "7889587761925,7509552903416,7509552902747"
        gtins_pedido = [g.strip().lower() for g in gtin_pedido.split(",") if g.strip()]

        # Llave 1: SKU del pedido == ID del stock
        mask_llave1 = df_stock[col_id_stock].apply(
            lambda v: str(v).strip().lower()
        ) == sku_pedido.lower()

        # Llave 2: cualquiera de los GTINs del pedido == SKU del stock
        mask_llave2 = df_stock[col_sku_stock].apply(
            lambda v: str(v).strip().lower() in gtins_pedido
        ) if gtins_pedido else pd.Series(False, index=df_stock.index)

        # Llave 3: ID del stock coincide con alguno de los GTINs del pedido
        mask_llave3 = df_stock[col_id_stock].apply(
            lambda v: str(v).strip().lower() in gtins_pedido
        ) if gtins_pedido else pd.Series(False, index=df_stock.index)

        df_encontrado = df_stock[mask_llave1 | mask_llave2 | mask_llave3]

        gtin_key = sku_pedido or gtin_pedido  # para logs

        if df_encontrado.empty:
            logger.warning(f"Sin match en stock: '{nombre_producto}' (SKU={sku_pedido}, GTIN={gtin_pedido})")
            filas_sin_stock.append({
                "producto":  nombre_producto,
                "variante":  variante,
                "sku":       sku_pedido,
                "gtin":      gtin_pedido,
                "unidades":  unidades,
                "motivo":    "Sin match en archivo de stock",
            })
            continue

        # ── Optimizar sucursales ────────────────────────────
        asignaciones = optimizar_producto(
            gtin_key=gtin_key,
            unidades_requeridas=unidades,
            df_stock_producto=df_encontrado,
            col_nodo=col_nodo,
            col_stock=col_stk,
            zonas_local=zonas_local,
            zonas_llamar=zonas_llamar,
            max_sucursales=max_suc,
        )

        if not asignaciones:
            filas_sin_stock.append({
                "producto":  nombre_producto,
                "variante":  variante,
                "sku":       sku_pedido,
                "gtin":      gtin_pedido,
                "unidades":  unidades,
                "motivo":    "Stock 0 en todas las sucursales",
            })
            continue

        # Obtener datos adicionales del stock para el nombre Zetti
        nombre_zetti = ""
        col_nombre_stock = mapa_stock.get("nombre")
        if col_nombre_stock and col_nombre_stock in df_encontrado.columns:
            nombre_zetti = str(df_encontrado.iloc[0][col_nombre_stock])

        for asig in asignaciones:
            filas_ruta.append({
                # Columnas del output (las 10 que describiste)
                "Producto":            nombre_producto,
                "Tipo / Variante":     variante,
                "Zetti (ID)":          sku_pedido,
                "GTIN":                gtin_pedido,
                "Nombre Zetti":        nombre_zetti,
                "Cantidad pedida":     unidades,
                "Farmacia":            asig["farmacia"],
                "Stock sucursal":      asig["stock_sucursal"],
                "Unidades a buscar":   asig["unidades_asignadas"],
                "Zona":                asig["zona"],
                "Estado de búsqueda":  asig["estado_busqueda"],
            })

    df_ruta      = pd.DataFrame(filas_ruta)
    df_sin_stock = pd.DataFrame(filas_sin_stock)

    logger.info(f"Filas generadas en planilla: {len(df_ruta)}")
    logger.info(f"Productos sin cobertura total: {len(df_sin_stock)}")

    return df_ruta, df_sin_stock
