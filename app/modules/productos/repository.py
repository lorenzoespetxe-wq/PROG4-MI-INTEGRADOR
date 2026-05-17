# app/modules/productos/repository.py
from sqlmodel import Session, select, func, or_
from sqlalchemy import and_

from app.core.repository import BaseRepository
from app.modules.productos.model import Producto, ProductoCategoria, ProductoIngrediente
from app.modules.categorias.model import Categoria


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session):
        super().__init__(Producto, session)

    def get_by_nombre(self, nombre: str) -> Producto | None:
        statement = (
            select(Producto)
            .where(Producto.nombre == nombre)
            .where(Producto.deleted_at.is_(None))
        )
        return self.session.exec(statement).first()

    def list_with_filters(
        self,
        search: str | None,
        categoria_id: int | None,
        disponible: bool | None,
        skip: int,
        limit: int,
    ) -> list[Producto]:
        statement = select(Producto).where(Producto.deleted_at.is_(None))

        if search:
            statement = statement.where(Producto.nombre.ilike(f"%{search}%"))

        if disponible is not None:
            statement = statement.where(Producto.disponible == disponible)

        if categoria_id is not None:
            statement = statement.join(
                ProductoCategoria,
                ProductoCategoria.producto_id == Producto.id,
            ).where(ProductoCategoria.categoria_id == categoria_id)

        statement = statement.offset(skip).limit(limit).order_by(Producto.nombre)
        return list(self.session.exec(statement).all())

    def count_with_filters(
        self,
        search: str | None,
        categoria_id: int | None,
        disponible: bool | None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Producto)
            .where(Producto.deleted_at.is_(None))
        )

        if search:
            statement = statement.where(Producto.nombre.ilike(f"%{search}%"))

        if disponible is not None:
            statement = statement.where(Producto.disponible == disponible)

        if categoria_id is not None:
            statement = statement.join(
                ProductoCategoria,
                ProductoCategoria.producto_id == Producto.id,
            ).where(ProductoCategoria.categoria_id == categoria_id)

        return self.session.exec(statement).one()

    def get_with_relations(self, id: int) -> Producto | None:
        """
        Carga el producto con sus relaciones.
        SQLModel/SQLAlchemy lazy-loada por defecto;
        acceder a las relaciones dentro de la sesión activa es suficiente.
        """
        statement = (
            select(Producto)
            .where(Producto.id == id)
            .where(Producto.deleted_at.is_(None))
        )
        producto = self.session.exec(statement).first()
        if producto:
            # Forzar carga de relaciones mientras la sesión está activa
            _ = producto.producto_categorias
            _ = producto.producto_ingredientes
            _ = producto.unidad_venta
        return producto

    def update_stock_absoluto(self, id: int, cantidad: int) -> Producto:
        producto = self.session.get(Producto, id)
        producto.stock_cantidad = cantidad
        self.session.add(producto)
        self.session.flush()
        self.session.refresh(producto)
        return producto


class ProductoCategoriaRepository(BaseRepository[ProductoCategoria]):
    def __init__(self, session: Session):
        super().__init__(ProductoCategoria, session)

    def delete_por_producto(self, producto_id: int) -> None:
        statement = select(ProductoCategoria).where(
            ProductoCategoria.producto_id == producto_id
        )
        rows = list(self.session.exec(statement).all())
        for row in rows:
            self.session.delete(row)
        self.session.flush()


class ProductoIngredienteRepository(BaseRepository[ProductoIngrediente]):
    def __init__(self, session: Session):
        super().__init__(ProductoIngrediente, session)

    def get_por_producto_e_ingrediente(
        self, producto_id: int, ingrediente_id: int
    ) -> ProductoIngrediente | None:
        statement = select(ProductoIngrediente).where(
            and_(
                ProductoIngrediente.producto_id == producto_id,
                ProductoIngrediente.ingrediente_id == ingrediente_id,
            )
        )
        return self.session.exec(statement).first()

    def delete_por_producto(self, producto_id: int) -> None:
        statement = select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id
        )
        rows = list(self.session.exec(statement).all())
        for row in rows:
            self.session.delete(row)
        self.session.flush()
