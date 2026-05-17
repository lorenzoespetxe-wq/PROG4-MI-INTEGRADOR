# app/modules/productos/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, require_role, UserInToken
from app.modules.productos.schemas import (
    ProductoCreate,
    ProductoUpdate,
    ProductoRead,
    ProductoDetail,
    PaginatedProductos,
    IngredienteEnProductoRequest,
    IngredienteEnProductoRead,
    StockUpdateRequest,
    DisponibilidadRequest,
)
from app.modules.productos.service import ProductoService

router = APIRouter()


@router.get("", response_model=PaginatedProductos, status_code=status.HTTP_200_OK)
def listar_productos(
    search: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    disponible: bool | None = Query(default=None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.listar(
        search=search,
        categoria_id=categoria_id,
        disponible=disponible,
        page=page,
        size=size,
    )


@router.get("/{id}", response_model=ProductoDetail, status_code=status.HTTP_200_OK)
def get_producto(
    id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.get_detalle(id)


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def crear_producto(
    data: ProductoCreate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.crear(data)


@router.put("/{id}", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def actualizar_producto(
    id: int,
    data: ProductoUpdate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.actualizar(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    service.eliminar(id)


@router.patch(
    "/{id}/disponibilidad",
    response_model=ProductoRead,
    status_code=status.HTTP_200_OK,
)
def cambiar_disponibilidad(
    id: int,
    data: DisponibilidadRequest,
    current_user: UserInToken = Depends(require_role("ADMIN", "STOCK")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.cambiar_disponibilidad(id, data)


@router.patch(
    "/{id}/stock",
    response_model=ProductoRead,
    status_code=status.HTTP_200_OK,
)
def actualizar_stock(
    id: int,
    data: StockUpdateRequest,
    current_user: UserInToken = Depends(require_role("ADMIN", "STOCK")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.actualizar_stock(id, data)


@router.get(
    "/{id}/ingredientes",
    response_model=list[IngredienteEnProductoRead],
    status_code=status.HTTP_200_OK,
)
def get_ingredientes_producto(
    id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.get_ingredientes(id)


@router.post(
    "/{id}/ingredientes",
    response_model=ProductoDetail,
    status_code=status.HTTP_201_CREATED,
)
def agregar_ingrediente(
    id: int,
    data: IngredienteEnProductoRequest,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    return service.agregar_ingrediente(id, data)


@router.delete(
    "/{id}/ingredientes/{ingrediente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def quitar_ingrediente(
    id: int,
    ingrediente_id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = ProductoService(uow)
    service.quitar_ingrediente(id, ingrediente_id)
