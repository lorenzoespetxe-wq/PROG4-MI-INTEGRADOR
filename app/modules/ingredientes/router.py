# app/modules/ingredientes/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, require_role, UserInToken
from app.modules.ingredientes.schemas import (
    IngredienteCreate,
    IngredienteUpdate,
    IngredienteRead,
    PaginatedIngredientes,
)
from app.modules.ingredientes.service import IngredienteService

router = APIRouter()


@router.get("", response_model=PaginatedIngredientes, status_code=status.HTTP_200_OK)
def listar_ingredientes(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    solo_alergenos: bool = Query(False),
    uow: UnitOfWork = Depends(get_uow),
):
    service = IngredienteService(uow)
    return service.listar(page=page, size=size, solo_alergenos=solo_alergenos)


@router.get("/{id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def get_ingrediente(
    id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = IngredienteService(uow)
    return service.get_ingrediente(id)


@router.post("", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED)
def crear_ingrediente(
    data: IngredienteCreate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = IngredienteService(uow)
    return service.crear(data)


@router.patch("/{id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def actualizar_ingrediente(
    id: int,
    data: IngredienteUpdate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = IngredienteService(uow)
    return service.actualizar(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ingrediente(
    id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = IngredienteService(uow)
    service.eliminar(id)
