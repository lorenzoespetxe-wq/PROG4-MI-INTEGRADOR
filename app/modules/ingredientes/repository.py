# app/modules/ingredientes/repository.py
from sqlmodel import Session, select, func

from app.core.repository import BaseRepository
from app.modules.ingredientes.model import Ingrediente
from app.modules.productos.model import ProductoIngrediente


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session: Session):
        super().__init__(Ingrediente, session)

    def get_by_nombre(self, nombre: str) -> Ingrediente | None:
        statement = (
            select(Ingrediente)
            .where(Ingrediente.nombre == nombre)
            .where(Ingrediente.deleted_at.is_(None))
        )
        return self.session.exec(statement).first()

    def list_activos(
        self, skip: int = 0, limit: int = 100, solo_alergenos: bool = False
    ) -> list[Ingrediente]:
        statement = select(Ingrediente).where(Ingrediente.deleted_at.is_(None))
        if solo_alergenos:
            statement = statement.where(Ingrediente.es_alergeno == True)

        statement = statement.offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def count_activos(self, solo_alergenos: bool = False) -> int:
        statement = (
            select(func.count())
            .select_from(Ingrediente)
            .where(Ingrediente.deleted_at.is_(None))
        )
        if solo_alergenos:
            statement = statement.where(Ingrediente.es_alergeno == True)

        return self.session.exec(statement).one()

    def esta_en_uso(self, id: int) -> bool:
        statement = (
            select(func.count())
            .select_from(ProductoIngrediente)
            .where(ProductoIngrediente.ingrediente_id == id)
        )
        count = self.session.exec(statement).one()
        return count > 0
