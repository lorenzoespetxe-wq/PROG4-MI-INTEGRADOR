# app/modules/admin/service.py
import math

from app.core.unit_of_work import UnitOfWork
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    DashboardMetrics,
    ProductoStockAlert,
    TopProducto,
    StockBulkUpdate,
    StockBulkResponse,
)
from app.modules.pedidos.schemas import PaginatedPedidos, PedidoRead
from app.modules.productos.model import Producto


class AdminService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ──────────────────────────────────────────────────────────────────────
    # Dashboard
    # ──────────────────────────────────────────────────────────────────────

    def get_dashboard(self, umbral_stock: int = 5) -> DashboardMetrics:
        with self.uow:
            repo = AdminRepository(self.uow.session)

            total_pedidos_hoy = repo.get_total_pedidos_hoy()
            ingresos_hoy = repo.get_ingresos_hoy()
            pedidos_por_estado = repo.get_pedidos_por_estado()

            productos_bajo_stock_raw = repo.get_productos_bajo_stock(umbral=umbral_stock)
            productos_bajo_stock = [
                ProductoStockAlert(
                    id=p.id,
                    nombre=p.nombre,
                    stock_cantidad=p.stock_cantidad,
                    disponible=p.disponible,
                )
                for p in productos_bajo_stock_raw
            ]

            top_raw = repo.get_top_productos(limit=5)
            top_productos = [
                TopProducto(
                    id=row["producto_id"],
                    nombre=row["nombre"],
                    total_vendido=row["total_vendido"],
                )
                for row in top_raw
            ]

            return DashboardMetrics(
                total_pedidos_hoy=total_pedidos_hoy,
                ingresos_hoy=ingresos_hoy,
                pedidos_por_estado=pedidos_por_estado,
                productos_bajo_stock=productos_bajo_stock,
                top_productos=top_productos,
            )

    # ──────────────────────────────────────────────────────────────────────
    # Pedidos activos (panel operativo)
    # ──────────────────────────────────────────────────────────────────────

    def get_pedidos_activos(self, page: int, size: int) -> PaginatedPedidos:
        with self.uow:
            repo = AdminRepository(self.uow.session)
            skip = (page - 1) * size

            pedidos = repo.get_pedidos_activos(skip=skip, limit=size)
            total = repo.count_pedidos_activos()
            pages = math.ceil(total / size) if size > 0 else 0

            items = [
                PedidoRead(
                    id=p.id,
                    estado_codigo=p.estado_codigo,
                    forma_pago_codigo=p.forma_pago_codigo,
                    total=float(p.total),
                    created_at=p.created_at,
                )
                for p in pedidos
            ]

            return PaginatedPedidos(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    # ──────────────────────────────────────────────────────────────────────
    # Stock bulk
    # ──────────────────────────────────────────────────────────────────────

    def actualizar_stock_bulk(self, data: StockBulkUpdate) -> StockBulkResponse:
        """
        Actualiza el stock de N productos en una única transacción.
        Los producto_id inexistentes se acumulan en errores sin abortar
        las actualizaciones válidas.
        """
        errores: list[str] = []
        updated: int = 0

        with self.uow:
            for item in data.actualizaciones:
                producto = self.uow.session.get(Producto, item.producto_id)

                if not producto or producto.deleted_at is not None:
                    errores.append(
                        f"producto_id {item.producto_id}: no encontrado o inactivo"
                    )
                    continue

                producto.stock_cantidad = item.stock_cantidad
                self.uow.session.add(producto)
                updated += 1

            # flush() al final del bloque; el commit lo hace el UoW al salir
            if updated > 0:
                self.uow.session.flush()

        return StockBulkResponse(updated=updated, errores=errores)
