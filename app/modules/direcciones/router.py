# app/modules/direcciones/router.py
from fastapi import APIRouter, Depends, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, get_current_user, UserInToken
from app.modules.direcciones.schemas import (
    DireccionCreate,
    DireccionUpdate,
    DireccionRead,
)
from app.modules.direcciones.service import DireccionService

router = APIRouter()


@router.get("", response_model=list[DireccionRead], status_code=status.HTTP_200_OK)
def listar(
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DireccionService(uow)
    return service.listar(current_user.id)


@router.post("", response_model=DireccionRead, status_code=status.HTTP_201_CREATED)
def crear(
    data: DireccionCreate,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DireccionService(uow)
    return service.crear(current_user.id, data)


@router.put("/{id}", response_model=DireccionRead, status_code=status.HTTP_200_OK)
def actualizar(
    id: int,
    data: DireccionUpdate,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DireccionService(uow)
    return service.actualizar(current_user.id, id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DireccionService(uow)
    service.eliminar(current_user.id, id)


@router.patch(
    "/{id}/principal", response_model=DireccionRead, status_code=status.HTTP_200_OK
)
def establecer_principal(
    id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = DireccionService(uow)
    return service.establecer_principal(current_user.id, id)
