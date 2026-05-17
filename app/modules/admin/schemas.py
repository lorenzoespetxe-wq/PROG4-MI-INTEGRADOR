# app/modules/admin/schemas.py
from pydantic import BaseModel, Field


class ProductoStockAlert(BaseModel):
    id: int
    nombre: str
    stock_cantidad: int
    disponible: bool


class TopProducto(BaseModel):
    id: int
    nombre: str
    total_vendido: int


class DashboardMetrics(BaseModel):
    total_pedidos_hoy: int
    ingresos_hoy: float
    pedidos_por_estado: dict[str, int]
    productos_bajo_stock: list[ProductoStockAlert]
    top_productos: list[TopProducto]


class StockBulkItem(BaseModel):
    producto_id: int
    stock_cantidad: int = Field(ge=0)


class StockBulkUpdate(BaseModel):
    actualizaciones: list[StockBulkItem] = Field(min_length=1, max_length=50)


class StockBulkResponse(BaseModel):
    updated: int
    errores: list[str]
