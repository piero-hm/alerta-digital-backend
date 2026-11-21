"""Reglas de negocio del módulo Aprender."""

from typing import Any

from core.exceptions import NoEncontrado
from repositories import aprender_repository


def listar_temas(
    conn, publico_objetivo: str | None = None
) -> list[dict[str, Any]]:
    """Devuelve los temas publicados (opcionalmente por público objetivo)."""
    return aprender_repository.listar_temas_publicados(conn, publico_objetivo)


def obtener_tema(conn, slug: str) -> dict[str, Any]:
    """Devuelve un tema publicado con sus bloques ordenados."""
    tema = aprender_repository.obtener_tema_publicado(conn, slug)
    if tema is None:
        raise NoEncontrado("Tema no encontrado")
    tema["bloques"] = aprender_repository.listar_bloques(conn, tema["id"])
    return tema
