"""Modelos comunes de entrada y salida."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Formato único de error de la API."""

    code: str
    detail: str
