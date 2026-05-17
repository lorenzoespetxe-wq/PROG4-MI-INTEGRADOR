from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, CHAR, DateTime, func, ForeignKey, String

from app.core.base_model import TimestampMixin, SoftDeleteMixin


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    codigo: str = Field(max_length=20, primary_key=True)
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    descripcion: str | None = Field(default=None)


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

    # Relaciones - join explícito para evitar ambigüedad con asignado_por_id
    usuarios_roles: list["UsuarioRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"primaryjoin": "Usuario.id == UsuarioRol.usuario_id"},
    )
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="usuario")
    direcciones: list["DireccionEntrega"] = Relationship(back_populates="usuario")
    pedidos: list["Pedido"] = Relationship(back_populates="usuario")
    historiales: list["HistorialEstadoPedido"] = Relationship(back_populates="usuario")


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"

    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), primary_key=True)
    )
    rol_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("rol.codigo"), primary_key=True)
    )
    asignado_por_id: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    # Relación explícita
    usuario: "Usuario" = Relationship(
        back_populates="usuarios_roles",
        sa_relationship_kwargs={"primaryjoin": "Usuario.id == UsuarioRol.usuario_id"},
    )
