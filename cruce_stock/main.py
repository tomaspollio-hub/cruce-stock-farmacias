"""
main.py
Orquestador del pipeline de cruce de stock.
Puede usarse desde la terminal o importarse por la GUI (app.py).

Uso desde terminal:
  python main.py --pedidos ruta/pedidos.xlsx --stock ruta/stock.csv
  python main.py --pedidos ruta/pedidos.xlsx --stock ruta/stock.csv --salida ./resultados
"""

from __future__ import annotations
import argparse
import pathlib
import sys
import yaml

from src.loader     import cargar_archivo
from src.matcher    import mapear_columnas_pedidos, mapear_columnas_stock
from src.optimizer  import construir_planilla
from src.exporter   import exportar_excel, generar_nombre_salida
from src.logger     import get_logger, limpiar_log

logger = get_logger("main")

CONFIG_PATH = pathlib.Path(__file__).parent / "config.yaml"


def cargar_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ejecutar(
    path_pedidos: str,
    path_stock: str,
    carpeta_salida: str = ".",
    callback_progreso=None,   # función opcional para actualizar la GUI
) -> dict:
    """
    Pipeline completo. Devuelve un dict con resumen de resultados.

    callback_progreso: callable(mensaje: str) para notificar pasos a la GUI.
    """
    limpiar_log()

    def progreso(msg: str):
        logger.info(msg)
        if callback_progreso:
            callback_progreso(msg)

    cfg = cargar_config()

    # ── 1. Carga de archivos ────────────────────────────────
    progreso("📂 Cargando archivo de pedidos...")
    try:
        df_pedidos = cargar_archivo(path_pedidos)
    except Exception as e:
        raise RuntimeError(f"Error al leer pedidos: {e}") from e

    progreso("📂 Cargando archivo de stock de sucursales...")
    try:
        df_stock = cargar_archivo(path_stock)
    except Exception as e:
        raise RuntimeError(f"Error al leer stock: {e}") from e

    progreso(f"   Pedidos: {len(df_pedidos)} filas | Stock: {len(df_stock)} filas")

    # ── 2. Detección de columnas ────────────────────────────
    progreso("🔍 Detectando columnas automáticamente...")
    try:
        mapa_pedidos = mapear_columnas_pedidos(df_pedidos, cfg)
        mapa_stock   = mapear_columnas_stock(df_stock, cfg)
    except ValueError as e:
        raise RuntimeError(f"Error en detección de columnas: {e}") from e

    progreso(f"   Columnas pedidos: {mapa_pedidos}")
    progreso(f"   Columnas stock:   {mapa_stock}")

    # ── 3. Cruce y optimización ─────────────────────────────
    progreso("⚙️  Cruzando pedidos con stock y optimizando sucursales...")
    df_ruta, df_sin_stock = construir_planilla(
        df_pedidos=df_pedidos,
        df_stock=df_stock,
        mapa_pedidos=mapa_pedidos,
        mapa_stock=mapa_stock,
        cfg=cfg,
    )

    # ── 4. Exportar ─────────────────────────────────────────
    progreso("💾 Generando archivo Excel...")
    path_salida = generar_nombre_salida(carpeta_salida)
    exportar_excel(
        path_salida=path_salida,
        df_ruta=df_ruta,
        df_sin_stock=df_sin_stock,
        estados_busqueda=cfg["estados_busqueda"],
    )

    # ── 5. Resumen ──────────────────────────────────────────
    resumen = {
        "path_salida":         path_salida,
        "filas_planilla":      len(df_ruta),
        "productos_sin_cobertura": len(df_sin_stock),
        "pedidos_procesados":  len(
            df_pedidos[
                df_pedidos[mapa_pedidos["estado"]]
                .apply(lambda v: str(v).strip().lower()) == cfg["pedidos"]["estado_activo"].lower()
            ]
        ),
    }

    progreso(
        f"✅ Listo. "
        f"{resumen['pedidos_procesados']} pedidos activos → "
        f"{resumen['filas_planilla']} filas en planilla | "
        f"{resumen['productos_sin_cobertura']} sin cobertura."
    )

    return resumen


# ── Entrada por terminal ─────────────────────────────────────
def _cli():
    parser = argparse.ArgumentParser(
        description="Cruce de pedidos ecommerce con stock de sucursales."
    )
    parser.add_argument("--pedidos", required=True, help="Archivo de pedidos (.xlsx o .csv)")
    parser.add_argument("--stock",   required=True, help="Archivo de stock de sucursales (.xlsx o .csv)")
    parser.add_argument("--salida",  default=".",   help="Carpeta de salida (default: directorio actual)")
    args = parser.parse_args()

    try:
        resumen = ejecutar(args.pedidos, args.stock, args.salida)
        print(f"\n📁 Archivo generado: {resumen['path_salida']}")
        sys.exit(0)
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    _cli()
