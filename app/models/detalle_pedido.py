from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    String,
    DECIMAL,
    Integer,
    SmallInteger,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from typing import Optional


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
