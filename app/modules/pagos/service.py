# app/modules/pagos/service.py
from uuid import uuid4

from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND, FORBIDDEN, INVALID_TRANSITION
from app.modules.pagos.model import Pago
from app.modules.pagos.schemas import CrearPagoRequest, PagoRead
from app.modules.pagos.repository import PagoRepository
from app.modules.pagos import mp_client
from app.modules.pedidos.model import Pedido, HistorialEstadoPedido


class PagoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _map_to_read(self, pago: Pago) -> PagoRead:
        return PagoRead(
            id=pago.id,
            pedido_id=pago.pedido_id,
            mp_payment_id=pago.mp_payment_id,
            payment_method_id=pago.payment_method_id,
            mp_status=pago.mp_status,
            mp_status_detail=pago.mp_status_detail,
            monto=float(pago.monto),
            created_at=pago.created_at,
        )

    def _get_pedido(self, pedido_id: int) -> Pedido:
        pedido = self.uow.session.get(Pedido, pedido_id)
        if not pedido or pedido.deleted_at is not None:
            raise http_error(404, "Pedido no encontrado", NOT_FOUND)
        return pedido

    def _confirmar_pedido(self, pedido_id: int, usuario_id: int) -> None:
        """
        Avanza el pedido a CONFIRMADO directamente, sin abrir un UoW nuevo.
        Solo se llama desde dentro de un bloque with self.uow: ya activo.
        """
        pedido = self._get_pedido(pedido_id)
        if pedido.estado_codigo != "PENDIENTE":
            return  # ya fue avanzado por otra vía, no hacer nada

        pedido.estado_codigo = "CONFIRMADO"
        self.uow.session.add(pedido)
        self.uow.session.add(
            HistorialEstadoPedido(
                pedido_id=pedido_id,
                estado_desde="PENDIENTE",
                estado_hasta="CONFIRMADO",
                usuario_id=usuario_id,
                motivo="Pago aprobado automáticamente",
            )
        )
        self.uow.session.flush()

    # ──────────────────────────────────────────────────────────────────────
    # Operaciones públicas
    # ──────────────────────────────────────────────────────────────────────

    def crear_pago(self, usuario_id: int, data: CrearPagoRequest) -> PagoRead:
        """
        Flujo:
          1. Validaciones de negocio (pedido existe, pertenece al usuario,
             está en PENDIENTE, no tiene pago aprobado previo).
          2. Llamada al SDK de MP — FUERA del UoW.
          3. Persist Pago + avance a CONFIRMADO si approved — DENTRO del UoW.
        """
        # ── Fase 1: validaciones previas ────────────────────────────────
        with self.uow:
            repo = PagoRepository(self.uow.session)

            pedido = self._get_pedido(data.pedido_id)

            if pedido.usuario_id != usuario_id:
                raise http_error(
                    403,
                    "No tienes permiso para pagar este pedido",
                    FORBIDDEN,
                )

            if pedido.estado_codigo != "PENDIENTE":
                raise http_error(
                    422,
                    "El pedido no está en estado PENDIENTE",
                    INVALID_TRANSITION,
                )

            # Idempotencia: si ya existe un pago aprobado, lo devolvemos
            pago_existente = repo.get_by_pedido_id(data.pedido_id)
            if pago_existente and pago_existente.mp_status == "approved":
                return self._map_to_read(pago_existente)

            monto = float(pedido.total)
            external_reference = f"foodstore-pedido-{pedido.id}"
            idempotency_key = str(uuid4())
            description = f"Food Store — Pedido #{pedido.id}"

        # ── Fase 2: llamada al SDK (FUERA del UoW) ──────────────────────
        resultado_mp = mp_client.crear_pago(
            token=data.token_tarjeta,
            monto=monto,
            cuotas=data.cuotas,
            external_reference=external_reference,
            idempotency_key=idempotency_key,
            description=description,
        )

        mp_status = resultado_mp.get("status", "pending")
        mp_status_detail = resultado_mp.get("status_detail")
        mp_payment_id = resultado_mp.get("id")
        payment_method_id = resultado_mp.get("payment_method_id")

        # ── Fase 3: persistencia (DENTRO de un nuevo UoW) ───────────────
        with self.uow:
            repo = PagoRepository(self.uow.session)

            nuevo_pago = Pago(
                pedido_id=data.pedido_id,
                mp_payment_id=mp_payment_id,
                payment_method_id=payment_method_id,
                mp_status=mp_status,
                mp_status_detail=mp_status_detail,
                monto=monto,
                external_reference=external_reference,
                idempotency_key=idempotency_key,
            )
            self.uow.session.add(nuevo_pago)
            self.uow.session.flush()
            self.uow.session.refresh(nuevo_pago)

            # Avanzar el pedido a CONFIRMADO directamente, sin anidar otro UoW
            if mp_status == "approved":
                self._confirmar_pedido(data.pedido_id, usuario_id)

            return self._map_to_read(nuevo_pago)

    def procesar_webhook(self, mp_payment_id: int) -> None:
        """
        Llamado por el endpoint público de webhook de MercadoPago.
        Nunca lanza excepciones hacia el cliente (siempre retorna 200).

        Flujo:
          1. Consulta estado actualizado al SDK — FUERA del UoW.
          2. Actualiza Pago y avanza pedido si corresponde — DENTRO del UoW.
        """
        # ── Fase 1: consulta al SDK (FUERA del UoW) ─────────────────────
        try:
            resultado_mp = mp_client.obtener_pago(mp_payment_id)
        except Exception:
            return

        nuevo_status = resultado_mp.get("status", "pending")
        nuevo_status_detail = resultado_mp.get("status_detail")

        # ── Fase 2: persistencia dentro del UoW ─────────────────────────
        try:
            with self.uow:
                repo = PagoRepository(self.uow.session)

                pago = repo.get_by_mp_payment_id(mp_payment_id)
                if not pago:
                    return

                pago.mp_status = nuevo_status
                pago.mp_status_detail = nuevo_status_detail
                self.uow.session.add(pago)
                self.uow.session.flush()

                # Avanzar pedido a CONFIRMADO directamente, sin anidar otro UoW
                if nuevo_status == "approved":
                    pedido = self._get_pedido(pago.pedido_id)
                    if pedido.estado_codigo == "PENDIENTE":
                        self._confirmar_pedido(pago.pedido_id, pedido.usuario_id)
        except Exception:
            return

    def get_pago_por_pedido(
        self, usuario_id: int, pedido_id: int, roles: list[str]
    ) -> PagoRead:
        with self.uow:
            repo = PagoRepository(self.uow.session)

            pago = repo.get_by_pedido_id(pedido_id)
            if not pago:
                raise http_error(404, "Pago no encontrado para este pedido", NOT_FOUND)

            es_admin = any(r in roles for r in ("ADMIN", "PEDIDOS"))
            if not es_admin:
                pedido = self._get_pedido(pedido_id)
                if pedido.usuario_id != usuario_id:
                    raise http_error(
                        404,
                        "Pago no encontrado para este pedido",
                        NOT_FOUND,
                    )

            return self._map_to_read(pago)
