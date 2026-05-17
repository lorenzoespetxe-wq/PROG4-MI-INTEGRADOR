# app/modules/categorias/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CategoriaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None
    parent_id: int | None = None
    imagen_url: str | None = None


class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = None
    parent_id: int | None = None
    imagen_url: str | None = None


class CategoriaRead(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    parent_id: int | None
    imagen_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoriaTree(BaseModel):
    id: int
    nombre: str
    imagen_url: str | None
    hijos: list["CategoriaTree"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
