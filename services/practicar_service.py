"""Reglas de negocio del módulo Practicar."""

from collections import defaultdict
from typing import Any

from core.exceptions import NoEncontrado
from repositories import practicar_repository


def obtener_preguntas(conn, slug: str) -> list[dict[str, Any]]:
    """Devuelve preguntas activas con opciones, sin revelar la correcta."""
    tema = practicar_repository.obtener_tema_publicado(conn, slug)
    if tema is None:
        raise NoEncontrado("Tema no encontrado")

    preguntas = practicar_repository.listar_preguntas_activas(conn, tema["id"])
    opciones = practicar_repository.listar_opciones_por_tema(conn, tema["id"])

    opciones_por_pregunta: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for opcion in opciones:
        opciones_por_pregunta[opcion["pregunta_id"]].append(
            {"id": opcion["id"], "texto": opcion["texto"]}
        )

    for pregunta in preguntas:
        pregunta["opciones"] = opciones_por_pregunta.get(pregunta["id"], [])

    return preguntas


def responder(conn, usuario_id: str, opcion_id: int) -> dict[str, Any]:
    """Guarda una respuesta nueva y devuelve si era correcta y su explicación."""
    opcion = practicar_repository.obtener_opcion_para_responder(conn, opcion_id)
    if opcion is None:
        raise NoEncontrado("Opción no encontrada")

    practicar_repository.guardar_respuesta(conn, usuario_id, opcion_id)
    return {
        "es_correcta": opcion["es_correcta"],
        "explicacion": opcion["explicacion"],
    }


def obtener_progreso(conn, usuario_id: str) -> list[dict[str, Any]]:
    """Calcula porcentaje y completado a partir de la vista de progreso."""
    filas = practicar_repository.obtener_progreso(conn, usuario_id)

    progreso = []
    for fila in filas:
        total = int(fila["total_preguntas"] or 0)
        correctas = int(fila["correctas"] or 0)
        progreso.append(
            {
                "tema_id": fila["tema_id"],
                "slug": fila["slug"],
                "titulo": fila["titulo"],
                "total_preguntas": total,
                "correctas": correctas,
                "porcentaje": round(correctas * 100 / total, 2) if total else 0.0,
                "completado": total > 0 and correctas == total,
            }
        )
    return progreso
