"""
exportador.py
Servicio de exportación a Excel: desacopla la lógica de bytes del session_state.

Dos modos de exportación:
  excel_a_bytes()      — formato simple (3 hojas), usado por el historial
  excel_a_bytes_pro()  — formato profesional (4 hojas), usado por el cruce nuevo
"""
import os
import tempfile

import pandas as pd


# Columnas internas — nunca van al Excel
_COLS_INTERNAS = [
    "_gtin_key", "prioridad",
    "_criterio", "_tier", "_consolida_pedido",
    "_gtin_norm", "_sku_norm", "_unidades_int",
    "_id_norm",
]


def excel_a_bytes(
    df_ruta: pd.DataFrame,
    df_sin_stock: pd.DataFrame,
    estados_busqueda: list,
    estados_cadete: dict | None = None,
    gestor_estados=None,
    observaciones_cadete: dict | None = None,
) -> bytes:
    """
    Genera el archivo Excel y devuelve sus bytes.

    Args:
        df_ruta:          DataFrame principal de la planilla.
        df_sin_stock:     DataFrame de productos sin cobertura.
        estados_busqueda: Lista de estados válidos (para el dropdown).
        estados_cadete:   {row_idx → estado} con cambios del cadete (opcional).
        gestor_estados:   GestorEstados activo; si se pasa, enriquece el Excel
                          con columnas 'Estado final', 'Asignación original' y 'Observación'.
    """
    from src.exporter import exportar_excel

    df_exp = df_ruta.drop(columns=_COLS_INTERNAS, errors="ignore").copy()

    # Aplicar estados cadete (dict plano — compatibilidad base)
    if estados_cadete:
        for idx, estado in estados_cadete.items():
            if idx < len(df_exp) and "Estado de búsqueda" in df_exp.columns:
                df_exp.at[idx, "Estado de búsqueda"] = estado

    # Enriquecer con trazabilidad del GestorEstados si está disponible
    if gestor_estados is not None:
        _enriquecer_con_gestor(df_exp, gestor_estados)

    # Agregar columna de observaciones del cadete
    if observaciones_cadete:
        df_exp["Observación cadete"] = [
            observaciones_cadete.get(i, "") for i in df_exp.index
        ]

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


def _enriquecer_con_gestor(df_exp: pd.DataFrame, gestor) -> None:
    """
    Agrega columnas de trazabilidad al DataFrame de exportación:
      - 'Asignación original' : estado que tenía la fila al generar la planilla
      - 'Observación'         : motivo del último cambio de estado
      - 'Reasignado'          : 'Sí' si el ítem pasó por estado REASIGNADO

    Modifica df_exp in-place.
    """
    iniciales   = []
    observaciones = []
    reasignados = []

    for idx in df_exp.index:
        iniciales.append(gestor.estado_inicial_str(idx))
        observaciones.append(gestor.ultimo_motivo(idx))
        reasignados.append("Sí" if gestor.fue_reasignado(idx) else "")

    df_exp["Asignación original"] = iniciales
    df_exp["Observación"]         = observaciones
    df_exp["Reasignado"]          = reasignados


def excel_a_bytes_pro(
    df_ruta: pd.DataFrame,
    df_sin_stock: pd.DataFrame,
    estados_busqueda: list,
    estados_cadete: dict | None = None,
    gestor_estados=None,
    resultado_matching=None,
    resumenes_pedidos: list | None = None,
    archivo_pedidos: str = "",
    archivo_stock: str = "",
    pedidos_unicos: int = 0,
) -> bytes:
    """
    Genera el Excel profesional (4 hojas) y devuelve sus bytes.
    Reemplaza a excel_a_bytes() para el cruce nuevo.
    El historial sigue usando excel_a_bytes() (formato simple).
    """
    from src.exporter import exportar_excel_profesional, DatosExport

    # Aplicar estados del gestor / dict plano al df antes de construir DatosExport
    df_exp = df_ruta.copy()

    if estados_cadete:
        for idx, estado in estados_cadete.items():
            if idx < len(df_exp) and "Estado de búsqueda" in df_exp.columns:
                df_exp.at[idx, "Estado de búsqueda"] = estado

    if gestor_estados is not None:
        _enriquecer_con_gestor(df_exp, gestor_estados)

    datos = DatosExport(
        df_ruta            = df_exp,
        df_sin_stock       = df_sin_stock if df_sin_stock is not None else pd.DataFrame(),
        estados_busqueda   = estados_busqueda,
        gestor_estados     = gestor_estados,
        resultado_matching = resultado_matching,
        resumenes_pedidos  = resumenes_pedidos or [],
        archivo_pedidos    = archivo_pedidos,
        archivo_stock      = archivo_stock,
        pedidos_unicos     = pedidos_unicos,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        path_tmp = tmp.name

    exportar_excel_profesional(datos, path_tmp)

    with open(path_tmp, "rb") as f:
        data = f.read()
    os.unlink(path_tmp)
    return data
