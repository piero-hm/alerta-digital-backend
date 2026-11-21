"""Consultas SQL del módulo transversal de dashboard."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def top_estafas(conn: Connection) -> list[dict[str, Any]]:
    """Tipos de fraude con más reportes validados."""
    sql = """
        SELECT tipo_fraude, total
        FROM public.v_top_estafas
        ORDER BY total DESC, tipo_fraude
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchall()


def reportes_por_departamento(conn: Connection) -> list[dict[str, Any]]:
    """Reportes validados agrupados por departamento."""
    sql = """
        SELECT departamento, total
        FROM public.v_reportes_departamento
        ORDER BY total DESC, departamento
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchall()


def reportes_mensuales(conn: Connection) -> list[dict[str, Any]]:
    """Reportes validados agrupados por mes."""
    sql = """
        SELECT mes, total, monto_afectado
        FROM public.v_reportes_mensual
        ORDER BY mes
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchall()
