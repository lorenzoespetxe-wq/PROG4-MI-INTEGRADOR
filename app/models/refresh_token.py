from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, BigInteger, ForeignKey, CHAR, DateTime, func


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("usuario.id"), nullable=False)
    )
    token_hash: str = Field(
        sa_column=Column(CHAR(64), unique=True, index=True, nullable=False)
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    revoked_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    usuario: "Usuario" = Relationship(back_populates="refresh_tokens")
