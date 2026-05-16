from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func, BigInteger, ForeignKey, String


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

    # Relación explícita indicando la FK correcta para evitar ambigüedad con asignado_por_id
    usuario: "Usuario" = Relationship(
        back_populates="usuarios_roles",
        sa_relationship_kwargs={"foreign_keys": "[UsuarioRol.usuario_id]"},
    )
