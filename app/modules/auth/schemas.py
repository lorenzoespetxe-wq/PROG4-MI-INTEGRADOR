import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=2)
    apellido: str = Field(min_length=2)
    email: EmailStr
    celular: str | None = None
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    celular: str | None
    roles: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
