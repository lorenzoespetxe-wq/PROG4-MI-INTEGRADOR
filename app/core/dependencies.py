from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from pydantic import BaseModel

from app.core.database import get_session
from app.core.security import decode_token
from app.core.unit_of_work import UnitOfWork

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserInToken(BaseModel):
    id: int
    email: str
    roles: list[str]


def get_uow(session: Session = Depends(get_session)) -> UnitOfWork:
    return UnitOfWork(session)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session),
) -> UserInToken:
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))

    # Importación local diferida para evitar errores circulares y
    # dependencias prematuras de la Fase 2
    from app.models.usuario import Usuario

    user = session.get(Usuario, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo"
        )

    email = payload.get("email", user.email)
    roles = payload.get("roles", [])

    return UserInToken(id=user_id, email=email, roles=roles)


def require_role(*required_roles: str):
    def role_checker(
        current_user: UserInToken = Depends(get_current_user),
    ) -> UserInToken:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes"
            )
        return current_user

    return role_checker
