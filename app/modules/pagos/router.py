# app/modules/pagos/router.py
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, get_current_user, require_role, UserInToken
from app.modules.pagos.schemas import CrearPagoRequest, PagoRead
from app.modules.pagos.service import PagoService

router = APIRouter()


@router.post(
    "/crear",
    response_model=PagoRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_pago(
    data: CrearPagoRequest,
    current_user: UserInToken = Depends(require_role("CLIENT")),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Inicia el cobro de un pedido via MercadoPago.
    Si el pago es aprobado de inmediato, el pedido avanza a CONFIRMADO
    en la misma transacción.
    Rol requerido: CLIENT (el propietario del pedido).
    """
    service = PagoService(uow)
    return service.crear_pago(usuario_id=current_user.id, data=data)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
)
def webhook_mercadopago(
    id: int | None = Query(default=None),
    topic: str | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Endpoint público llamado por MercadoPago con notificaciones IPN.
    Solo procesa notificaciones de tipo 'payment'.
    Siempre retorna 200 — nunca expone errores internos a MP.
    """
    if topic == "payment" and id is not None:
        service = PagoService(uow)
        service.procesar_webhook(mp_payment_id=id)

    return JSONResponse(content={"status": "ok"})


@router.get(
    "/{pedido_id}",
    response_model=PagoRead,
    status_code=status.HTTP_200_OK,
)
def get_pago(
    pedido_id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Devuelve el pago asociado a un pedido.
    CLIENT: solo puede ver el pago de sus propios pedidos (devuelve 404 si no es suyo).
    ADMIN / PEDIDOS: puede ver cualquier pago.
    """
    service = PagoService(uow)
    return service.get_pago_por_pedido(
        usuario_id=current_user.id,
        pedido_id=pedido_id,
        roles=current_user.roles,
    )
