"""Consultas SQL del módulo Practicar."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def obtener_tema_publicado(conn: Connection, slug: str) -> dict[str, Any] | None:
    """Busca un tema publicado por su slug."""
    sql = """
        SELECT id, slug, titulo
        FROM public.tema
        WHERE slug = %s AND publicado = true
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (slug,))
        return cur.fetchone()


def listar_preguntas_activas(
    conn: Connection, tema_id: int
) -> list[dict[str, Any]]:
    """Lista las preguntas activas de un tema."""
    sql = """
        SELECT id, enunciado, mensaje_simulado
        FROM public.pregunta
        WHERE tema_id = %s AND activa = true
        ORDER BY id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()


def listar_opciones_por_tema(
    conn: Connection, tema_id: int
) -> list[dict[str, Any]]:
    """Lista las opciones de las preguntas activas de un tema."""
    sql = """
        SELECT o.id, o.pregunta_id, o.texto
        FROM public.opcion AS o
        JOIN public.pregunta AS p ON p.id = o.pregunta_id
        WHERE p.tema_id = %s AND p.activa = true
        ORDER BY o.pregunta_id, o.id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()


def obtener_opcion_para_responder(
    conn: Connection, opcion_id: int
) -> dict[str, Any] | None:
    """Busca una opción de una pregunta activa de un tema publicado."""
    sql = """
        SELECT o.id, o.es_correcta, p.explicacion
        FROM public.opcion AS o
        JOIN public.pregunta AS p ON p.id = o.pregunta_id
        JOIN public.tema AS t ON t.id = p.tema_id
        WHERE o.id = %s AND p.activa = true AND t.publicado = true
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (opcion_id,))
        return cur.fetchone()


def guardar_respuesta(
    conn: Connection, usuario_id: str, opcion_id: int
) -> None:
    """Inserta una nueva respuesta, conservando el historial."""
    sql = """
        INSERT INTO public.respuesta_usuario (usuario_id, opcion_id)
        VALUES (%s::uuid, %s)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (usuario_id, opcion_id))


def obtener_progreso(
    conn: Connection, usuario_id: str
) -> list[dict[str, Any]]:
    """Obtiene el progreso del usuario en los temas publicados."""
    sql = """
        SELECT
            v.tema_id,
            v.slug,
            t.titulo,
            v.total_preguntas,
            v.correctas
        FROM public.v_progreso_tema AS v
        JOIN public.tema AS t ON t.id = v.tema_id
        WHERE v.usuario_id = %s::uuid AND t.publicado = true
        ORDER BY v.tema_id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchall()
