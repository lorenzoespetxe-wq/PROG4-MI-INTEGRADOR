import hashlib
from datetime import datetime, timedelta, timezone
from sqlmodel import select

from app.core.config import settings
from app.core.unit_of_work import UnitOfWork
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.exceptions import (
    http_error,
    ALREADY_EXISTS,
    INVALID_CREDENTIALS,
    FORBIDDEN,
    NOT_FOUND,
)
from app.modules.usuarios.model import Usuario, UsuarioRol
from app.modules.refreshtokens.model import RefreshToken
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.modules.auth.repository import RefreshTokenRepository


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def register(self, data: RegisterRequest) -> UserResponse:
        with self.uow:
            statement = select(Usuario).where(Usuario.email == data.email)
            existing_user = self.uow.session.exec(statement).first()
            if existing_user:
                raise http_error(409, "El email ya está registrado", ALREADY_EXISTS)

            nuevo_usuario = Usuario(
                nombre=data.nombre,
                apellido=data.apellido,
                email=data.email,
                celular=data.celular,
                password_hash=hash_password(data.password),
                activo=True,
            )
            self.uow.session.add(nuevo_usuario)
            self.uow.session.flush()

            rol_cliente = UsuarioRol(
                usuario_id=nuevo_usuario.id, rol_codigo="CLIENT", asignado_por_id=None
            )
            self.uow.session.add(rol_cliente)
            self.uow.session.flush()

            # Forzar la carga de la relación para el esquema de respuesta
            self.uow.session.refresh(nuevo_usuario)
            roles = ["CLIENT"]

            return UserResponse(
                id=nuevo_usuario.id,
                nombre=nuevo_usuario.nombre,
                apellido=nuevo_usuario.apellido,
                email=nuevo_usuario.email,
                celular=nuevo_usuario.celular,
                roles=roles,
                created_at=nuevo_usuario.created_at,
            )

    def login(self, data: LoginRequest) -> TokenResponse:
        with self.uow:
            statement = select(Usuario).where(Usuario.email == data.email)
            usuario = self.uow.session.exec(statement).first()

            if not usuario or not verify_password(data.password, usuario.password_hash):
                raise http_error(401, "Credenciales inválidas", INVALID_CREDENTIALS)

            # FIX: verificar tanto `activo` como `deleted_at` para bloquear
            # usuarios con baja lógica aunque `activo` no haya sido seteado a
            # False por un estado inconsistente previo en la base de datos.
            if not usuario.activo or usuario.deleted_at is not None:
                raise http_error(401, "Credenciales inválidas", INVALID_CREDENTIALS)

            roles = [ur.rol_codigo for ur in usuario.usuarios_roles]

            access_token = create_access_token(
                data={"sub": str(usuario.id), "email": usuario.email, "roles": roles},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            raw_refresh_token = create_refresh_token()
            token_hash = self._hash_token(raw_refresh_token)

            nuevo_refresh_token = RefreshToken(
                usuario_id=usuario.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
            self.uow.session.add(nuevo_refresh_token)

            return TokenResponse(
                access_token=access_token,
                refresh_token=raw_refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

    def refresh(self, data: RefreshRequest) -> TokenResponse:
        with self.uow:
            repo = RefreshTokenRepository(self.uow.session)
            token_hash = self._hash_token(data.refresh_token)
            db_token = repo.get_by_hash(token_hash)

            if not db_token:
                raise http_error(401, "Token inválido", INVALID_CREDENTIALS)

            if db_token.revoked_at is not None or db_token.expires_at < datetime.now(
                timezone.utc
            ):
                raise http_error(401, "Token inválido o expirado", INVALID_CREDENTIALS)

            # Cargar usuario para generar nuevo payload
            usuario = db_token.usuario
            if not usuario.activo:
                raise http_error(403, "Usuario inactivo", FORBIDDEN)

            # Revocar token actual
            repo.revoke(db_token)

            roles = [ur.rol_codigo for ur in usuario.usuarios_roles]
            access_token = create_access_token(
                data={"sub": str(usuario.id), "email": usuario.email, "roles": roles},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            raw_refresh_token = create_refresh_token()
            new_token_hash = self._hash_token(raw_refresh_token)

            nuevo_refresh_token = RefreshToken(
                usuario_id=usuario.id,
                token_hash=new_token_hash,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
            self.uow.session.add(nuevo_refresh_token)

            return TokenResponse(
                access_token=access_token,
                refresh_token=raw_refresh_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

    def logout(self, refresh_token: str) -> None:
        with self.uow:
            repo = RefreshTokenRepository(self.uow.session)
            token_hash = self._hash_token(refresh_token)
            db_token = repo.get_by_hash(token_hash)

            if db_token and db_token.revoked_at is None:
                repo.revoke(db_token)

    def get_me(self, usuario_id: int) -> UserResponse:
        with self.uow:
            usuario = self.uow.session.get(Usuario, usuario_id)
            if not usuario or not usuario.activo:
                raise http_error(404, "Usuario no encontrado", NOT_FOUND)

            roles = [ur.rol_codigo for ur in usuario.usuarios_roles]

            return UserResponse(
                id=usuario.id,
                nombre=usuario.nombre,
                apellido=usuario.apellido,
                email=usuario.email,
                celular=usuario.celular,
                roles=roles,
                created_at=usuario.created_at,
            )
