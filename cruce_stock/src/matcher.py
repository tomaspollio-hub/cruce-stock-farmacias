"""
matcher.py
Detección automática de columnas usando fuzzy matching (RapidFuzz).
Dado un DataFrame y una lista de nombres candidatos, devuelve
la columna real del DataFrame que mejor coincide.
"""

from rapidfuzz import fuzz
import pandas as pd
from src.logger import get_logger

logger = get_logger(__name__)

SCORE_MINIMO = 70  # puntuación mínima para aceptar un match


def detectar_columna(df: pd.DataFrame, candidatos: list[str], obligatoria: bool = True) -> str | None:
    """
    Busca entre las columnas de df la que mejor coincide con alguno
    de los candidatos (ya normalizados a lowercase).

    Retorna el nombre exacto de la columna en el DataFrame.
    Si no encuentra nada con score >= SCORE_MINIMO:
      - Si obligatoria=True  → lanza ValueError
      - Si obligatoria=False → retorna None y loguea warning
    """
    columnas_df = list(df.columns)  # ya vienen en lower desde loader
    candidatos_lower = [str(c).strip().lower() for c in candidatos]

    mejor_col = None
    mejor_score = 0

    for col_df in columnas_df:
        for candidato in candidatos_lower:
            score = fuzz.token_sort_ratio(col_df, candidato)
            if score > mejor_score:
                mejor_score = score
                mejor_col = col_df

    if mejor_score >= SCORE_MINIMO:
        logger.debug(f"Columna detectada: '{mejor_col}' (score={mejor_score}) para candidatos {candidatos}")
        return mejor_col

    msg = (
        f"No se encontró columna para {candidatos}. "
        f"Columnas disponibles: {columnas_df}"
    )
    if obligatoria:
        logger.error(msg)
        raise ValueError(msg)
    else:
        logger.warning(msg)
        return None


def mapear_columnas_pedidos(df: pd.DataFrame, cfg: dict) -> dict:
    """
    Devuelve un dict con las columnas reales del DataFrame de pedidos
    mapeadas a nombres internos estandarizados.
    """
    c = cfg["pedidos"]
    return {
        "nro_pedido": detectar_columna(df, c["col_nro_pedido"], obligatoria=False),
        "estado":     detectar_columna(df, c["col_estado"]),
        "producto":   detectar_columna(df, c["col_producto"]),
        "variante":   detectar_columna(df, c["col_variante"],   obligatoria=False),
        "marca":      detectar_columna(df, c["col_marca"],      obligatoria=False),
        "sku":        detectar_columna(df, c["col_sku"]),
        "gtin":       detectar_columna(df, c["col_gtin"]),
        "unidades":   detectar_columna(df, c["col_unidades"]),
    }


def mapear_columnas_stock(df: pd.DataFrame, cfg: dict) -> dict:
    """
    Devuelve un dict con las columnas reales del DataFrame de stock
    mapeadas a nombres internos estandarizados.
    """
    c = cfg["stock"]
    return {
        "id":         detectar_columna(df, c["col_id"]),
        "nombre":     detectar_columna(df, c["col_nombre"],    obligatoria=False),
        "sku":        detectar_columna(df, c["col_sku"]),
        "marca":      detectar_columna(df, c["col_marca"],     obligatoria=False),
        "fabricante": detectar_columna(df, c["col_fabricante"],obligatoria=False),
        "nodo":       detectar_columna(df, c["col_nodo"]),
        "stock":      detectar_columna(df, c["col_stock"]),
    }
