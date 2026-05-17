# app/modules/pedidos/service.py
import math
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import (
    http_error,
    NOT_FOUND,
    FORBIDDEN,
    INSUFFICIENT_STOCK,
    INVALID_TRANSITION,
)
from app.modules.pedidos.model import Pedido, DetallePedido, HistorialEstadoPedido
from app.modules.pedidos.schemas import (
    CrearPedidoRequest,
    AvanzarEstadoRequest,
    DetallePedidoRead,
    HistorialRead,
    PedidoRead,
    PedidoDetail,
    PaginatedPedidos,
)
from app.modules.pedidos.repositories import (
    PedidoRepository,
    DetallePedidoRepository,
    HistorialRepository,
    FormaPagoRepository,
)
from app.modules.pedidos import fsm
from app.modules.productos.model import Producto
from app.modules.direcciones.model import DireccionEntrega


COSTO_ENVIO_FIJO = 50.00


class PedidoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ──────────────────────────────────────────────────────────────────────
    # Helpers de mapeo
    # ──────────────────────────────────────────────────────────────────────

    def _map_to_read(self, pedido: Pedido) -> PedidoRead:
        return PedidoRead(
            id=pedido.id,
            estado_codigo=pedido.estado_codigo,
            forma_pago_codigo=pedido.forma_pago_codigo,
            total=float(pedido.total),
            created_at=pedido.created_at,
        )

    def _map_to_detail(self, pedido: Pedido) -> PedidoDetail:
        items = [
            DetallePedidoRead(
                id=d.id,
                producto_id=d.producto_id,
                nombre_snapshot=d.nombre_snapshot,
                precio_snapshot=float(d.precio_snapshot),
                cantidad=d.cantidad,
                subtotal_snap=float(d.subtotal_snap),
                personalizacion=d.personalizacion,
            )
            for d in pedido.detalles
        ]

        historial = [
            HistorialRead(
                id=h.id,
                estado_desde=h.estado_desde,
                estado_hasta=h.estado_hasta,
                usuario_id=h.usuario_id,
                motivo=h.motivo,
                created_at=h.created_at,
            )
            for h in sorted(pedido.historial, key=lambda h: h.created_at)
        ]

        return PedidoDetail(
            id=pedido.id,
            estado_codigo=pedido.estado_codigo,
            forma_pago_codigo=pedido.forma_pago_codigo,
            subtotal=float(pedido.subtotal),
            descuento=float(pedido.descuento),
            costo_envio=float(pedido.costo_envio),
            total=float(pedido.total),
            notas=pedido.notas,
            items=items,
            historial=historial,
            created_at=pedido.created_at,
        )

    def _get_pedido_visible(
        self, repo: PedidoRepository, pedido_id: int, usuario_id: int, roles: list[str]
    ) -> Pedido:
        """
        Carga el pedido con sus relaciones.
        Los CLIENTs solo pueden ver sus propios pedidos (devuelve 404 para
        no revelar la existencia del pedido ajeno).
        ADMIN / PEDIDOS pueden ver cualquiera.
        """
        pedido = repo.get_with_relations(pedido_id)
        if not pedido:
            raise http_error(404, "Pedido no encontrado", NOT_FOUND)

        es_admin_o_pedidos = any(r in roles for r in ("ADMIN", "PEDIDOS"))
        if not es_admin_o_pedidos and pedido.usuario_id != usuario_id:
            raise http_error(404, "Pedido no encontrado", NOT_FOUND)

        return pedido

    # ──────────────────────────────────────────────────────────────────────
    # Operaciones públicas
    # ──────────────────────────────────────────────────────────────────────

    def crear_pedido(self, usuario_id: int, data: CrearPedidoRequest) -> PedidoDetail:
        with self.uow:
            forma_pago_repo = FormaPagoRepository(self.uow.session)
            detalle_repo = DetallePedidoRepository(self.uow.session)
            historial_repo = HistorialRepository(self.uow.session)

            # Validar forma de pago
            forma_pago = forma_pago_repo.get_by_codigo(data.forma_pago_codigo)
            if not forma_pago:
                raise http_error(
                    404,
                    f"Forma de pago '{data.forma_pago_codigo}' no encontrada",
                    NOT_FOUND,
                )
            if not forma_pago.habilitado:
                raise http_error(
                    422,
                    f"La forma de pago '{data.forma_pago_codigo}' no está habilitada",
                    INVALID_TRANSITION,
                )

            # Validar dirección (si se provee) pertenece al usuario
            if data.direccion_id is not None:
                direccion = self.uow.session.get(DireccionEntrega, data.direccion_id)
                if (
                    not direccion
                    or direccion.deleted_at is not None
                    or direccion.usuario_id != usuario_id
                ):
                    raise http_error(
                        404,
                        "Dirección de entrega no encontrada",
                        NOT_FOUND,
                    )

            # Validar productos: disponibilidad y stock.
            # Acumulamos todos los errores antes de fallar.
            errores_stock: list[str] = []
            productos_cache: dict[int, Producto] = {}

            for item in data.items:
                producto = self.uow.session.get(Producto, item.producto_id)
                if not producto or producto.deleted_at is not None:
                    errores_stock.append(
                        f"Producto {item.producto_id}: no encontrado o inactivo"
                    )
                    continue
                if not producto.disponible:
                    errores_stock.append(f"Producto '{producto.nombre}': no disponible")
                    continue
                if producto.stock_cantidad < item.cantidad:
                    errores_stock.append(
                        f"Producto '{producto.nombre}': stock insuficiente "
                        f"(solicitado: {item.cantidad}, disponible: {producto.stock_cantidad})"
                    )
                    continue
                productos_cache[item.producto_id] = producto

            if errores_stock:
                raise http_error(
                    422,
                    "; ".join(errores_stock),
                    INSUFFICIENT_STOCK,
                )

            # Calcular totales
            subtotal = sum(
                float(productos_cache[item.producto_id].precio_base) * item.cantidad
                for item in data.items
            )
            descuento = 0.0
            costo_envio = COSTO_ENVIO_FIJO
            total = subtotal + costo_envio - descuento

            # Insertar Pedido
            nuevo_pedido = Pedido(
                usuario_id=usuario_id,
                estado_codigo="PENDIENTE",
                forma_pago_codigo=data.forma_pago_codigo,
                direccion_id=data.direccion_id,
                subtotal=subtotal,
                descuento=descuento,
                costo_envio=costo_envio,
                total=total,
                notas=data.notas,
            )
            self.uow.session.add(nuevo_pedido)
            self.uow.session.flush()
            self.uow.session.refresh(nuevo_pedido)

            # Insertar detalles en bulk
            detalles = [
                DetallePedido(
                    pedido_id=nuevo_pedido.id,
                    producto_id=item.producto_id,
                    nombre_snapshot=productos_cache[item.producto_id].nombre,
                    precio_snapshot=float(
                        productos_cache[item.producto_id].precio_base
                    ),
                    cantidad=item.cantidad,
                    subtotal_snap=float(productos_cache[item.producto_id].precio_base)
                    * item.cantidad,
                    personalizacion=item.personalizacion,
                )
                for item in data.items
            ]
            detalle_repo.create_bulk(detalles)

            # Insertar entrada inicial en el historial
            historial_repo.append(
                HistorialEstadoPedido(
                    pedido_id=nuevo_pedido.id,
                    estado_desde=None,
                    estado_hasta="PENDIENTE",
                    usuario_id=usuario_id,
                    motivo=None,
                )
            )

            # Descontar stock de cada producto
            for item in data.items:
                prod = productos_cache[item.producto_id]
                prod.stock_cantidad -= item.cantidad
                self.uow.session.add(prod)
            self.uow.session.flush()

            # Recargar relaciones para el mapeo final
            self.uow.session.refresh(nuevo_pedido)
            _ = nuevo_pedido.detalles
            _ = nuevo_pedido.historial

            return self._map_to_detail(nuevo_pedido)

    def listar(
        self,
        usuario_id: int,
        roles: list[str],
        page: int,
        size: int,
        estado: str | None = None,
    ) -> PaginatedPedidos:
        with self.uow:
            repo = PedidoRepository(self.uow.session)
            skip = (page - 1) * size

            es_admin_o_pedidos = any(r in roles for r in ("ADMIN", "PEDIDOS"))

            if es_admin_o_pedidos:
                items = repo.list_todos(skip=skip, limit=size, estado=estado)
                total = repo.count_todos(estado=estado)
            else:
                items = repo.list_por_usuario(
                    usuario_id=usuario_id, skip=skip, limit=size
                )
                total = repo.count_por_usuario(usuario_id=usuario_id)

            pages = math.ceil(total / size) if size > 0 else 0

            return PaginatedPedidos(
                items=[self._map_to_read(p) for p in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_detalle(
        self, usuario_id: int, pedido_id: int, roles: list[str]
    ) -> PedidoDetail:
        with self.uow:
            repo = PedidoRepository(self.uow.session)
            pedido = self._get_pedido_visible(repo, pedido_id, usuario_id, roles)
            return self._map_to_detail(pedido)

    def avanzar_estado(
        self,
        usuario_id: int,
        pedido_id: int,
        data: AvanzarEstadoRequest,
        roles: list[str],
    ) -> PedidoDetail:
        with self.uow:
            repo = PedidoRepository(self.uow.session)
            historial_repo = HistorialRepository(self.uow.session)

            pedido = repo.get_with_relations(pedido_id)
            if not pedido:
                raise http_error(404, "Pedido no encontrado", NOT_FOUND)

            # Validar FSM antes de chequear permisos para dar el error más informativo
            fsm.validar_transicion(pedido.estado_codigo, data.nuevo_estado)

            # Lógica de permisos por rol
            es_admin_o_pedidos = any(r in roles for r in ("ADMIN", "PEDIDOS"))
            es_cliente = "CLIENT" in roles

            if not es_admin_o_pedidos:
                # CLIENT solo puede cancelar sus propios pedidos en PENDIENTE
                if not es_cliente:
                    raise http_error(403, "Permisos insuficientes", FORBIDDEN)
                if pedido.usuario_id != usuario_id:
                    raise http_error(404, "Pedido no encontrado", NOT_FOUND)
                if data.nuevo_estado != "CANCELADO":
                    raise http_error(
                        403,
                        "Los clientes solo pueden cancelar sus pedidos",
                        FORBIDDEN,
                    )
                if pedido.estado_codigo != "PENDIENTE":
                    raise http_error(
                        403,
                        "Solo se pueden cancelar pedidos en estado PENDIENTE",
                        FORBIDDEN,
                    )

            estado_anterior = pedido.estado_codigo

            # Append al historial (append-only)
            historial_repo.append(
                HistorialEstadoPedido(
                    pedido_id=pedido.id,
                    estado_desde=estado_anterior,
                    estado_hasta=data.nuevo_estado,
                    usuario_id=usuario_id,
                    motivo=data.motivo,
                )
            )

            # Avanzar estado del pedido
            pedido.estado_codigo = data.nuevo_estado
            self.uow.session.add(pedido)
            self.uow.session.flush()

            # Restaurar stock si se cancela desde un estado con stock descontado
            if (
                data.nuevo_estado == "CANCELADO"
                and estado_anterior in fsm.ESTADOS_CON_STOCK_DESCONTADO
            ):
                for detalle in pedido.detalles:
                    if detalle.producto_id is not None:
                        producto = self.uow.session.get(Producto, detalle.producto_id)
                        if producto:
                            producto.stock_cantidad += detalle.cantidad
                            self.uow.session.add(producto)
                self.uow.session.flush()

            self.uow.session.refresh(pedido)
            _ = pedido.detalles
            _ = pedido.historial

            return self._map_to_detail(pedido)

    def get_historial(
        self, usuario_id: int, pedido_id: int, roles: list[str]
    ) -> list[HistorialRead]:
        with self.uow:
            repo = PedidoRepository(self.uow.session)
            historial_repo = HistorialRepository(self.uow.session)

            # Valida visibilidad antes de devolver el historial
            self._get_pedido_visible(repo, pedido_id, usuario_id, roles)

            entradas = historial_repo.list_por_pedido_asc(pedido_id)
            return [
                HistorialRead(
                    id=h.id,
                    estado_desde=h.estado_desde,
                    estado_hasta=h.estado_hasta,
                    usuario_id=h.usuario_id,
                    motivo=h.motivo,
                    created_at=h.created_at,
                )
                for h in entradas
            ]
