"""Reglas de negocio de moderación y administración."""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from psycopg.errors import UniqueViolation

from core.exceptions import Conflicto, ErrorInterno, NoEncontrado, Validacion
from repositories import admin_repository
from schemas.admin import (
    BloqueAdminCreate,
    BloqueAdminUpdate,
    OpcionAdminCreate,
    OpcionAdminUpdate,
    PreguntaAdminCreate,
    PreguntaAdminUpdate,
    TemaAdminCreate,
    TemaAdminUpdate,
)

logger = logging.getLogger(__name__)
ESTADO_PENDIENTE = "pendiente"
ESTADOS_MODERACION = {"validado", "rechazado"}


def listar_reportes(conn, estado: str | None) -> list[dict[str, Any]]:
    """Lista reportes para moderación, validando el estado si se indica."""
    if estado is not None:
        if admin_repository.obtener_estado_id(conn, estado) is None:
            raise Validacion("Estado no válido")
    return admin_repository.listar_reportes(conn, estado)


def cambiar_estado_reporte(
    conn, reporte_id: int, nuevo_estado: str, perfil: dict[str, Any]
) -> dict[str, Any]:
    """Modera un reporte pendiente y registra el cambio en el log."""
    if nuevo_estado not in ESTADOS_MODERACION:
        raise Validacion("El estado debe ser 'validado' o 'rechazado'")

    actual = admin_repository.obtener_reporte_admin(conn, reporte_id)
    if actual is None:
        raise NoEncontrado("Reporte no encontrado")
    if actual["estado"] != ESTADO_PENDIENTE:
        raise Conflicto("Solo se pueden moderar reportes pendientes")

    estado_id = admin_repository.obtener_estado_id(conn, nuevo_estado)
    if estado_id is None:
        raise ErrorInterno("No se encontró el estado solicitado")

    actualizado = admin_repository.actualizar_estado_reporte(
        conn, reporte_id, estado_id, actual["estado_id"]
    )
    if actualizado is None:
        raise Conflicto("El reporte cambió de estado; vuelve a intentarlo")

    logger.info(
        "Reporte %s moderado por %s (%s) de '%s' a '%s' el %s",
        reporte_id,
        perfil.get("email"),
        perfil.get("id"),
        actual["estado"],
        nuevo_estado,
        datetime.now(timezone.utc).isoformat(),
    )
    return actualizado


def listar_temas(conn) -> list[dict[str, Any]]:
    """Lista todos los temas para administración."""
    return admin_repository.listar_temas_admin(conn)


def obtener_detalle_tema(conn, tema_id: int) -> dict[str, Any]:
    """Devuelve un tema con sus bloques y preguntas con opciones."""
    tema = admin_repository.obtener_tema_admin(conn, tema_id)
    if tema is None:
        raise NoEncontrado("Tema no encontrado")

    bloques = admin_repository.listar_bloques(conn, tema_id)
    preguntas = admin_repository.listar_preguntas_admin(conn, tema_id)
    opciones = admin_repository.listar_opciones_admin(conn, tema_id)

    opciones_por_pregunta: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for opcion in opciones:
        opciones_por_pregunta[opcion["pregunta_id"]].append(opcion)

    for pregunta in preguntas:
        pregunta["opciones"] = opciones_por_pregunta.get(pregunta["id"], [])

    return {**tema, "bloques": bloques, "preguntas": preguntas}


def crear_tema(conn, datos: TemaAdminCreate) -> dict[str, Any]:
    """Crea un tema no publicado."""
    if admin_repository.existe_slug(conn, datos.slug):
        raise Conflicto("El slug ya está en uso")
    try:
        return admin_repository.crear_tema(
            conn,
            slug=datos.slug,
            titulo=datos.titulo,
            resumen=datos.resumen,
            publico_objetivo=datos.publico_objetivo,
        )
    except UniqueViolation as exc:
        raise Conflicto("El slug ya está en uso") from exc


def actualizar_tema(
    conn, tema_id: int, datos: TemaAdminUpdate
) -> dict[str, Any]:
    """Edita los campos enviados de un tema."""
    actual = admin_repository.obtener_tema_admin(conn, tema_id)
    if actual is None:
        raise NoEncontrado("Tema no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    if "slug" in campos and admin_repository.existe_slug(
        conn, campos["slug"], excluir_id=tema_id
    ):
        raise Conflicto("El slug ya está en uso")
    if not campos:
        return actual

    try:
        return admin_repository.actualizar_tema(conn, tema_id, campos)
    except UniqueViolation as exc:
        raise Conflicto("El slug ya está en uso") from exc


def cambiar_publicacion(
    conn, tema_id: int, publicado: bool
) -> dict[str, Any]:
    """Publica o despublica un tema."""
    tema = admin_repository.actualizar_publicacion(
        conn, tema_id, publicado
    )
    if tema is None:
        raise NoEncontrado("Tema no encontrado")
    return tema


def crear_bloque(
    conn, tema_id: int, datos: BloqueAdminCreate
) -> dict[str, Any]:
    """Crea un bloque con orden único dentro del tema."""
    if admin_repository.obtener_tema_admin(conn, tema_id) is None:
        raise NoEncontrado("Tema no encontrado")
    if admin_repository.existe_orden_bloque(conn, tema_id, datos.orden):
        raise Conflicto("El orden ya está usado en este tema")

    try:
        return admin_repository.crear_bloque(
            conn,
            tema_id=tema_id,
            orden=datos.orden,
            tipo=datos.tipo,
            contenido=datos.contenido,
            recurso_url=datos.recurso_url,
        )
    except UniqueViolation as exc:
        raise Conflicto("El orden ya está usado en este tema") from exc


def actualizar_bloque(
    conn, bloque_id: int, datos: BloqueAdminUpdate
) -> dict[str, Any]:
    """Edita un bloque manteniendo el orden único por tema."""
    actual = admin_repository.obtener_bloque(conn, bloque_id)
    if actual is None:
        raise NoEncontrado("Bloque no encontrado")

    campos = datos.model_dump(exclude_unset=True)
    if "orden" in campos and admin_repository.existe_orden_bloque(
        conn, actual["tema_id"], campos["orden"], excluir_id=bloque_id
    ):
        raise Conflicto("El orden ya está usado en este tema")
    if not campos:
        return actual

    try:
        return admin_repository.actualizar_bloque(conn, bloque_id, campos)
    except UniqueViolation as exc:
        raise Conflicto("El orden ya está usado en este tema") from exc


def crear_pregunta(
    conn, tema_id: int, datos: PreguntaAdminCreate
) -> dict[str, Any]:
    """Crea una pregunta para un tema."""
    if admin_repository.obtener_tema_admin(conn, tema_id) is None:
        raise NoEncontrado("Tema no encontrado")

    pregunta = admin_repository.crear_pregunta(
        conn,
        tema_id=tema_id,
        enunciado=datos.enunciado,
        mensaje_simulado=datos.mensaje_simulado,
        explicacion=datos.explicacion,
        activa=datos.activa,
    )
    pregunta["opciones"] = []
    return pregunta


def actualizar_pregunta(
    conn, pregunta_id: int, datos: PreguntaAdminUpdate
) -> dict[str, Any]:
    """Edita una pregunta y devuelve sus opciones."""
    actual = admin_repository.obtener_pregunta(conn, pregunta_id)
    if actual is None:
        raise NoEncontrado("Pregunta no encontrada")

    campos = datos.model_dump(exclude_unset=True)
    if campos:
        actual = admin_repository.actualizar_pregunta(
            conn, pregunta_id, campos
        )
    actual["opciones"] = admin_repository.listar_opciones_por_pregunta(
        conn, pregunta_id
    )
    return actual


def crear_opcion(
    conn, pregunta_id: int, datos: OpcionAdminCreate
) -> dict[str, Any]:
    """Crea una opción respetando el máximo de una correcta por pregunta."""
    if admin_repository.obtener_pregunta(conn, pregunta_id) is None:
        raise NoEncontrado("Pregunta no encontrada")
    if datos.es_correcta and admin_repository.existe_opcion_correcta(
        conn, pregunta_id
    ):
        raise Conflicto("La pregunta ya tiene una opción correcta")

    try:
        return admin_repository.crear_opcion(
            conn,
            pregunta_id=pregunta_id,
            texto=datos.texto,
            es_correcta=datos.es_correcta,
        )
    except UniqueViolation as exc:
        raise Conflicto("La pregunta ya tiene una opción correcta") from exc


def actualizar_opcion(
    conn, opcion_id: int, datos: OpcionAdminUpdate
) -> dict[str, Any]:
    """Edita una opción respetando el máximo de una correcta por pregunta."""
    actual = admin_repository.obtener_opcion(conn, opcion_id)
    if actual is None:
        raise NoEncontrado("Opción no encontrada")

    campos = datos.model_dump(exclude_unset=True)
    if campos.get("es_correcta") is True and admin_repository.existe_opcion_correcta(
        conn, actual["pregunta_id"], excluir_id=opcion_id
    ):
        raise Conflicto("La pregunta ya tiene una opción correcta")
    if not campos:
        return actual

    try:
        return admin_repository.actualizar_opcion(
            conn, opcion_id, campos
        )
    except UniqueViolation as exc:
        raise Conflicto("La pregunta ya tiene una opción correcta") from exc
