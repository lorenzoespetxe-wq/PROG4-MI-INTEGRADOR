# app/modules/pedidos/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, get_current_user, UserInToken
from app.modules.pedidos.schemas import (
    CrearPedidoRequest,
    AvanzarEstadoRequest,
    PedidoDetail,
    PedidoRead,
    PaginatedPedidos,
    HistorialRead,
)
from app.modules.pedidos.service import PedidoService

router = APIRouter()


@router.get("", response_model=PaginatedPedidos, status_code=status.HTTP_200_OK)
def listar_pedidos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    estado: str | None = Query(default=None),
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Lista pedidos.
    - CLIENT: ve solo sus propios pedidos (filtro de estado ignorado).
    - ADMIN / PEDIDOS: ve todos, con filtro opcional por estado.
    """
    service = PedidoService(uow)
    return service.listar(
        usuario_id=current_user.id,
        roles=current_user.roles,
        page=page,
        size=size,
        estado=estado,
    )


@router.post("", response_model=PedidoDetail, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: CrearPedidoRequest,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Crea un pedido. Requiere autenticación."""
    service = PedidoService(uow)
    return service.crear_pedido(usuario_id=current_user.id, data=data)


@router.get("/{id}", response_model=PedidoDetail, status_code=status.HTTP_200_OK)
def get_pedido(
    id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Devuelve el detalle de un pedido.
    - CLIENT: solo puede ver sus propios pedidos (devuelve 404 si el pedido no es suyo).
    - ADMIN / PEDIDOS: puede ver cualquier pedido.
    """
    service = PedidoService(uow)
    return service.get_detalle(
        usuario_id=current_user.id,
        pedido_id=id,
        roles=current_user.roles,
    )


@router.patch(
    "/{id}/estado",
    response_model=PedidoDetail,
    status_code=status.HTTP_200_OK,
)
def avanzar_estado(
    id: int,
    data: AvanzarEstadoRequest,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Avanza el estado de un pedido.
    - CLIENT: solo puede cancelar sus propios pedidos en estado PENDIENTE o CONFIRMADO.
    - ADMIN / PEDIDOS: pueden aplicar cualquier transición válida.
    """
    service = PedidoService(uow)
    return service.avanzar_estado(
        usuario_id=current_user.id,
        pedido_id=id,
        data=data,
        roles=current_user.roles,
    )


@router.delete("/{id}", response_model=PedidoDetail, status_code=status.HTTP_200_OK)
def cancelar_pedido(
    id: int,
    motivo: str = Query(..., min_length=1, description="Motivo de la cancelación"),
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Cancela el propio pedido (spec §5.3).
    Solo permitido desde PENDIENTE o CONFIRMADO.
    Delega a avanzar_estado con nuevo_estado='CANCELADO'.
    """
    service = PedidoService(uow)
    data = AvanzarEstadoRequest(nuevo_estado="CANCELADO", motivo=motivo)
    return service.avanzar_estado(
        usuario_id=current_user.id,
        pedido_id=id,
        data=data,
        roles=current_user.roles,
    )


@router.get(
    "/{id}/historial",
    response_model=list[HistorialRead],
    status_code=status.HTTP_200_OK,
)
def get_historial(
    id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Devuelve el historial de estados de un pedido, ordenado cronológicamente.
    - CLIENT: solo puede ver el historial de sus propios pedidos.
    - ADMIN / PEDIDOS: puede ver cualquier historial.
    """
    service = PedidoService(uow)
    return service.get_historial(
        usuario_id=current_user.id,
        pedido_id=id,
        roles=current_user.roles,
    )
