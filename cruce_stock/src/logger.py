"""
logger.py
Logger centralizado. Guarda todo en memoria para exportarlo
al Excel final como pestaña "Log", además de mostrarlo en consola.
"""

import logging
from datetime import datetime


# Almacén en memoria de todos los registros
_log_records: list[dict] = []


class _MemoryHandler(logging.Handler):
    """Handler que captura registros en la lista global."""
    def emit(self, record: logging.LogRecord):
        _log_records.append({
            "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "nivel":     record.levelname,
            "modulo":    record.name,
            "mensaje":   self.format(record),
        })


def get_logger(name: str) -> logging.Logger:
    """Devuelve (o crea) un logger con handler de consola y memoria."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        fmt = logging.Formatter("%(levelname)s | %(name)s | %(message)s")

        # Consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # Memoria
        mh = _MemoryHandler()
        mh.setLevel(logging.DEBUG)
        mh.setFormatter(fmt)
        logger.addHandler(mh)

    return logger


def get_log_records() -> list[dict]:
    """Devuelve todos los registros acumulados."""
    return list(_log_records)


def limpiar_log():
    """Limpia el log para una nueva ejecución."""
    _log_records.clear()
