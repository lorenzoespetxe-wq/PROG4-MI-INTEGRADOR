from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    Text,
    DECIMAL,
    Integer,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from app.core.base_model import TimestampMixin, SoftDeleteMixin


class Producto(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "producto"
    __table_args__ = (
        CheckConstraint("precio_base >= 0", name="check_precio_base_positivo"),
        CheckConstraint("stock_cantidad >= 0", name="check_stock_cantidad_positivo"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(max_length=150, unique=True, nullable=False)
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    precio_base: float = Field(sa_column=Column(DECIMAL(10, 2), nullable=False))
    imagenes_url: list[str] | None = Field(
        default=None, sa_column=Column(ARRAY(Text), nullable=True)
    )
    stock_cantidad: int = Field(
        default=0, sa_column=Column(Integer, nullable=False, server_default="0")
    )
    disponible: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true")
    )
    unidad_venta_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("unidad_medida.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Relaciones
    unidad_venta: Optional["UnidadMedida"] = Relationship(back_populates="productos")
    producto_categorias: list["ProductoCategoria"] = Relationship(
        back_populates="producto"
    )
    producto_ingredientes: list["ProductoIngrediente"] = Relationship(
        back_populates="producto"
    )
    detalles_pedido: list["DetallePedido"] = Relationship(back_populates="producto")


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"

    producto_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("producto.id", ondelete="CASCADE"), primary_key=True
        )
    )
    categoria_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("categoria.id", ondelete="CASCADE"), primary_key=True
        )
    )
    es_principal: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False, server_default="false")
    )

    producto: "Producto" = Relationship(back_populates="producto_categorias")


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    producto_id: int = Field(
        sa_column=Column(
            BigInteger, ForeignKey("producto.id", ondelete="CASCADE"), primary_key=True
        )
    )
    ingrediente_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("ingrediente.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    cantidad: float = Field(sa_column=Column(DECIMAL(10, 3), nullable=False))
    unidad_medida_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("unidad_medida.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    es_removible: bool = Field(sa_column=Column(Boolean, nullable=False))

    producto: "Producto" = Relationship(back_populates="producto_ingredientes")
    unidad_medida: "UnidadMedida" = Relationship(back_populates="producto_ingredientes")
