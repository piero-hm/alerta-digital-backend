"""Schemas del módulo transversal de autenticación y DNI."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DniOut(BaseModel):
    """Datos personales obtenidos a partir del DNI."""

    dni: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None = None


class PerfilCreate(BaseModel):
    """Datos para crear el perfil del usuario autenticado."""

    dni: str = Field(pattern=r"^\d{8}$")
    acepto_datos: bool


class PerfilOut(BaseModel):
    """Perfil del usuario con el nombre de su rol."""

    id: UUID
    dni: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None = None
    email: str
    rol: str
    activo: bool
    acepto_datos_en: datetime
    creado_en: datetime
