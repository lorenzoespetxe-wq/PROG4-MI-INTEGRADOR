from fastapi import HTTPException

# Códigos de error constantes
NOT_FOUND = "NOT_FOUND"
ALREADY_EXISTS = "ALREADY_EXISTS"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
FORBIDDEN = "FORBIDDEN"
INVALID_TRANSITION = "INVALID_TRANSITION"
TERMINAL_STATE = "TERMINAL_STATE"
INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
PAYMENT_ERROR = "PAYMENT_ERROR"


def http_error(
    status_code: int, detail: str, code: str, field: str | None = None
) -> HTTPException:
    payload = {
        "detail": detail,
        "code": code,
    }
    if field is not None:
        payload["field"] = field

    return HTTPException(status_code=status_code, detail=payload)
