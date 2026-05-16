from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, Boolean, DECIMAL


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
