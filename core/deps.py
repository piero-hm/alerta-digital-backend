"""Dependencias de autenticación y autorización para los routers."""

from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.database import get_db
from core.exceptions import NoAutenticado, SinPermiso
from core.security import validar_token
from repositories import usuario_repository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Valida solo el JWT y devuelve {sub, email} (aunque no exista perfil)."""
    if credentials is None:
        raise NoAutenticado("Falta el token de autenticación")
    return validar_token(credentials.credentials)


def get_current_profile(
    user: dict[str, Any] = Depends(get_current_user),
    conn=Depends(get_db),
) -> dict[str, Any]:
    """Valida el JWT y busca la fila del usuario con el nombre de su rol."""
    perfil = usuario_repository.obtener_perfil(conn, user["sub"])
    if perfil is None:
        raise SinPermiso("Falta completar el perfil")
    return {**user, **perfil}


def require_role(*roles: str):
    """Devuelve una dependencia que exige uno de los roles indicados."""

    def _verificar_rol(perfil: dict[str, Any] = Depends(get_current_profile)):
        if perfil.get("rol") not in roles:
            raise SinPermiso("No tienes permiso para realizar esta acción")
        return perfil

    return _verificar_rol
