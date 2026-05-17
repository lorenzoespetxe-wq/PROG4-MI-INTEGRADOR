# app/modules/productos/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class IngredienteEnProductoRequest(BaseModel):
    ingrediente_id: int
    cantidad: float = Field(gt=0)
    unidad_medida_id: int
    es_removible: bool


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    precio_base: float = Field(ge=0)
    imagenes_url: list[str] | None = None
    stock_cantidad: int = Field(default=0, ge=0)
    disponible: bool = True
    unidad_venta_id: int | None = None
    categoria_ids: list[int] = Field(min_length=1)
    ingredientes: list[IngredienteEnProductoRequest] = Field(default_factory=list)


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    precio_base: float | None = Field(default=None, ge=0)
    imagenes_url: list[str] | None = None
    stock_cantidad: int | None = Field(default=None, ge=0)
    disponible: bool | None = None
    unidad_venta_id: int | None = None
    categoria_ids: list[int] | None = Field(default=None, min_length=1)
    ingredientes: list[IngredienteEnProductoRequest] | None = None


class IngredienteEnProductoRead(BaseModel):
    ingrediente_id: int
    nombre: str
    es_alergeno: bool
    cantidad: float
    simbolo_unidad: str
    es_removible: bool

    model_config = ConfigDict(from_attributes=True)


class UnidadResumen(BaseModel):
    id: int
    nombre: str
    simbolo: str

    model_config = ConfigDict(from_attributes=True)


class ProductoRead(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    precio_base: float
    imagenes_url: list[str] | None
    stock_cantidad: int
    disponible: bool
    unidad_venta: UnidadResumen | None
    categorias: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductoDetail(ProductoRead):
    ingredientes: list[IngredienteEnProductoRead]


class PaginatedProductos(BaseModel):
    items: list[ProductoRead]
    total: int
    page: int
    size: int
    pages: int


class StockUpdateRequest(BaseModel):
    stock_cantidad: int = Field(ge=0)


class DisponibilidadRequest(BaseModel):
    disponible: bool
