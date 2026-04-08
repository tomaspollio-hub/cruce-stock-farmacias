"""
state.py
Gestión de estado de la aplicación: servidor compartido y sesión local.
"""
from __future__ import annotations
from datetime import datetime

import pandas as pd
import streamlit as st

# Import lazy para evitar que un error en src.services.estados
# rompa el arranque completo de la app.
def _get_gestor_cls():
    from src.services.estados import GestorEstados
    return GestorEstados


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


def _set_estado_cadete(
    idx: int,
    estado: str,
    motivo: str = "",
    farmacia_nueva: str = "",
    origen: str = "cadete",
    forzar: bool = False,
) -> tuple[bool, str]:
    """
    Actualiza el estado de un ítem en la sesión local Y en el
    estado compartido del servidor (visible desde otras sesiones).

    Delega al GestorEstados para validar la transición y registrar
    el evento con trazabilidad.

    Args:
        forzar: si True, salta la validación de transición (para resets del sistema).

    Returns:
        (True, "") si OK | (False, mensaje_error) si transición inválida.
    """
    gestor = st.session_state.get("gestor_estados") or _get_gestor_cls()()

    if forzar:
        gestor.forzar(idx, estado, motivo=motivo, origen=origen)
        ok, msg = True, ""
    else:
        ok, msg = gestor.transicionar(
            idx, estado, motivo=motivo, farmacia_nueva=farmacia_nueva, origen=origen
        )

    if ok:
        # Sincronizar dict plano (compatibilidad con servidor + exportador)
        estado_final = gestor.estado_str(idx)
        st.session_state.estados_cadete[idx] = estado_final
        st.session_state["gestor_estados"] = gestor

        srv = _servidor_estado()
        srv["estados_cadete"][idx] = estado_final
        srv["ultima_actualizacion"] = datetime.now().strftime("%H:%M:%S")
        srv["sesion_activa"] = True

    return ok, msg


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
        "gestor_estados":      None,       # GestorEstados activo (se crea al generar planilla)
        "observaciones_cadete":{},         # {row_idx → str} observaciones registradas por el cadete
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _inicializar_gestor(df_ruta) -> None:
    """
    Crea un GestorEstados nuevo a partir del df_ruta recién generado.
    Llama después de construir_planilla() para arrancar la sesión limpia.
    """
    gestor = _get_gestor_cls().desde_df(df_ruta)
    st.session_state["gestor_estados"] = gestor
    # Sincronizar dict plano desde el nuevo gestor
    st.session_state["estados_cadete"] = gestor.to_dict_plano()


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
