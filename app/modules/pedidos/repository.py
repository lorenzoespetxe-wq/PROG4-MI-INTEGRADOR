# app/modules/pedidos/repositories.py
from sqlmodel import Session, select, func

from app.core.repository import BaseRepository
from app.modules.pedidos.model import (
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
    FormaPago,
)


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session):
        super().__init__(Pedido, session)

    def list_por_usuario(
        self, usuario_id: int, skip: int = 0, limit: int = 20
    ) -> list[Pedido]:
        statement = (
            select(Pedido)
            .where(Pedido.usuario_id == usuario_id)
            .where(Pedido.deleted_at.is_(None))
            .order_by(Pedido.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def list_todos(
        self,
        skip: int = 0,
        limit: int = 20,
        estado: str | None = None,
    ) -> list[Pedido]:
        statement = (
            select(Pedido)
            .where(Pedido.deleted_at.is_(None))
            .order_by(Pedido.created_at.desc())
        )
        if estado is not None:
            statement = statement.where(Pedido.estado_codigo == estado)
        statement = statement.offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def count_por_usuario(self, usuario_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Pedido)
            .where(Pedido.usuario_id == usuario_id)
            .where(Pedido.deleted_at.is_(None))
        )
        return self.session.exec(statement).one()

    def count_todos(self, estado: str | None = None) -> int:
        statement = (
            select(func.count()).select_from(Pedido).where(Pedido.deleted_at.is_(None))
        )
        if estado is not None:
            statement = statement.where(Pedido.estado_codigo == estado)
        return self.session.exec(statement).one()

    def get_with_relations(self, pedido_id: int) -> Pedido | None:
        """
        Carga el pedido y fuerza el acceso a sus relaciones dentro de la sesión
        para que los datos estén disponibles después del cierre del contexto.
        """
        statement = (
            select(Pedido)
            .where(Pedido.id == pedido_id)
            .where(Pedido.deleted_at.is_(None))
        )
        pedido = self.session.exec(statement).first()
        if pedido:
            _ = pedido.detalles
            _ = pedido.historial
        return pedido


class DetallePedidoRepository(BaseRepository[DetallePedido]):
    def __init__(self, session: Session):
        super().__init__(DetallePedido, session)

    def create_bulk(self, detalles: list[DetallePedido]) -> None:
        """Inserta todos los detalles en una sola operación y hace flush."""
        self.session.add_all(detalles)
        self.session.flush()


class HistorialRepository(BaseRepository[HistorialEstadoPedido]):
    def __init__(self, session: Session):
        super().__init__(HistorialEstadoPedido, session)

    def list_por_pedido_asc(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        statement = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at.asc())
        )
        return list(self.session.exec(statement).all())

    def append(self, entrada: HistorialEstadoPedido) -> HistorialEstadoPedido:
        """Append-only: nunca actualiza ni elimina entradas de historial."""
        self.session.add(entrada)
        self.session.flush()
        self.session.refresh(entrada)
        return entrada


class FormaPagoRepository(BaseRepository[FormaPago]):
    def __init__(self, session: Session):
        super().__init__(FormaPago, session)

    def get_by_codigo(self, codigo: str) -> FormaPago | None:
        statement = select(FormaPago).where(FormaPago.codigo == codigo)
        return self.session.exec(statement).first()
