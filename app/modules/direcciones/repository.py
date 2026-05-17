# app/modules/direcciones/repository.py
from sqlmodel import Session, select, func
from sqlalchemy import update

from app.core.repository import BaseRepository
from app.modules.direcciones.model import DireccionEntrega


class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session):
        super().__init__(DireccionEntrega, session)

    def list_por_usuario(
        self, usuario_id: int, skip: int = 0, limit: int = 100
    ) -> list[DireccionEntrega]:
        statement = (
            select(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_por_usuario_y_id(
        self, usuario_id: int, direccion_id: int
    ) -> DireccionEntrega | None:
        statement = (
            select(DireccionEntrega)
            .where(DireccionEntrega.id == direccion_id)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.deleted_at.is_(None))
        )
        return self.session.exec(statement).first()

    def count_activas(self, usuario_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.deleted_at.is_(None))
        )
        return self.session.exec(statement).one()

    def get_mas_antigua_activa(self, usuario_id: int) -> DireccionEntrega | None:
        statement = (
            select(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.deleted_at.is_(None))
            .order_by(DireccionEntrega.created_at.asc())
        )
        return self.session.exec(statement).first()

    def desmarcar_principal(self, usuario_id: int) -> None:
        statement = (
            update(DireccionEntrega)
            .where(DireccionEntrega.usuario_id == usuario_id)
            .where(DireccionEntrega.deleted_at.is_(None))
            .values(es_principal=False)
        )
        self.session.exec(statement)
        self.session.flush()
