"""
estados.py
Modelo de estados operativos para ítems del cruce de stock.

Diseño:
  - EstadoItem     : constantes de estado + etiquetas para UI
  - Transiciones   : reglas de qué estado puede pasar a qué otro
  - EventoEstado   : registro inmutable de un cambio (trazabilidad)
  - GestorEstados  : administra eventos y expone el estado actual

El GestorEstados se guarda en session_state["gestor_estados"].
El dict plano session_state["estados_cadete"] sigue existiendo
para compatibilidad con el servidor compartido y el exportador —
GestorEstados lo actualiza automáticamente.

No importa streamlit directamente: sus métodos reciben
session_state como argumento para ser testeables de forma aislada.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ════════════════════════════════════════════════════════════
#  ESTADOS
# ════════════════════════════════════════════════════════════

class EstadoItem(str, Enum):
    """
    Estados operativos de un ítem de planilla.
    Hereda de str para que sea serializable y comparable con strings.
    """
    PENDIENTE     = "Búsqueda"           # estado inicial (compatible con nombre existente)
    ENCONTRADO    = "Encontrado"
    NO_ENCONTRADO = "No encontrado"
    REASIGNADO    = "Reasignado"          # nuevo estado — se reasignó a otra sucursal
    SIN_COBERTURA = "Sin cobertura"       # sin alternativa disponible
    EN_REVISION   = "En revisión"         # requiere confirmación humana

    @classmethod
    def desde_str(cls, valor: str) -> "EstadoItem":
        """Convierte un string al estado correspondiente. Devuelve PENDIENTE si no matchea."""
        mapa = {e.value.lower(): e for e in cls}
        # compatibilidad con nombres anteriores
        alias = {
            "busqueda":          cls.PENDIENTE,
            "requiere revision": cls.EN_REVISION,
            "requiere revisión": cls.EN_REVISION,
            "mal stock":         cls.EN_REVISION,
            "llamar a suc":      cls.EN_REVISION,
            "llamar cliente":    cls.SIN_COBERTURA,
            "mal stock - resuelto": cls.ENCONTRADO,
            "reasignado":        cls.REASIGNADO,
            "sin cobertura":     cls.SIN_COBERTURA,
        }
        key = str(valor).strip().lower()
        return mapa.get(key) or alias.get(key) or cls.PENDIENTE

    def label_ui(self) -> str:
        """Etiqueta corta para mostrar en la UI."""
        return self.value

    def es_terminal(self) -> bool:
        """True si el estado no puede transicionar hacia delante."""
        return self in (self.ENCONTRADO, self.SIN_COBERTURA)


# ════════════════════════════════════════════════════════════
#  TRANSICIONES VÁLIDAS
# ════════════════════════════════════════════════════════════

TRANSICIONES: dict[EstadoItem, set[EstadoItem]] = {
    EstadoItem.PENDIENTE:     {
        EstadoItem.ENCONTRADO,
        EstadoItem.NO_ENCONTRADO,
        EstadoItem.EN_REVISION,
        EstadoItem.SIN_COBERTURA,
    },
    EstadoItem.NO_ENCONTRADO: {
        EstadoItem.REASIGNADO,
        EstadoItem.EN_REVISION,
        EstadoItem.SIN_COBERTURA,
    },
    EstadoItem.EN_REVISION:   {
        EstadoItem.ENCONTRADO,
        EstadoItem.REASIGNADO,
        EstadoItem.SIN_COBERTURA,
        EstadoItem.NO_ENCONTRADO,
    },
    EstadoItem.REASIGNADO:    {
        EstadoItem.ENCONTRADO,
        EstadoItem.NO_ENCONTRADO,
        EstadoItem.EN_REVISION,
    },
    EstadoItem.ENCONTRADO:    set(),   # terminal
    EstadoItem.SIN_COBERTURA: set(),   # terminal
}


def transicion_valida(desde: EstadoItem, hacia: EstadoItem) -> bool:
    return hacia in TRANSICIONES.get(desde, set())


# ════════════════════════════════════════════════════════════
#  EVENTO DE ESTADO
# ════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class EventoEstado:
    """Registro inmutable de un cambio de estado. Base de la trazabilidad."""
    idx:              int           # índice de fila en df_ruta
    estado_anterior:  str           # valor antes del cambio
    estado_nuevo:     str           # valor después del cambio
    motivo:           str = ""      # razón del cambio (libre, puede quedar vacío)
    farmacia_original: str = ""     # sucursal que tenía asignada antes
    farmacia_nueva:    str = ""     # sucursal nueva si hubo reasignación
    timestamp:        str = field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S")
    )
    origen:           str = "cadete"  # "cadete" | "oficina" | "sistema"


# ════════════════════════════════════════════════════════════
#  GESTOR DE ESTADOS
# ════════════════════════════════════════════════════════════

class GestorEstados:
    """
    Administra los estados de todos los ítems de la planilla activa.

    Responsabilidades:
      - Mantener el estado actual de cada fila (idx → EstadoItem)
      - Registrar el historial de eventos (trazabilidad)
      - Validar transiciones antes de aplicarlas
      - Mantener sincronizado el dict plano (compatibilidad)

    Uso:
        gestor = GestorEstados.desde_df(df_ruta)
        ok, msg = gestor.transicionar(idx=3, nuevo="No encontrado", motivo="No había stock")
        session_state["estados_cadete"][3] = gestor.estado_str(3)
    """

    def __init__(self) -> None:
        # Estado actual: {idx → EstadoItem}
        self._estados:  dict[int, EstadoItem] = {}
        # Estado inicial registrado al cargar la planilla
        self._inicial:  dict[int, EstadoItem] = {}
        # Historial de eventos: [{idx → [EventoEstado]}]
        self._historial: dict[int, list[EventoEstado]] = {}

    # ── Construcción ────────────────────────────────────────

    @classmethod
    def desde_df(cls, df) -> "GestorEstados":
        """
        Inicializa el gestor a partir del df_ruta.
        Lee la columna 'Estado de búsqueda' como estado inicial.
        """
        g = cls()
        if df is None or df.empty:
            return g
        col = "Estado de búsqueda"
        for idx in df.index:
            val = str(df.at[idx, col]) if col in df.columns else "Búsqueda"
            estado = EstadoItem.desde_str(val)
            g._estados[idx]  = estado
            g._inicial[idx]  = estado
        return g

    @classmethod
    def desde_dict_plano(cls, estados_cadete: dict, df=None) -> "GestorEstados":
        """
        Reconstruye el gestor desde el dict plano existente (compatibilidad
        con sesiones que ya tenían estados_cadete).
        """
        g = cls.desde_df(df) if df is not None else cls()
        for idx, val in estados_cadete.items():
            g._estados[int(idx)] = EstadoItem.desde_str(val)
        return g

    # ── Transiciones ────────────────────────────────────────

    def transicionar(
        self,
        idx: int,
        nuevo: str | EstadoItem,
        motivo: str = "",
        farmacia_nueva: str = "",
        origen: str = "cadete",
    ) -> tuple[bool, str]:
        """
        Cambia el estado de un ítem. Valida la transición antes de aplicarla.

        Returns:
            (True, "") si OK
            (False, mensaje_error) si la transición no es válida
        """
        estado_nuevo = EstadoItem.desde_str(str(nuevo)) if isinstance(nuevo, str) else nuevo
        estado_actual = self._estados.get(idx, EstadoItem.PENDIENTE)

        if not transicion_valida(estado_actual, estado_nuevo):
            return False, (
                f"Transición no permitida: {estado_actual.value} → {estado_nuevo.value}. "
                f"Desde '{estado_actual.value}' se puede ir a: "
                f"{', '.join(e.value for e in TRANSICIONES.get(estado_actual, set()))}"
            )

        evento = EventoEstado(
            idx               = idx,
            estado_anterior   = estado_actual.value,
            estado_nuevo      = estado_nuevo.value,
            motivo            = motivo,
            farmacia_nueva    = farmacia_nueva,
            origen            = origen,
        )
        self._historial.setdefault(idx, []).append(evento)
        self._estados[idx] = estado_nuevo
        return True, ""

    def forzar(
        self,
        idx: int,
        nuevo: str | EstadoItem,
        motivo: str = "",
        origen: str = "sistema",
    ) -> None:
        """
        Aplica un estado sin validar la transición. Solo para uso del sistema
        (al inicializar desde estados_cadete existentes o al resetear).
        """
        estado_nuevo = EstadoItem.desde_str(str(nuevo)) if isinstance(nuevo, str) else nuevo
        estado_actual = self._estados.get(idx, EstadoItem.PENDIENTE)
        evento = EventoEstado(
            idx             = idx,
            estado_anterior = estado_actual.value,
            estado_nuevo    = estado_nuevo.value,
            motivo          = motivo,
            origen          = origen,
        )
        self._historial.setdefault(idx, []).append(evento)
        self._estados[idx] = estado_nuevo

    def resetear(self, idx: int) -> None:
        """Vuelve un ítem a su estado inicial (el que tenía al cargar la planilla)."""
        inicial = self._inicial.get(idx, EstadoItem.PENDIENTE)
        self.forzar(idx, inicial, motivo="reset manual", origen="sistema")

    # ── Consulta ────────────────────────────────────────────

    def estado(self, idx: int) -> EstadoItem:
        return self._estados.get(idx, EstadoItem.PENDIENTE)

    def estado_str(self, idx: int) -> str:
        return self.estado(idx).value

    def estado_inicial_str(self, idx: int) -> str:
        return self._inicial.get(idx, EstadoItem.PENDIENTE).value

    def historial(self, idx: int) -> list[EventoEstado]:
        return list(self._historial.get(idx, []))

    def ultimo_motivo(self, idx: int) -> str:
        """Motivo del último cambio de estado registrado."""
        eventos = self._historial.get(idx, [])
        return eventos[-1].motivo if eventos else ""

    def fue_reasignado(self, idx: int) -> bool:
        return any(e.estado_nuevo == EstadoItem.REASIGNADO.value
                   for e in self._historial.get(idx, []))

    def to_dict_plano(self) -> dict[int, str]:
        """Serializa para session_state["estados_cadete"] (compatibilidad)."""
        return {idx: e.value for idx, e in self._estados.items()}

    # ── Métricas ────────────────────────────────────────────

    def resumen(self) -> dict:
        """Conteo de estados para métricas de dashboard."""
        conteo: dict[str, int] = {}
        for estado in self._estados.values():
            conteo[estado.value] = conteo.get(estado.value, 0) + 1
        total = len(self._estados)
        enc   = conteo.get(EstadoItem.ENCONTRADO.value, 0)
        return {
            "total":        total,
            "encontrado":   enc,
            "no_encontrado":conteo.get(EstadoItem.NO_ENCONTRADO.value, 0),
            "en_revision":  conteo.get(EstadoItem.EN_REVISION.value, 0),
            "reasignado":   conteo.get(EstadoItem.REASIGNADO.value, 0),
            "sin_cobertura":conteo.get(EstadoItem.SIN_COBERTURA.value, 0),
            "pendiente":    conteo.get(EstadoItem.PENDIENTE.value, 0),
            "pct_completado": round(enc / total * 100, 1) if total else 0.0,
        }

    def filas_con_estado(self, estado: str | EstadoItem) -> list[int]:
        """Devuelve índices de filas que tienen el estado indicado."""
        target = EstadoItem.desde_str(str(estado)) if isinstance(estado, str) else estado
        return [idx for idx, e in self._estados.items() if e == target]
