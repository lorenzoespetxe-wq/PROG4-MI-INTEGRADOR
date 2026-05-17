# app/modules/pagos/repository.py
from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.modules.pagos.model import Pago


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, session: Session):
        super().__init__(Pago, session)

    def get_by_pedido_id(self, pedido_id: int) -> Pago | None:
        statement = select(Pago).where(Pago.pedido_id == pedido_id)
        return self.session.exec(statement).first()

    def get_by_mp_payment_id(self, mp_id: int) -> Pago | None:
        statement = select(Pago).where(Pago.mp_payment_id == mp_id)
        return self.session.exec(statement).first()

    def get_by_external_reference(self, ref: str) -> Pago | None:
        statement = select(Pago).where(Pago.external_reference == ref)
        return self.session.exec(statement).first()
