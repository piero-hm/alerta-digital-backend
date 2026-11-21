"""Reglas de negocio del módulo transversal de catálogos."""

from typing import Any

from repositories import catalogos_repository


def obtener_catalogos(conn) -> dict[str, Any]:
    """Devuelve departamentos, tipos de fraude y canales."""
    return {
        "departamentos": catalogos_repository.listar_departamentos(conn),
        "tipos_fraude": catalogos_repository.listar_tipos_fraude(conn),
        "canales": catalogos_repository.listar_canales(conn),
    }
