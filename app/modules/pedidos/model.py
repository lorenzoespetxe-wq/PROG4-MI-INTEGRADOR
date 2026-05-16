from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    DECIMAL,
    Text,
    String,
    CheckConstraint,
    DateTime,
    func,
    Integer,
    SmallInteger,
)
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.base_model import TimestampMixin, SoftDeleteMixin


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"

    codigo: str = Field(max_length=20, primary_key=True)
    descripcion: str = Field(sa_column=Column(Text))
    orden: int = Field(nullable=False)
    es_terminal: bool = Field(nullable=False)


class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago"

    codigo: str = Field(max_length=20, primary_key=True)
    descripcion: str = Field(max_length=80, nullable=False)
    habilitado: bool = Field(default=True, nullable=False)


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


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"
    __table_args__ = (CheckConstraint("cantidad >= 1", name="check_cantidad_minima"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    pedido_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False
        )
    )
    producto_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("producto.id", ondelete="SET NULL"), nullable=True
        ),
    )
    nombre_snapshot: str = Field(sa_column=Column(String(200), nullable=False))
    precio_snapshot: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    subtotal_snap: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    cantidad: int = Field(sa_column=Column(SmallInteger, nullable=False))
    personalizacion: list[int] | None = Field(
        default=None, sa_column=Column(ARRAY(Integer), nullable=True)
    )

    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="detalles")
    producto: Optional["Producto"] = Relationship(back_populates="detalles_pedido")


class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    pedido_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False
        )
    )
    estado_desde: str | None = Field(
        default=None,
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=True),
    )
    estado_hasta: str = Field(
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=False)
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    )
    motivo: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="historial")
    usuario: "Usuario" = Relationship(back_populates="historiales")
