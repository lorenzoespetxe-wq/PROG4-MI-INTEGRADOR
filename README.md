# Food Store — Backend API

Backend REST para una plataforma de pedidos de comida. Construido con **FastAPI · Python 3.12 · SQLModel · PostgreSQL 16 · Alembic**.

Arquitectura Feature-First con patrón Unit of Work, RBAC, JWT con refresh token rotativo e integración con MercadoPago.

---

## Setup local

### Prerrequisitos

- Python 3.12+
- Docker y Docker Compose
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd PROG4-MI-INTEGRADOR

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (ver sección Variables de entorno)

# 4. Levantar la base de datos
docker-compose up -d

# 5. Correr migraciones
alembic upgrade head

# 6. Cargar datos iniciales (roles, estados, formas de pago, admin)
python -m app.db.seed

# 7. Levantar el servidor
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva en `http://localhost:8000/docs`.
pgAdmin en `http://localhost:5050` (usuario: `admin@foodstore.com`, contraseña: `admin`).

---

## Variables de entorno

Copiar `.env.example` a `.env` y completar cada valor:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@localhost:5432/foodstore_db` |
| `SECRET_KEY` | Clave secreta para firmar JWT. Mínimo 32 caracteres. | `cambia-esto-por-un-secreto-largo` |
| `ALGORITHM` | Algoritmo de firma JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del access token en minutos | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Duración del refresh token en días | `7` |
| `CORS_ORIGINS` | Lista JSON de orígenes permitidos por CORS | `["http://localhost:5173"]` |
| `MP_ACCESS_TOKEN` | Access token de MercadoPago (empieza con `TEST-` en sandbox) | `TEST-xxxx` |
| `MP_PUBLIC_KEY` | Public key de MercadoPago | `TEST-xxxx` |
| `MP_NOTIFICATION_URL` | URL pública donde MP enviará notificaciones IPN | `https://tu-dominio.com/api/v1/pagos/webhook` |

> Para desarrollo con sandbox de MercadoPago, obtener credenciales en [developers.mercadopago.com](https://www.mercadopago.com.ar/developers/panel/app).
> `MP_NOTIFICATION_URL` requiere una URL pública; en desarrollo se puede usar [ngrok](https://ngrok.com/).

---

## Credenciales del admin por defecto

Creadas por el seed:

| Campo | Valor |
|---|---|
| Email | `admin@foodstore.com` |
| Password | `Admin1234!` |

Cambiar la contraseña en producción.

---

## Roles del sistema

| Rol | Código | Permisos |
|---|---|---|
| Administrador | `ADMIN` | Acceso total: gestión de usuarios, productos, categorías, ingredientes, unidades, pedidos, dashboard y stock bulk |
| Gestor de Stock | `STOCK` | Crear y editar productos, actualizar stock y disponibilidad, stock bulk |
| Gestor de Pedidos | `PEDIDOS` | Ver y avanzar estados de todos los pedidos, ver panel de pedidos activos |
| Cliente | `CLIENT` | Crear pedidos, ver sus propios pedidos e historial, gestionar sus direcciones, cancelar pedidos propios en PENDIENTE o CONFIRMADO |

Un usuario puede tener múltiples roles simultáneamente. El rol `CLIENT` se asigna automáticamente al registrarse.

---

## Tarjetas de prueba — Sandbox MercadoPago

Usar estos datos al llamar al endpoint `POST /api/v1/pagos/crear`. El campo `token_tarjeta` se genera en el frontend con el SDK de MercadoPago usando los datos de la tarjeta.

### Tarjeta aprobada

| Campo | Valor |
|---|---|
| Número | `4509 9535 6623 3704` |
| CVV | `123` |
| Vencimiento | `11/25` |
| Titular | `APRO` |

### Tarjeta rechazada

| Campo | Valor |
|---|---|
| Número | `4000 0000 0000 0002` |
| CVV | `123` |
| Vencimiento | `11/25` |
| Titular | `OTHE` |

> Consultar el listado completo de tarjetas de prueba en la [documentación oficial de MercadoPago](https://www.mercadopago.com.ar/developers/es/docs/your-integrations/test/cards).

---

## FSM de pedidos

```
PENDIENTE → CONFIRMADO → EN_PREP → EN_CAMINO → ENTREGADO
    ↓              ↓         ↓
CANCELADO      CANCELADO  CANCELADO
```

- **ENTREGADO** y **CANCELADO** son estados terminales; no admiten más transiciones.
- Al cancelar desde cualquier estado con stock descontado (PENDIENTE, CONFIRMADO, EN_PREP, EN_CAMINO), el stock de cada ítem se restaura automáticamente.
- El historial de estados es append-only: nunca se modifica ni elimina.

---

## Endpoints principales

### Auth — `/api/v1/auth`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/register` | Público | Registrar nuevo usuario (rol CLIENT automático) |
| POST | `/login` | Público | Login, retorna access + refresh token |
| POST | `/refresh` | Público | Rotar refresh token |
| POST | `/logout` | Bearer | Revocar refresh token |
| GET | `/me` | Bearer | Datos del usuario autenticado |

### Usuarios — `/api/v1/usuarios`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | ADMIN | Listar usuarios paginado |
| GET | `/{id}` | ADMIN o propio | Ver usuario |
| PATCH | `/{id}` | ADMIN o propio | Actualizar usuario |
| DELETE | `/{id}` | ADMIN | Soft delete de usuario |
| POST | `/{id}/roles` | ADMIN | Asignar rol |
| DELETE | `/{id}/roles/{codigo}` | ADMIN | Revocar rol |

### Direcciones — `/api/v1/direcciones`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Bearer | Listar direcciones propias |
| POST | `/` | Bearer | Crear dirección |
| PUT | `/{id}` | Bearer (propietario) | Actualizar dirección |
| DELETE | `/{id}` | Bearer (propietario) | Eliminar dirección |
| PATCH | `/{id}/principal` | Bearer (propietario) | Marcar como principal |

### Categorías — `/api/v1/categorias`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Público | Listar categorías (lista plana) |
| GET | `/arbol` | Público | Árbol jerárquico anidado |
| GET | `/{id}` | Público | Ver categoría |
| POST | `/` | ADMIN | Crear categoría |
| PUT | `/{id}` | ADMIN | Actualizar categoría |
| DELETE | `/{id}` | ADMIN | Eliminar categoría |

### Unidades de medida — `/api/v1/unidades`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Público | Listar unidades. Query: `tipo` |
| GET | `/{id}` | Público | Ver unidad |
| POST | `/` | ADMIN | Crear unidad |
| PUT | `/{id}` | ADMIN | Actualizar unidad |
| DELETE | `/{id}` | ADMIN | Eliminar unidad (hard delete) |

### Ingredientes — `/api/v1/ingredientes`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Público | Listar paginado. Query: `solo_alergenos`, `page`, `size` |
| GET | `/{id}` | Público | Ver ingrediente |
| POST | `/` | ADMIN | Crear ingrediente |
| PATCH | `/{id}` | ADMIN | Actualizar ingrediente |
| DELETE | `/{id}` | ADMIN | Soft delete (falla si está en uso) |

### Productos — `/api/v1/productos`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Público | Listar paginado. Query: `search`, `categoria_id`, `disponible`, `page`, `size` |
| GET | `/{id}` | Público | Ver producto con ingredientes |
| POST | `/` | ADMIN, STOCK | Crear producto |
| PUT | `/{id}` | ADMIN, STOCK | Actualizar producto |
| DELETE | `/{id}` | ADMIN | Soft delete |
| PATCH | `/{id}/disponibilidad` | ADMIN, STOCK | Cambiar disponibilidad |
| PATCH | `/{id}/stock` | ADMIN, STOCK | Actualizar stock (valor absoluto) |
| GET | `/{id}/ingredientes` | Público | Listar ingredientes del producto |
| POST | `/{id}/ingredientes` | ADMIN | Agregar ingrediente al producto |
| DELETE | `/{id}/ingredientes/{ingrediente_id}` | ADMIN | Quitar ingrediente del producto |

### Pedidos — `/api/v1/pedidos`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | Bearer | Listar pedidos. CLIENT ve los suyos; ADMIN/PEDIDOS ven todos. Query: `estado`, `page`, `size` |
| POST | `/` | Bearer | Crear pedido (descuenta stock atómicamente) |
| GET | `/{id}` | Bearer | Ver detalle. CLIENT solo ve los suyos |
| PATCH | `/{id}/estado` | Bearer | Avanzar estado según FSM |
| DELETE | `/{id}` | Bearer | Cancelar pedido propio (solo desde PENDIENTE o CONFIRMADO) |
| GET | `/{id}/historial` | Bearer | Ver historial de estados |

### Pagos — `/api/v1/pagos`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/crear` | CLIENT | Iniciar pago con MercadoPago |
| POST | `/webhook` | Público | Endpoint IPN para notificaciones de MercadoPago |
| GET | `/{pedido_id}` | Bearer | Ver pago de un pedido |

### Admin — `/api/v1/admin`

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/dashboard` | ADMIN | Métricas: pedidos hoy, ingresos, estados, bajo stock, top productos |
| GET | `/pedidos-activos` | ADMIN, PEDIDOS | Pedidos en curso paginados |
| POST | `/stock/bulk` | ADMIN, STOCK | Actualizar stock de hasta 50 productos en una transacción |

---

## Estructura del proyecto

```
app/
├── core/           # Config, seguridad, DB, excepciones, repositorio base, UoW
├── db/             # Registry de modelos (Alembic), seed
└── modules/
    ├── auth/
    ├── usuarios/
    ├── refreshtokens/
    ├── direcciones/
    ├── categorias/
    ├── unidades/
    ├── ingredientes/
    ├── productos/
    ├── pedidos/
    ├── pagos/
    └── admin/

alembic/            # Migraciones
```

Cada módulo sigue la estructura `model → repository → service → router → schemas`. La capa de acceso a datos (repository) nunca llama a `commit()`; esa responsabilidad es exclusiva del `UnitOfWork`.