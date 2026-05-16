from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, Text, DECIMAL
from app.models.base import TimestampMixin, SoftDeleteMixin


class DireccionEntrega(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "direccion_entrega"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    )
    alias: str | None = Field(default=None, max_length=50)
    linea1: str = Field(sa_column=Column(Text, nullable=False))
    linea2: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    ciudad: str | None = Field(default=None, max_length=100)
    provincia: str | None = Field(default=None, max_length=100)
    codigo_postal: str | None = Field(default=None, max_length=10)
    latitud: float | None = Field(
        default=None, sa_column=Column(DECIMAL(9, 6), nullable=True)
    )
    longitud: float | None = Field(
        default=None, sa_column=Column(DECIMAL(9, 6), nullable=True)
    )
    es_principal: bool = Field(default=False, nullable=False)

    usuario: "Usuario" = Relationship(back_populates="direcciones")
