"""
exporter.py
Genera el Excel final con:
  - Pestaña "Planilla Cadete"  : la ruta de búsqueda lista para usar
  - Pestaña "Sin Cobertura"    : productos sin stock en ninguna sucursal
  - Pestaña "Log"              : registro de errores y advertencias

Características:
  - Dropdown en columna "Estado de búsqueda" con openpyxl DataValidation
  - Formato condicional: verde = encontrado, rojo = sin cobertura, amarillo = llamar
  - Encabezados en negrita con color de fondo
  - Columnas con ancho ajustado automáticamente
"""

from __future__ import annotations
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side
)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

from src.logger import get_logger, get_log_records

logger = get_logger(__name__)

# ── Paleta de colores ────────────────────────────────────────
COLOR_HEADER_RUTA    = "2E4057"   # azul oscuro
COLOR_HEADER_SIN     = "8B0000"   # rojo oscuro
COLOR_HEADER_LOG     = "4A4A4A"   # gris oscuro
COLOR_BUSQUEDA       = "FFFFFF"
COLOR_ENCONTRADO     = "C6EFCE"   # verde claro
COLOR_MAL_STOCK      = "FFEB9C"   # amarillo
COLOR_LLAMAR         = "BDD7EE"   # celeste
COLOR_SIN_COBERTURA  = "FFC7CE"   # rojo claro
COLOR_LLAMAR_CLIENTE = "FFC7CE"


def _aplicar_encabezado(ws, color_hex: str):
    """Pone negrita, fondo de color y texto blanco en la primera fila."""
    fill = PatternFill("solid", fgColor=color_hex)
    font = Font(bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _ajustar_ancho(ws):
    """Ajusta el ancho de cada columna al contenido más largo."""
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 4, 50)


def _df_to_sheet(ws, df: pd.DataFrame):
    """Escribe un DataFrame en un worksheet (incluye encabezados)."""
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=value)


def _agregar_dropdown_estado(ws, estados: list[str], col_letra: str, n_filas: int):
    """
    Agrega validación de datos (dropdown) en la columna de estado
    desde la fila 2 hasta n_filas+1.
    """
    formula = '"' + ",".join(estados) + '"'
    dv = DataValidation(
        type="list",
        formula1=formula,
        allow_blank=False,
        showDropDown=False,  # False = mostrar el icono de dropdown
    )
    dv.sqref = f"{col_letra}2:{col_letra}{n_filas + 1}"
    ws.add_data_validation(dv)


def _agregar_formato_condicional_estado(ws, col_letra: str, n_filas: int):
    """
    Colorea la fila completa según el valor de la columna Estado.
    Usa FormulaRule para aplicar color a toda la fila.
    """
    ultima_col = get_column_letter(ws.max_column)
    rango = f"A2:{ultima_col}{n_filas + 1}"

    reglas = [
        ("Encontrado",           COLOR_ENCONTRADO),
        ("Mal stock",            COLOR_MAL_STOCK),
        ("Mal stock - Resuelto", COLOR_MAL_STOCK),
        ("Llamar a suc",         COLOR_LLAMAR),
        ("Llamar cliente",       COLOR_LLAMAR_CLIENTE),
        ("— SIN COBERTURA —",    COLOR_SIN_COBERTURA),
    ]

    for valor, color in reglas:
        fill = PatternFill("solid", fgColor=color)
        # La fórmula ancla a la columna de estado (col_letra) pero aplica a la fila
        formula = f'${col_letra}2="{valor}"'
        ws.conditional_formatting.add(
            rango,
            FormulaRule(formula=[formula], fill=fill)
        )


def exportar_excel(
    path_salida: str,
    df_ruta: pd.DataFrame,
    df_sin_stock: pd.DataFrame,
    estados_busqueda: list[str],
):
    """
    Genera el archivo Excel final.

    path_salida        : ruta completa del archivo a crear
    df_ruta            : planilla del cadete
    df_sin_stock       : productos sin cobertura
    estados_busqueda   : lista de opciones para el dropdown
    """
    wb = Workbook()
    wb.remove(wb.active)  # quitar hoja por defecto

    # ── Pestaña 1: Planilla Cadete ───────────────────────────
    ws_ruta = wb.create_sheet("Planilla Cadete")

    if df_ruta.empty:
        ws_ruta.append(["Sin datos para mostrar"])
    else:
        _df_to_sheet(ws_ruta, df_ruta)
        _aplicar_encabezado(ws_ruta, COLOR_HEADER_RUTA)
        _ajustar_ancho(ws_ruta)

        # Detectar columna "Estado de búsqueda"
        headers = [cell.value for cell in ws_ruta[1]]
        if "Estado de búsqueda" in headers:
            col_idx  = headers.index("Estado de búsqueda") + 1
            col_letra = get_column_letter(col_idx)
            n_filas  = len(df_ruta)
            _agregar_dropdown_estado(ws_ruta, estados_busqueda, col_letra, n_filas)
            _agregar_formato_condicional_estado(ws_ruta, col_letra, n_filas)

        # Congelar la primera fila
        ws_ruta.freeze_panes = "A2"

    # ── Pestaña 2: Sin Cobertura ─────────────────────────────
    ws_sin = wb.create_sheet("Sin Cobertura")
    if df_sin_stock.empty:
        ws_sin.append(["✅ Todos los productos tienen cobertura en sucursales"])
    else:
        _df_to_sheet(ws_sin, df_sin_stock)
        _aplicar_encabezado(ws_sin, COLOR_HEADER_SIN)
        _ajustar_ancho(ws_sin)
        ws_sin.freeze_panes = "A2"

    # ── Pestaña 3: Log ───────────────────────────────────────
    ws_log = wb.create_sheet("Log")
    registros = get_log_records()
    if registros:
        df_log = pd.DataFrame(registros)
        _df_to_sheet(ws_log, df_log)
        _aplicar_encabezado(ws_log, COLOR_HEADER_LOG)
        _ajustar_ancho(ws_log)
    else:
        ws_log.append(["Sin advertencias ni errores registrados"])

    # ── Guardar ──────────────────────────────────────────────
    wb.save(path_salida)
    logger.info(f"Archivo exportado: {path_salida}")
    return path_salida


def generar_nombre_salida(carpeta: str) -> str:
    """Genera un nombre de archivo con timestamp para evitar sobreescribir."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{carpeta}/planilla_cadete_{ts}.xlsx"
