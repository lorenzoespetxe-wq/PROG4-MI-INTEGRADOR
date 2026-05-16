from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"

    codigo: str = Field(max_length=20, primary_key=True)
    descripcion: str = Field(sa_column=Column(Text))
    orden: int = Field(nullable=False)
    es_terminal: bool = Field(nullable=False)
