from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, String, Text, DateTime, func


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
