# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

from app.modules.auth.router import router as auth_router
from app.modules.usuarios.router import router as usuarios_router
from app.modules.direcciones.router import router as direcciones_router
from app.modules.categorias.router import router as categorias_router
from app.modules.unidades.router import router as unidades_router
from app.modules.ingredientes.router import router as ingredientes_router
from app.modules.productos.router import router as productos_router
from app.modules.pedidos.router import router as pedidos_router
from app.modules.pagos.router import router as pagos_router
from app.modules.admin.router import router as admin_router

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Food Store API iniciando...")
    yield
    print("🛑 Food Store API cerrando...")


app = FastAPI(
    title="Food Store API",
    version="1.0.0",
    description="Backend para plataforma de pedidos de comida",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(usuarios_router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(
    direcciones_router, prefix="/api/v1/direcciones", tags=["Direcciones"]
)
app.include_router(categorias_router, prefix="/api/v1/categorias", tags=["Categorías"])
app.include_router(unidades_router, prefix="/api/v1/unidades", tags=["Unidades"])
app.include_router(
    ingredientes_router, prefix="/api/v1/ingredientes", tags=["Ingredientes"]
)
app.include_router(productos_router, prefix="/api/v1/productos", tags=["Productos"])
app.include_router(pedidos_router, prefix="/api/v1/pedidos", tags=["Pedidos"])
app.include_router(pagos_router, prefix="/api/v1/pagos", tags=["Pagos"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
