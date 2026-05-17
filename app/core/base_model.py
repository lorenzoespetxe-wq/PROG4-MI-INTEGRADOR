from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, func


class TimestampMixin(SQLModel):
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": func.now()},
        nullable=True,
    )


class SoftDeleteMixin(SQLModel):
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )
