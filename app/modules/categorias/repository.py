# app/modules/categorias/repository.py
from sqlmodel import Session, select, func
from sqlalchemy.orm import aliased

from app.core.repository import BaseRepository
from app.modules.categorias.model import Categoria
from app.modules.productos.model import ProductoCategoria


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session):
        super().__init__(Categoria, session)

    def get_by_nombre(self, nombre: str) -> Categoria | None:
        statement = (
            select(Categoria)
            .where(Categoria.nombre == nombre)
            .where(Categoria.deleted_at.is_(None))
        )
        return self.session.exec(statement).first()

    def get_hijos_activos(self, parent_id: int) -> list[Categoria]:
        statement = (
            select(Categoria)
            .where(Categoria.parent_id == parent_id)
            .where(Categoria.deleted_at.is_(None))
        )
        return list(self.session.exec(statement).all())

    def tiene_productos_asociados(self, categoria_id: int) -> bool:
        statement = (
            select(func.count())
            .select_from(ProductoCategoria)
            .where(ProductoCategoria.categoria_id == categoria_id)
        )
        count = self.session.exec(statement).one()
        return count > 0

    def es_ancestro(self, posible_ancestro_id: int, nodo_id: int) -> bool:
        if posible_ancestro_id == nodo_id:
            return True

        # CTE Recursiva: partimos del nodo_id y subimos por parent_id
        hierarchy = (
            select(Categoria.id, Categoria.parent_id)
            .where(Categoria.id == nodo_id)
            .cte(name="hierarchy", recursive=True)
        )

        parent_alias = aliased(Categoria)
        hierarchy = hierarchy.union_all(
            select(parent_alias.id, parent_alias.parent_id).where(
                parent_alias.id == hierarchy.c.parent_id
            )
        )

        statement = select(hierarchy.c.id).where(hierarchy.c.id == posible_ancestro_id)
        result = self.session.exec(statement).first()

        return result is not None

    def get_todos_activos(self) -> list[Categoria]:
        statement = select(Categoria).where(Categoria.deleted_at.is_(None))
        return list(self.session.exec(statement).all())
