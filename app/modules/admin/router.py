# app/modules/admin/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, require_role, UserInToken
from app.modules.admin.schemas import (
    DashboardMetrics,
    StockBulkUpdate,
    StockBulkResponse,
)
from app.modules.admin.service import AdminService
from app.modules.pedidos.schemas import PaginatedPedidos

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardMetrics,
    status_code=status.HTTP_200_OK,
)
def get_dashboard(
    umbral_stock: int = Query(default=5, ge=0, description="Stock mínimo para alertas"),
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Métricas de negocio en tiempo real:
    pedidos de hoy, ingresos, conteo por estado,
    productos bajo stock y top 5 más vendidos.
    Rol requerido: ADMIN.
    """
    service = AdminService(uow)
    return service.get_dashboard(umbral_stock=umbral_stock)


@router.get(
    "/pedidos-activos",
    response_model=PaginatedPedidos,
    status_code=status.HTTP_200_OK,
)
def get_pedidos_activos(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: UserInToken = Depends(require_role("ADMIN", "PEDIDOS")),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Lista paginada de pedidos en curso (excluye ENTREGADO y CANCELADO),
    ordenados de más antiguo a más reciente para facilitar la gestión operativa.
    Roles requeridos: ADMIN o PEDIDOS.
    """
    service = AdminService(uow)
    return service.get_pedidos_activos(page=page, size=size)


@router.post(
    "/stock/bulk",
    response_model=StockBulkResponse,
    status_code=status.HTTP_200_OK,
)
def actualizar_stock_bulk(
    data: StockBulkUpdate,
    current_user: UserInToken = Depends(require_role("ADMIN", "STOCK")),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Actualiza el stock de hasta 50 productos en una única transacción.
    Los IDs inexistentes se reportan en el campo 'errores' sin cancelar
    las actualizaciones válidas.
    Roles requeridos: ADMIN o STOCK.
    """
    service = AdminService(uow)
    return service.actualizar_stock_bulk(data)
