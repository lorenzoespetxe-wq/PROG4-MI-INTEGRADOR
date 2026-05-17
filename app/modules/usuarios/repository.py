# app/modules/usuarios/repository.py
from sqlmodel import Session, select, func

from app.core.repository import BaseRepository
from app.modules.usuarios.model import Usuario, Rol, UsuarioRol


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(Usuario, session)

    def get_by_email(self, email: str) -> Usuario | None:
        statement = select(Usuario).where(Usuario.email == email)
        return self.session.exec(statement).first()

    def list_activos(self, skip: int = 0, limit: int = 100) -> list[Usuario]:
        statement = (
            select(Usuario)
            .where(Usuario.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count_activos(self) -> int:
        statement = (
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.deleted_at.is_(None))
        )
        return self.session.exec(statement).one()

    def get_roles(self, usuario_id: int) -> list[str]:
        statement = select(UsuarioRol.rol_codigo).where(
            UsuarioRol.usuario_id == usuario_id
        )
        return list(self.session.exec(statement).all())


class RolRepository(BaseRepository[Rol]):
    def __init__(self, session: Session):
        super().__init__(Rol, session)

    def get_by_codigo(self, codigo: str) -> Rol | None:
        statement = select(Rol).where(Rol.codigo == codigo)
        return self.session.exec(statement).first()
