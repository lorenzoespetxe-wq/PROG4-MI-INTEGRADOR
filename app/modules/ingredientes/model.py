from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger, Text
from app.core.base_model import TimestampMixin, SoftDeleteMixin


class Ingrediente(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "ingrediente"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(max_length=100, unique=True, nullable=False)
    es_alergeno: bool = Field(default=False, nullable=False)
    descripcion: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
