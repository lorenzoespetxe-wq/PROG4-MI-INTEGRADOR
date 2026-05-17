# app/modules/pagos/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CrearPagoRequest(BaseModel):
    pedido_id: int
    token_tarjeta: str
    cuotas: int = Field(default=1, ge=1)


class PagoRead(BaseModel):
    id: int
    pedido_id: int
    mp_payment_id: int | None
    payment_method_id: str | None
    mp_status: str
    mp_status_detail: str | None
    monto: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
