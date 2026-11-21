"""Reglas de negocio del perfil de usuario."""

from typing import Any

from psycopg.errors import UniqueViolation

from core.exceptions import Conflicto, ErrorInterno, NoAutenticado, Validacion
from repositories import usuario_repository
from services import dni_service

ROL_INICIAL = "ciudadano"


def crear_perfil(
    conn,
    usuario_id: str,
    email: str | None,
    dni: str,
    acepto_datos: bool,
) -> dict[str, Any]:
    """Crea el perfil del usuario autenticado con rol ciudadano."""
    if not acepto_datos:
        raise Validacion("Debes aceptar el tratamiento de tus datos personales")
    if not email:
        raise NoAutenticado("El token no contiene un correo electrónico")

    if usuario_repository.obtener_perfil(conn, usuario_id) is not None:
        raise Conflicto("El perfil ya existe")
    if usuario_repository.existe_dni(conn, dni):
        raise Conflicto("El DNI ya está registrado")

    datos = dni_service.consultar_dni(dni)
    rol_id = usuario_repository.obtener_rol_id(conn, ROL_INICIAL)
    if rol_id is None:
        raise ErrorInterno("No se encontró el rol ciudadano")

    try:
        return usuario_repository.crear_usuario(
            conn,
            usuario_id=usuario_id,
            rol_id=rol_id,
            dni=dni,
            nombres=datos["nombres"],
            apellido_paterno=datos["apellido_paterno"],
            apellido_materno=datos["apellido_materno"],
            email=email,
        )
    except UniqueViolation as exc:
        raise Conflicto("El DNI o el correo ya están registrados") from exc
