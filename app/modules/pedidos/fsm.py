# app/modules/pedidos/fsm.py
from app.core.exceptions import http_error, INVALID_TRANSITION, TERMINAL_STATE

# Mapa de transiciones válidas por estado
TRANSICIONES: dict[str, list[str]] = {
    "PENDIENTE": ["CONFIRMADO", "CANCELADO"],
    "CONFIRMADO": ["EN_PREP", "CANCELADO"],
    "EN_PREP": ["EN_CAMINO", "CANCELADO"],
    "EN_CAMINO": ["ENTREGADO"],
    "ENTREGADO": [],
    "CANCELADO": [],
}

# Estados que no admiten más transiciones
TERMINALES: set[str] = {"ENTREGADO", "CANCELADO"}

# Estados donde el stock ya fue descontado; si se cancela desde uno de estos
# hay que restaurar el stock
ESTADOS_CON_STOCK_DESCONTADO: set[str] = {
    "PENDIENTE",
    "CONFIRMADO",
    "EN_PREP",
    "EN_CAMINO",
}


def validar_transicion(estado_actual: str, nuevo_estado: str) -> None:
    """
    Valida que la transición de estado sea permitida por la FSM.

    Lanza:
    - http_error 409 TERMINAL_STATE   — si el estado actual es terminal.
    - http_error 422 INVALID_TRANSITION — si la transición no está en el mapa.
    """
    if estado_actual in TERMINALES:
        raise http_error(
            409,
            f"El pedido está en estado terminal '{estado_actual}' y no puede avanzar",
            TERMINAL_STATE,
        )

    destinos_validos = TRANSICIONES.get(estado_actual, [])
    if nuevo_estado not in destinos_validos:
        raise http_error(
            422,
            f"Transición inválida: '{estado_actual}' → '{nuevo_estado}'. "
            f"Destinos permitidos: {destinos_validos}",
            INVALID_TRANSITION,
        )
