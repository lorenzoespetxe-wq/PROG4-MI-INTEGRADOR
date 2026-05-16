from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, CHAR
from app.models.base import TimestampMixin, SoftDeleteMixin


class Usuario(TimestampMixin, SoftDeleteMixin, SQLModel, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    nombre: str = Field(max_length=80, nullable=False)
    apellido: str = Field(max_length=80, nullable=False)
    email: str = Field(max_length=254, unique=True, index=True, nullable=False)
    celular: str | None = Field(default=None, max_length=20)
    password_hash: str = Field(sa_column=Column(CHAR(60), nullable=False))
    activo: bool = Field(default=True, nullable=False)

    # Relaciones (forward references para evitar dependencias circulares)
    usuarios_roles: list["UsuarioRol"] = Relationship(back_populates="usuario")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="usuario")
    direcciones: list["DireccionEntrega"] = Relationship(back_populates="usuario")
    pedidos: list["Pedido"] = Relationship(back_populates="usuario")
    historiales: list["HistorialEstadoPedido"] = Relationship(back_populates="usuario")
