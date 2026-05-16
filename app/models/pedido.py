from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    DECIMAL,
    Text,
    String,
    CheckConstraint,
)
from app.models.base import TimestampMixin, SoftDeleteMixin


class Pedido(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "pedido"
    __table_args__ = (CheckConstraint("total >= 0", name="check_total_positivo"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    )
    estado_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=False)
    )
    forma_pago_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("forma_pago.codigo"), nullable=False)
    )
    direccion_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("direccion_entrega.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    subtotal: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    descuento: float = Field(
        default=0.0,
        sa_column=Column(DECIMAL(10, 2), nullable=False, server_default="0.00"),
    )
    costo_envio: float = Field(
        default=50.00,
        sa_column=Column(DECIMAL(10, 2), nullable=False, server_default="50.00"),
    )
    total: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    notas: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Relaciones
    usuario: "Usuario" = Relationship(back_populates="pedidos")
    detalles: list["DetallePedido"] = Relationship(back_populates="pedido")
    historial: list["HistorialEstadoPedido"] = Relationship(back_populates="pedido")
    pago: "Pago" = Relationship(back_populates="pedido")
