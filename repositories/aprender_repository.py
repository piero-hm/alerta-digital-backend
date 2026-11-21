"""Consultas SQL del módulo Aprender."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def listar_temas_publicados(
    conn: Connection, publico_objetivo: str | None = None
) -> list[dict[str, Any]]:
    """Lista temas publicados, opcionalmente filtrados por público objetivo."""
    sql = """
        SELECT id, slug, titulo, resumen, publico_objetivo
        FROM public.tema
        WHERE publicado = true
    """
    params: list[Any] = []
    if publico_objetivo is not None:
        sql += " AND (publico_objetivo = %s OR publico_objetivo = 'todos')"
        params.append(publico_objetivo)
    sql += " ORDER BY id"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def obtener_tema_publicado(conn: Connection, slug: str) -> dict[str, Any] | None:
    """Busca un tema publicado por su slug."""
    sql = """
        SELECT id, slug, titulo, resumen, publico_objetivo
        FROM public.tema
        WHERE slug = %s AND publicado = true
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (slug,))
        return cur.fetchone()


def listar_bloques(conn: Connection, tema_id: int) -> list[dict[str, Any]]:
    """Lista los bloques de un tema ordenados por 'orden'."""
    sql = """
        SELECT id, orden, tipo, contenido, recurso_url
        FROM public.bloque
        WHERE tema_id = %s
        ORDER BY orden
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()
