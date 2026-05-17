# app/modules/unidades/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UnidadMedidaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)
    simbolo: str = Field(min_length=1, max_length=10)
    tipo: str = Field(min_length=1, max_length=50)


class UnidadMedidaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=50)
    simbolo: str | None = Field(default=None, min_length=1, max_length=10)
    tipo: str | None = Field(default=None, min_length=1, max_length=50)


class UnidadMedidaRead(BaseModel):
    id: int
    nombre: str
    simbolo: str
    tipo: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
