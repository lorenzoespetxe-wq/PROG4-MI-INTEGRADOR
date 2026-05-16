from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, Boolean


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
