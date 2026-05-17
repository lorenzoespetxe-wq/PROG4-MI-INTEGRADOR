# app/modules/usuarios/service.py
import math
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND, ALREADY_EXISTS, FORBIDDEN
from app.modules.usuarios.model import Usuario, UsuarioRol
from app.modules.usuarios.schemas import (
    UsuarioUpdate,
    UsuarioRead,
    PaginatedUsuarios,
    AsignarRolRequest,
)
from app.modules.usuarios.repository import UsuarioRepository, RolRepository


class UsuarioService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _map_to_read(self, usuario: Usuario) -> UsuarioRead:
        roles = [ur.rol_codigo for ur in usuario.usuarios_roles]
        return UsuarioRead(
            id=usuario.id,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            celular=usuario.celular,
            activo=usuario.activo,
            roles=roles,
            created_at=usuario.created_at,
        )

    def _get_active_usuario(self, repo: UsuarioRepository, id: int) -> Usuario:
        usuario = repo.get_by_id(id)
        if not usuario or usuario.deleted_at is not None:
            raise http_error(404, "Usuario no encontrado", NOT_FOUND)
        return usuario

    def list_usuarios(self, page: int, size: int) -> PaginatedUsuarios:
        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            skip = (page - 1) * size
            usuarios = repo.list_activos(skip=skip, limit=size)
            total = repo.count_activos()
            pages = math.ceil(total / size) if size > 0 else 0

            return PaginatedUsuarios(
                items=[self._map_to_read(u) for u in usuarios],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_usuario(self, id: int) -> UsuarioRead:
        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            usuario = self._get_active_usuario(repo, id)
            return self._map_to_read(usuario)

    def update_usuario(
        self, id: int, data: UsuarioUpdate, current_user_id: int
    ) -> UsuarioRead:
        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            usuario = self._get_active_usuario(repo, id)

            if (
                id == current_user_id
                and data.activo is not None
                and data.activo != usuario.activo
            ):
                raise http_error(
                    400, "No puedes modificar tu propio estado activo", FORBIDDEN
                )

            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                usuario = repo.update(usuario, update_data)

            return self._map_to_read(usuario)

    def delete_usuario(self, id: int, current_user_id: int) -> None:
        if id == current_user_id:
            raise http_error(400, "No puedes eliminarte a ti mismo", FORBIDDEN)

        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            usuario = self._get_active_usuario(repo, id)
            repo.soft_delete(usuario)

    def asignar_rol(
        self, usuario_id: int, data: AsignarRolRequest, asignado_por_id: int
    ) -> UsuarioRead:
        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            rol_repo = RolRepository(self.uow.session)

            usuario = self._get_active_usuario(repo, usuario_id)

            rol = rol_repo.get_by_codigo(data.rol_codigo)
            if not rol:
                raise http_error(404, "Rol no encontrado", NOT_FOUND)

            roles_actuales = [ur.rol_codigo for ur in usuario.usuarios_roles]
            if data.rol_codigo in roles_actuales:
                raise http_error(
                    409, "El usuario ya tiene asignado este rol", ALREADY_EXISTS
                )

            nuevo_rol = UsuarioRol(
                usuario_id=usuario.id,
                rol_codigo=data.rol_codigo,
                asignado_por_id=asignado_por_id,
            )
            self.uow.session.add(nuevo_rol)
            self.uow.session.flush()
            self.uow.session.refresh(usuario)

            return self._map_to_read(usuario)

    def revocar_rol(
        self, usuario_id: int, rol_codigo: str, current_user_id: int
    ) -> UsuarioRead:
        if usuario_id == current_user_id:
            raise http_error(400, "No puedes revocar tus propios roles", FORBIDDEN)

        with self.uow:
            repo = UsuarioRepository(self.uow.session)
            usuario = self._get_active_usuario(repo, usuario_id)

            if len(usuario.usuarios_roles) <= 1:
                raise http_error(
                    400, "El usuario debe tener al menos un rol", FORBIDDEN
                )

            rol_a_eliminar = next(
                (ur for ur in usuario.usuarios_roles if ur.rol_codigo == rol_codigo),
                None,
            )
            if not rol_a_eliminar:
                raise http_error(
                    404, "El usuario no tiene este rol asignado", NOT_FOUND
                )

            self.uow.session.delete(rol_a_eliminar)
            self.uow.session.flush()
            self.uow.session.refresh(usuario)

            return self._map_to_read(usuario)
