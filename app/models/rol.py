from sqlmodel import SQLModel, Field


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    codigo: str = Field(max_length=20, primary_key=True)
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    descripcion: str | None = Field(default=None)
