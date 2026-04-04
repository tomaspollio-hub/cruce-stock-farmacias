"""
normalizer.py
Normalización de GTINs, códigos de barra y textos.
"""

import re
import unicodedata
import pandas as pd
from src.logger import get_logger

logger = get_logger(__name__)

LONGITUDES_VALIDAS = {8, 12, 13, 14}
LONGITUD_ESTANDAR = 14


def _quitar_tildes(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_texto(valor) -> str:
    """Strip, lower, quitar tildes. Devuelve '' si es nulo."""
    if pd.isna(valor):
        return ""
    return _quitar_tildes(str(valor).strip().lower())


def normalizar_gtin(valor, contexto: str = "") -> str:
    """
    Convierte un valor a GTIN normalizado de 14 dígitos.
    - Quita espacios, guiones, puntos
    - Elimina parte decimal si viene como float de Excel (ej: '7790001234567.0')
    - Rellena con ceros a la izquierda hasta 14 dígitos
    - Loguea si la longitud no es válida

    Devuelve '' si no se puede normalizar.
    """
    if pd.isna(valor):
        return ""

    # Convertir a string y limpiar
    s = str(valor).strip()

    # Excel a veces convierte GTINs a float: '7790001234567.0'
    s = re.sub(r"\.0+$", "", s)

    # Quitar caracteres no numéricos
    s = re.sub(r"[^0-9]", "", s)

    if not s:
        logger.warning(f"GTIN vacío o no numérico{' en ' + contexto if contexto else ''}: '{valor}'")
        return ""

    # Rellenar hasta 14 dígitos
    s_padded = s.zfill(LONGITUD_ESTANDAR)

    # Validar longitud original (antes del padding)
    if len(s) not in LONGITUDES_VALIDAS:
        logger.warning(
            f"GTIN con longitud inusual ({len(s)} dígitos)"
            f"{' en ' + contexto if contexto else ''}: '{valor}' → '{s_padded}'"
        )

    return s_padded


def normalizar_columna_gtin(serie: pd.Series, contexto: str = "") -> pd.Series:
    """Aplica normalizar_gtin a toda una columna."""
    return serie.apply(lambda v: normalizar_gtin(v, contexto))


def normalizar_columna_texto(serie: pd.Series) -> pd.Series:
    """Aplica normalizar_texto a toda una columna."""
    return serie.apply(normalizar_texto)
