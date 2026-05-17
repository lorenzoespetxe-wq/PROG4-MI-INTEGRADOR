# app/modules/usuarios/router.py
from fastapi import APIRouter, Depends, Query, status

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, get_current_user, require_role, UserInToken
from app.core.exceptions import http_error, FORBIDDEN
from app.modules.usuarios.schemas import (
    UsuarioUpdate,
    UsuarioRead,
    PaginatedUsuarios,
    AsignarRolRequest,
)
from app.modules.usuarios.service import UsuarioService

router = APIRouter()


@router.get("", response_model=PaginatedUsuarios, status_code=status.HTTP_200_OK)
def list_usuarios(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UsuarioService(uow)
    return service.list_usuarios(page, size)


@router.get("/{id}", response_model=UsuarioRead, status_code=status.HTTP_200_OK)
def get_usuario(
    id: int,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    if id != current_user.id and "ADMIN" not in current_user.roles:
        raise http_error(403, "Permisos insuficientes", FORBIDDEN)

    service = UsuarioService(uow)
    return service.get_usuario(id)


@router.patch("/{id}", response_model=UsuarioRead, status_code=status.HTTP_200_OK)
def update_usuario(
    id: int,
    data: UsuarioUpdate,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    if id != current_user.id and "ADMIN" not in current_user.roles:
        raise http_error(403, "Permisos insuficientes", FORBIDDEN)

    service = UsuarioService(uow)
    return service.update_usuario(id, data, current_user.id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    id: int,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UsuarioService(uow)
    service.delete_usuario(id, current_user.id)


@router.post("/{id}/roles", response_model=UsuarioRead, status_code=status.HTTP_200_OK)
def asignar_rol(
    id: int,
    data: AsignarRolRequest,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UsuarioService(uow)
    return service.asignar_rol(id, data, current_user.id)


@router.delete("/{id}/roles/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def revocar_rol(
    id: int,
    codigo: str,
    current_user: UserInToken = Depends(require_role("ADMIN")),
    uow: UnitOfWork = Depends(get_uow),
):
    service = UsuarioService(uow)
    service.revocar_rol(id, codigo, current_user.id)
