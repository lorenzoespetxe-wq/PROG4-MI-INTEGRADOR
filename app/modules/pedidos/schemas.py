# app/modules/pedidos/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ItemPedidoRequest(BaseModel):
    producto_id: int
    cantidad: int = Field(ge=1)
    personalizacion: list[int] | None = None  # IDs de ingredientes a remover


class CrearPedidoRequest(BaseModel):
    items: list[ItemPedidoRequest] = Field(min_length=1)
    forma_pago_codigo: str
    direccion_id: int | None = None
    notas: str | None = None


class AvanzarEstadoRequest(BaseModel):
    nuevo_estado: str
    motivo: str | None = None

    @model_validator(mode="after")
    def motivo_requerido_si_cancela(self) -> "AvanzarEstadoRequest":
        if self.nuevo_estado == "CANCELADO" and not self.motivo:
            raise ValueError(
                "El campo 'motivo' es obligatorio cuando se cancela un pedido"
            )
        return self


class DetallePedidoRead(BaseModel):
    id: int
    producto_id: int | None
    nombre_snapshot: str
    precio_snapshot: float
    cantidad: int
    subtotal_snap: float
    personalizacion: list[int] | None

    model_config = ConfigDict(from_attributes=True)


class HistorialRead(BaseModel):
    id: int
    estado_desde: str | None
    estado_hasta: str
    usuario_id: int
    motivo: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PedidoRead(BaseModel):
    id: int
    estado_codigo: str
    forma_pago_codigo: str
    total: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PedidoDetail(BaseModel):
    id: int
    estado_codigo: str
    forma_pago_codigo: str
    subtotal: float
    descuento: float
    costo_envio: float
    total: float
    notas: str | None
    items: list[DetallePedidoRead]
    historial: list[HistorialRead]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedPedidos(BaseModel):
    items: list[PedidoRead]
    total: int
    page: int
    size: int
    pages: int
