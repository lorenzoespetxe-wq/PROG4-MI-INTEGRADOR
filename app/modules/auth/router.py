# app/modules/auth/router.py
from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.unit_of_work import UnitOfWork
from app.core.dependencies import get_uow, get_current_user, UserInToken
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
def register(
    request: Request,
    data: RegisterRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)
    return service.register(data)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
def login(
    request: Request,
    data: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)
    return service.login(data)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh(
    data: RefreshRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)
    return service.refresh(data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    data: RefreshRequest,
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)
    service.logout(data.refresh_token)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: UserInToken = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    service = AuthService(uow)
    return service.get_me(current_user.id)
