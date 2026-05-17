# app/modules/pagos/mp_client.py
"""
Wrapper liviano sobre el SDK de MercadoPago.
No depende de la BD ni del UnitOfWork.
Se instancia una única vez al importar el módulo.
"""
import mercadopago

from app.core.config import settings
from app.core.exceptions import http_error, PAYMENT_ERROR

# Instancia singleton del SDK — se crea al importar el módulo
sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)


def crear_pago(
    token: str,
    monto: float,
    cuotas: int,
    external_reference: str,
    idempotency_key: str,
    description: str,
) -> dict:
    """
    Crea un pago en MercadoPago usando el token de tarjeta.

    Retorna el dict de respuesta del SDK tal cual.
    Si el SDK retorna un status HTTP de error lanza http_error 402 PAYMENT_ERROR.
    """
    payload = {
        "transaction_amount": monto,
        "token": token,
        "description": description,
        "installments": cuotas,
        "payment_method_id": "visa",          # MP lo infiere del token; se puede omitir
        "external_reference": external_reference,
        "notification_url": settings.MP_NOTIFICATION_URL,
    }

    response = sdk.payment().create(
        payload,
        {"X-Idempotency-Key": idempotency_key},
    )

    # El SDK devuelve {"status": <http_code>, "response": <body>}
    http_status = response.get("status", 500)
    body = response.get("response", {})

    if http_status not in (200, 201):
        detalle = body.get("message") or body.get("error") or "Error al procesar el pago"
        raise http_error(402, detalle, PAYMENT_ERROR)

    return body


def obtener_pago(mp_payment_id: int) -> dict:
    """
    Consulta el estado de un pago existente en MercadoPago.

    Retorna el dict de respuesta del SDK.
    Si el SDK retorna error lanza http_error 402 PAYMENT_ERROR.
    """
    response = sdk.payment().get(mp_payment_id)

    http_status = response.get("status", 500)
    body = response.get("response", {})

    if http_status not in (200, 201):
        detalle = body.get("message") or body.get("error") or "Error al consultar el pago"
        raise http_error(402, detalle, PAYMENT_ERROR)

    return body
