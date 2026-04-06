"""
exportador.py
Servicio de exportación a Excel: desacopla la lógica de bytes del session_state.
"""
import os
import tempfile

import pandas as pd


def excel_a_bytes(
    df_ruta: pd.DataFrame,
    df_sin_stock: pd.DataFrame,
    estados_busqueda: list,
    estados_cadete: dict | None = None,
) -> bytes:
    """
    Genera el archivo Excel y devuelve sus bytes.

    Args:
        df_ruta:          DataFrame principal de la planilla.
        df_sin_stock:     DataFrame de productos sin cobertura.
        estados_busqueda: Lista de estados válidos (para el dropdown).
        estados_cadete:   {row_idx → estado} con cambios del cadete (opcional).
    """
    from src.exporter import exportar_excel

    df_exp = df_ruta.drop(columns=["_gtin_key", "prioridad"], errors="ignore").copy()

    # Aplicar actualizaciones de estado hechas desde la vista cadete
    if estados_cadete:
        for idx, estado in estados_cadete.items():
            if idx < len(df_exp) and "Estado de búsqueda" in df_exp.columns:
                df_exp.at[idx, "Estado de búsqueda"] = estado

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        path_tmp = tmp.name

    exportar_excel(
        path_salida=path_tmp,
        df_ruta=df_exp,
        df_sin_stock=df_sin_stock,
        estados_busqueda=estados_busqueda,
    )

    with open(path_tmp, "rb") as f:
        data = f.read()
    os.unlink(path_tmp)
    return data
