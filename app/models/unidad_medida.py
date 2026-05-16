from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, String, DateTime, func


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    simbolo: str = Field(max_length=10, unique=True, nullable=False)
    tipo: str = Field(max_length=20, nullable=False)  # masa, volumen, unidad, area
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    # Relaciones
    productos: list["Producto"] = Relationship(back_populates="unidad_venta")
    producto_ingredientes: list["ProductoIngrediente"] = Relationship(
        back_populates="unidad_medida"
    )
