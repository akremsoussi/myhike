from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    """Erreur renvoyée au front sous la forme {"detail": {"code", "message", ...}}.

    `code` est stable (le front s'en sert), `message` est affichable tel quel.
    """

    def __init__(self, status_code: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(status_code, detail={"code": code, "message": message, **extra})


def _field_message(error: dict[str, Any]) -> str:
    # Message écrit dans un validateur (ValueError), sinon message générique en français.
    if error["type"] == "value_error":
        return str(error["ctx"]["error"])
    if error["type"] == "missing":
        return "Champ obligatoire."
    return "Valeur invalide."


async def validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # loc = ("body", "champ", …) : une erreur imbriquée (un point de stop) remonte sur son champ.
    fields: dict[str, str] = {}
    for error in exc.errors():
        if len(error["loc"]) > 1:
            fields.setdefault(str(error["loc"][1]), _field_message(error))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": {
                "code": "validation_error",
                "message": "Certains champs sont invalides.",
                "fields": fields,
            }
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
