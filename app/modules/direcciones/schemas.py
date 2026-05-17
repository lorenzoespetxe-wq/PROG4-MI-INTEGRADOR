# app/modules/direcciones/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DireccionCreate(BaseModel):
    alias: str | None = Field(default=None, max_length=50)
    linea1: str = Field(min_length=1)
    linea2: str | None = None
    ciudad: str | None = Field(default=None, max_length=100)
    provincia: str | None = Field(default=None, max_length=100)
    codigo_postal: str | None = Field(default=None, max_length=10)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class DireccionUpdate(BaseModel):
    alias: str | None = Field(default=None, max_length=50)
    linea1: str | None = Field(default=None, min_length=1)
    linea2: str | None = None
    ciudad: str | None = Field(default=None, max_length=100)
    provincia: str | None = Field(default=None, max_length=100)
    codigo_postal: str | None = Field(default=None, max_length=10)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class DireccionRead(BaseModel):
    id: int
    usuario_id: int
    alias: str | None
    linea1: str
    linea2: str | None
    ciudad: str | None
    provincia: str | None
    codigo_postal: str | None
    latitud: float | None
    longitud: float | None
    es_principal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
