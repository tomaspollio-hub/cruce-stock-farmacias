"""
loader.py
Carga archivos Excel o CSV con detección automática de encoding.
Devuelve siempre un DataFrame de pandas con columnas sin espacios extras.
"""

import pathlib
import chardet
import pandas as pd


def _detectar_encoding(path: str) -> str:
    """Lee los primeros 50 KB para detectar encoding."""
    with open(path, "rb") as f:
        raw = f.read(50_000)
    resultado = chardet.detect(raw)
    encoding = resultado.get("encoding") or "utf-8"
    return encoding


def cargar_archivo(path: str) -> pd.DataFrame:
    """
    Carga un archivo Excel (.xlsx, .xls) o CSV (.csv, .txt).
    Limpia nombres de columna: strip + lower.
    Lanza ValueError si el formato no es reconocido.
    """
    p = pathlib.Path(path)
    ext = p.suffix.lower()

    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    elif ext in (".csv", ".txt"):
        encoding = _detectar_encoding(path)
        # Intentar con separador coma, luego punto y coma
        try:
            df = pd.read_csv(path, dtype=str, encoding=encoding, sep=",")
            if df.shape[1] == 1:
                # Probablemente separado por punto y coma
                df = pd.read_csv(path, dtype=str, encoding=encoding, sep=";")
        except Exception:
            df = pd.read_csv(path, dtype=str, encoding=encoding, sep=";")
    else:
        raise ValueError(
            f"Formato no soportado: '{ext}'. Usá .xlsx, .xls o .csv"
        )

    # Limpiar nombres de columnas
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Eliminar filas completamente vacías
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
