"""
state.py
Gestión de estado de la aplicación: servidor compartido y sesión local.
"""
from datetime import datetime

import pandas as pd
import streamlit as st


# ════════════════════════════════════════════════════════════
#  ESTADO COMPARTIDO — sincronización cadete ↔ oficina
# ════════════════════════════════════════════════════════════

@st.cache_resource
def _servidor_estado() -> dict:
    """
    Diccionario compartido entre TODAS las sesiones del servidor.
    Permite que los cambios del cadete sean visibles desde oficina
    sin recargar la página (con botón de sync manual).

    IMPORTANTE: se pierde si Streamlit Cloud reinicia el servidor
    (~30 min de inactividad en free tier). Para operación dentro
    del mismo día de trabajo esto es aceptable.
    """
    return {
        "estados_cadete":       {},    # {row_idx(int) → estado(str)}
        "ultima_actualizacion": None,  # str "HH:MM:SS" o None
        "sesion_activa":        False, # True cuando el cadete abrió la vista
    }


def _set_estado_cadete(idx: int, estado: str):
    """
    Actualiza el estado de un ítem en la sesión local Y en el
    estado compartido del servidor (visible desde otras sesiones).
    """
    st.session_state.estados_cadete[idx] = estado
    srv = _servidor_estado()
    srv["estados_cadete"][idx] = estado
    srv["ultima_actualizacion"] = datetime.now().strftime("%H:%M:%S")
    srv["sesion_activa"] = True


def _sincronizar_desde_servidor():
    """
    Trae los estados del servidor a la sesión local.
    Acción del operador de oficina para ver el avance real del cadete.
    """
    srv = _servidor_estado()
    if srv["estados_cadete"]:
        st.session_state.estados_cadete = dict(srv["estados_cadete"])


# ════════════════════════════════════════════════════════════
#  SESIÓN LOCAL
# ════════════════════════════════════════════════════════════

def _init_session():
    defaults = {
        "pagina":              "dashboard",
        "historial":           [],
        "ultimo_resultado":    None,
        "stock_por_producto":  {},
        "overrides":           {},
        "df_ruta_editable":    None,
        "vista_planilla":      "pedido",   # "pedido" | "ruta"
        "estados_cadete":      {},         # {row_idx → estado actualizado por el cadete}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _ir_a(pagina: str):
    st.session_state.pagina = pagina


def _agregar_historial(nombre_ped, nombre_stk, filas, sin_cob, excel_bytes, filename):
    n = len(st.session_state.historial) + 1
    st.session_state.historial.insert(0, {
        "id":       f"C{n:03d}",
        "pedidos":  nombre_ped,
        "stock":    nombre_stk,
        "hora":     datetime.now().strftime("%H:%M  %d/%m/%y"),
        "filas":    filas,
        "sin_cob":  sin_cob,
        "bytes":    excel_bytes,
        "filename": filename,
    })


def _aplicar_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza la columna Farmacia según los overrides guardados."""
    df = df.copy()
    for idx, nuevo_nodo in st.session_state.overrides.items():
        if idx < len(df):
            df.at[idx, "Farmacia"] = nuevo_nodo
            # Recalcular estado sugerido según si es remota o no
            zona_nueva = st.session_state.get(f"_zona_override_{idx}", "")
            if "Remota" in zona_nueva:
                df.at[idx, "Estado de búsqueda"] = "Llamar a suc"
    return df
