# app/modules/admin/repository.py
"""
AdminRepository — repositorio analítico puro.
No hereda de BaseRepository porque no opera sobre una única entidad;
ejecuta queries de agregación que cruzan varias tablas.
"""
from datetime import datetime, timezone

from sqlmodel import Session, select, func
from sqlalchemy import cast, Date, and_

from app.modules.productos.model import Producto
from app.modules.pedidos.model import Pedido, DetallePedido, EstadoPedido


# Estados que generan ingresos reales
_ESTADO_ENTREGADO = "ENTREGADO"
_ESTADO_CANCELADO = "CANCELADO"


class AdminRepository:
    def __init__(self, session: Session):
        self.session = session

    # ──────────────────────────────────────────────────────────────────────
    # Métricas de pedidos
    # ──────────────────────────────────────────────────────────────────────

    def get_total_pedidos_hoy(self) -> int:
        hoy = datetime.now(timezone.utc).date()
        statement = (
            select(func.count())
            .select_from(Pedido)
            .where(Pedido.deleted_at.is_(None))
            .where(cast(Pedido.created_at, Date) == hoy)
        )
        return self.session.exec(statement).one() or 0

    def get_ingresos_hoy(self) -> float:
        """Suma el total de pedidos ENTREGADOS creados hoy."""
        hoy = datetime.now(timezone.utc).date()
        statement = (
            select(func.coalesce(func.sum(Pedido.total), 0))
            .select_from(Pedido)
            .where(Pedido.deleted_at.is_(None))
            .where(Pedido.estado_codigo == _ESTADO_ENTREGADO)
            .where(cast(Pedido.created_at, Date) == hoy)
        )
        result = self.session.exec(statement).one()
        return float(result or 0)

    def get_pedidos_por_estado(self) -> dict[str, int]:
        """
        Retorna un dict con todos los estados conocidos, incluyendo
        aquellos sin pedidos (valor 0), para que el dashboard siempre
        muestre el cuadro completo.
        """
        # Obtener todos los estados posibles de la tabla de referencia
        todos_los_estados = list(
            self.session.exec(select(EstadoPedido.codigo)).all()
        )

        # Contar pedidos activos (no soft-deleted) agrupados por estado
        statement = (
            select(Pedido.estado_codigo, func.count().label("total"))
            .where(Pedido.deleted_at.is_(None))
            .group_by(Pedido.estado_codigo)
        )
        conteos_raw = {row[0]: row[1] for row in self.session.exec(statement).all()}

        # Garantizar que todos los estados aparecen, incluso con 0
        return {estado: conteos_raw.get(estado, 0) for estado in todos_los_estados}

    # ──────────────────────────────────────────────────────────────────────
    # Métricas de productos
    # ──────────────────────────────────────────────────────────────────────

    def get_productos_bajo_stock(self, umbral: int = 5) -> list[Producto]:
        statement = (
            select(Producto)
            .where(Producto.deleted_at.is_(None))
            .where(Producto.stock_cantidad <= umbral)
            .order_by(Producto.stock_cantidad.asc())
        )
        return list(self.session.exec(statement).all())

    def get_top_productos(self, limit: int = 5) -> list[dict]:
        """
        Top N productos por cantidad total vendida, excluyendo pedidos CANCELADOS.
        Retorna lista de dicts con claves: producto_id, nombre, total_vendido.
        """
        statement = (
            select(
                DetallePedido.producto_id,
                Producto.nombre,
                func.sum(DetallePedido.cantidad).label("total_vendido"),
            )
            .join(Pedido, DetallePedido.pedido_id == Pedido.id)
            .join(Producto, DetallePedido.producto_id == Producto.id)
            .where(Pedido.deleted_at.is_(None))
            .where(Pedido.estado_codigo != _ESTADO_CANCELADO)
            .where(DetallePedido.producto_id.is_not(None))
            .group_by(DetallePedido.producto_id, Producto.nombre)
            .order_by(func.sum(DetallePedido.cantidad).desc())
            .limit(limit)
        )
        rows = self.session.exec(statement).all()
        return [
            {
                "producto_id": row[0],
                "nombre": row[1],
                "total_vendido": int(row[2]),
            }
            for row in rows
        ]

    # ──────────────────────────────────────────────────────────────────────
    # Pedidos activos (para panel operativo)
    # ──────────────────────────────────────────────────────────────────────

    def get_pedidos_activos(self, skip: int = 0, limit: int = 20) -> list[Pedido]:
        """Pedidos que no están en estados terminales ni soft-deleted."""
        statement = (
            select(Pedido)
            .where(Pedido.deleted_at.is_(None))
            .where(Pedido.estado_codigo.not_in([_ESTADO_ENTREGADO, _ESTADO_CANCELADO]))
            .order_by(Pedido.created_at.asc())   # los más antiguos primero
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count_pedidos_activos(self) -> int:
        statement = (
            select(func.count())
            .select_from(Pedido)
            .where(Pedido.deleted_at.is_(None))
            .where(Pedido.estado_codigo.not_in([_ESTADO_ENTREGADO, _ESTADO_CANCELADO]))
        )
        return self.session.exec(statement).one() or 0
