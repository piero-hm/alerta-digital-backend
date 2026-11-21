"""Consultas SQL del módulo transversal de catálogos."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def listar_departamentos(conn: Connection) -> list[dict[str, Any]]:
    """Lista los departamentos ordenados por nombre."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id, nombre FROM public.departamento ORDER BY nombre")
        return cur.fetchall()


def listar_tipos_fraude(conn: Connection) -> list[dict[str, Any]]:
    """Lista los tipos de fraude ordenados por nombre."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id, nombre FROM public.tipo_fraude ORDER BY nombre")
        return cur.fetchall()


def listar_canales(conn: Connection) -> list[dict[str, Any]]:
    """Lista los canales ordenados por nombre."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id, nombre FROM public.canal ORDER BY nombre")
        return cur.fetchall()
