# app/modules/unidades/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, require_role, UserInToken
from app.modules.unidades.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
)
from app.modules.unidades.service import UnidadMedidaService

router = APIRouter()


@router.get("", response_model=list[UnidadMedidaRead], status_code=status.HTTP_200_OK)
def listar_unidades(
    tipo: str | None = Query(default=None),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UnidadMedidaService(uow)
    unidades = service.listar(page=1, size=100)
    if tipo:
        unidades = [u for u in unidades if u.tipo == tipo]
    return unidades


@router.get("/{id}", response_model=UnidadMedidaRead, status_code=status.HTTP_200_OK)
def obtener_unidad(
    id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = UnidadMedidaService(uow)
    return service.obtener_por_id(id)


@router.post("", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED)
def crear_unidad(
    data: UnidadMedidaCreate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UnidadMedidaService(uow)
    return service.crear(data)


@router.put("/{id}", response_model=UnidadMedidaRead, status_code=status.HTTP_200_OK)
def actualizar_unidad(
    id: int,
    data: UnidadMedidaUpdate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UnidadMedidaService(uow)
    return service.actualizar(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad(
    id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UnidadMedidaService(uow)
    service.eliminar(id)
