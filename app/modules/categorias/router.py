# app/modules/categorias/router.py
from fastapi import APIRouter, Depends, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, require_role, UserInToken
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaRead,
    CategoriaTree,
)
from app.modules.categorias.service import CategoriaService

router = APIRouter()


@router.get("", response_model=list[CategoriaRead], status_code=status.HTTP_200_OK)
def listar_categorias(
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    return service.listar()


@router.get(
    "/arbol", response_model=list[CategoriaTree], status_code=status.HTTP_200_OK
)
def listar_categorias_arbol(
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    return service.listar_arbol()


@router.get("/{id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def get_categoria(
    id: int,
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    return service.get_categoria(id)


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    data: CategoriaCreate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    return service.crear(data)


@router.put("/{id}", response_model=CategoriaRead, status_code=status.HTTP_200_OK)
def actualizar_categoria(
    id: int,
    data: CategoriaUpdate,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    return service.actualizar(id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = CategoriaService(uow)
    service.eliminar(id)
