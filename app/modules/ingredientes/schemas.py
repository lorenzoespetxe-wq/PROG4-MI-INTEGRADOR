# app/modules/ingredientes/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class IngredienteCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    es_alergeno: bool = Field(default=False)
    descripcion: str | None = None


class IngredienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    es_alergeno: bool | None = None
    descripcion: str | None = None


class IngredienteRead(BaseModel):
    id: int
    nombre: str
    es_alergeno: bool
    descripcion: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedIngredientes(BaseModel):
    items: list[IngredienteRead]
    total: int
    page: int
    size: int
    pages: int
