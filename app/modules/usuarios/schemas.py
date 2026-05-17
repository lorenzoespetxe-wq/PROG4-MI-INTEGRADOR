from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2)
    apellido: str = Field(min_length=2)
    email: EmailStr
    celular: str | None = None
    password: str = Field(min_length=8)


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2)
    apellido: str | None = Field(default=None, min_length=2)
    celular: str | None = None
    activo: bool | None = None


class UsuarioRead(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    celular: str | None
    activo: bool
    roles: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedUsuarios(BaseModel):
    items: list[UsuarioRead]
    total: int
    page: int
    size: int
    pages: int


class AsignarRolRequest(BaseModel):
    rol_codigo: str = Field(min_length=2)
