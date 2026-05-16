from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, Text
from app.models.base import TimestampMixin, SoftDeleteMixin


class Categoria(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "categoria"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(max_length=100, unique=True, nullable=False)
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    parent_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger, ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True
        ),
    )
    imagen_url: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    # Relación recursiva (self-referential)
    hijos: list["Categoria"] = Relationship(back_populates="parent")
    parent: Optional["Categoria"] = Relationship(
        back_populates="hijos", sa_relationship_kwargs={"remote_side": "Categoria.id"}
    )
