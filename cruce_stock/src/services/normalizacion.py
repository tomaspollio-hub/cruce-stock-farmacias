"""
normalizacion.py
Capa de normalización de datos para el cruce de stock.

Opera sobre DataFrames con el mapa de columnas ya detectado por matcher.py.
Agrega columnas internas (_gtin_norm, _sku_norm, etc.) sin modificar
las columnas originales — la trazabilidad hacia el dato original se conserva.
"""
from __future__ import annotations
import unicodedata
import pandas as pd


# ════════════════════════════════════════════════════════════
#  NORMALIZACIÓN DE VALORES INDIVIDUALES
# ════════════════════════════════════════════════════════════

def normalizar_gtin(valor) -> str:
    """
    Normaliza un GTIN (o cualquier código numérico) a string limpio.

    Transformaciones:
      - NaN / None / vacío  → ""
      - "8412345.0"         → "8412345"   (artefacto Excel: int leído como float)
      - "  8412345 "        → "8412345"   (whitespace)
      - "nan" / "None"      → ""
    """
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass
    s = str(valor).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return ""
    # Eliminar ".0" al final — artefacto habitual de Excel al leer enteros como float
    if s.endswith(".0"):
        s = s[:-2]
    return s.strip()


def normalizar_sku(valor) -> str:
    """Alias de normalizar_gtin — aplica las mismas transformaciones."""
    return normalizar_gtin(valor)


def normalizar_texto(valor) -> str:
    """
    Strip + lowercase + sin tildes.
    Para comparación o soporte, NO como llave de matching principal.
    """
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass
    nfkd = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ════════════════════════════════════════════════════════════
#  VALIDACIÓN DE COLUMNAS
# ════════════════════════════════════════════════════════════

def validar_columnas_requeridas(
    mapa: dict,
    requeridas: list[str],
    nombre_archivo: str = "",
) -> list[str]:
    """
    Verifica que las columnas requeridas hayan sido detectadas en el mapa.

    Args:
        mapa:           Resultado de mapear_columnas_*() — {campo_interno → col_real | None}
        requeridas:     Lista de campos internos que deben estar presentes.
        nombre_archivo: Nombre del archivo para mensajes de error.

    Returns:
        Lista de mensajes de error. Vacía si todo OK.
    """
    errores = []
    for campo in requeridas:
        if not mapa.get(campo):
            sufijo = f" en «{nombre_archivo}»" if nombre_archivo else ""
            errores.append(
                f"No se encontró la columna requerida '{campo}'{sufijo}. "
                f"Revisá los aliases en config.yaml."
            )
    return errores


# ════════════════════════════════════════════════════════════
#  NORMALIZACIÓN DE DATAFRAMES
# ════════════════════════════════════════════════════════════

def normalizar_pedidos(df: pd.DataFrame, mapa: dict) -> pd.DataFrame:
    """
    Agrega columnas normalizadas al DataFrame de pedidos.

    Columnas agregadas (internas, prefijo '_'):
      _gtin_norm    : GTIN normalizado (str, sin .0, sin espacios)
      _sku_norm     : SKU normalizado  (str, sin .0, sin espacios)
      _unidades_int : cantidad pedida  (int, 1 si no parseable)

    No modifica columnas originales.
    """
    df = df.copy()

    col_gtin = mapa.get("gtin")
    col_sku  = mapa.get("sku")
    col_uds  = mapa.get("unidades")

    df["_gtin_norm"] = (
        df[col_gtin].apply(normalizar_gtin) if col_gtin else ""
    )
    df["_sku_norm"] = (
        df[col_sku].apply(normalizar_sku) if col_sku else ""
    )

    if col_uds:
        df["_unidades_int"] = df[col_uds].apply(_parsear_unidades)
    else:
        df["_unidades_int"] = 1

    return df


def normalizar_stock(df: pd.DataFrame, mapa: dict) -> pd.DataFrame:
    """
    Agrega columnas normalizadas al DataFrame de stock.

    Columnas agregadas (internas, prefijo '_'):
      _id_norm  : GTIN/ID normalizado  (str)
      _sku_norm : SKU normalizado       (str)
    """
    df = df.copy()

    col_id  = mapa.get("id")
    col_sku = mapa.get("sku")

    df["_id_norm"] = (
        df[col_id].apply(normalizar_gtin) if col_id else ""
    )
    df["_sku_norm"] = (
        df[col_sku].apply(normalizar_sku) if col_sku else ""
    )

    return df


# ════════════════════════════════════════════════════════════
#  HELPERS INTERNOS
# ════════════════════════════════════════════════════════════

def _parsear_unidades(valor) -> int:
    """Convierte cualquier representación de cantidad a int. Devuelve 1 si falla."""
    try:
        return int(float(str(valor).strip()))
    except (ValueError, TypeError):
        return 1
