# app/modules/unidades/repository.py
from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.modules.unidades.model import UnidadMedida


class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
    def __init__(self, session: Session):
        super().__init__(UnidadMedida, session)

    def get_by_nombre(self, nombre: str) -> UnidadMedida | None:
        statement = select(UnidadMedida).where(UnidadMedida.nombre == nombre)
        return self.session.exec(statement).first()

    def get_by_simbolo(self, simbolo: str) -> UnidadMedida | None:
        statement = select(UnidadMedida).where(UnidadMedida.simbolo == simbolo)
        return self.session.exec(statement).first()

    def get_todas(self, skip: int = 0, limit: int = 100) -> list[UnidadMedida]:
        statement = select(UnidadMedida).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
