from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, String, DECIMAL
from app.core.base_model import TimestampMixin


class Pago(TimestampMixin, SQLModel, table=True):
    __tablename__ = "pago"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    pedido_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("pedido.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        )
    )
    mp_payment_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, unique=True, nullable=True)
    )
    payment_method_id: str | None = Field(default=None, max_length=50)
    mp_status: str = Field(
        default="pending",
        sa_column=Column(String(30), nullable=False, server_default="'pending'"),
    )
    mp_status_detail: str | None = Field(default=None, max_length=100)
    monto: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    external_reference: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False)
    )
    idempotency_key: str = Field(
        sa_column=Column(String(100), unique=True, nullable=False)
    )

    # Relación
    pedido: "Pedido" = Relationship(back_populates="pago")
