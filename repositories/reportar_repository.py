"""Consultas SQL del módulo Reportar."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def existe_tipo_fraude(conn: Connection, tipo_fraude_id: int) -> bool:
    """Indica si el tipo de fraude existe."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM public.tipo_fraude WHERE id = %s", (tipo_fraude_id,)
        )
        return cur.fetchone() is not None


def existe_canal(conn: Connection, canal_id: int) -> bool:
    """Indica si el canal existe."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM public.canal WHERE id = %s", (canal_id,))
        return cur.fetchone() is not None


def existe_departamento(conn: Connection, departamento_id: int) -> bool:
    """Indica si el departamento existe."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM public.departamento WHERE id = %s",
            (departamento_id,),
        )
        return cur.fetchone() is not None


def obtener_estado_id(conn: Connection, nombre: str) -> int | None:
    """Busca el id de un estado por su nombre (no se asumen ids)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM public.estado_reporte WHERE nombre = %s", (nombre,)
        )
        fila = cur.fetchone()
        return fila[0] if fila else None


def crear_reporte(
    conn: Connection,
    *,
    usuario_id: str,
    tipo_fraude_id: int,
    canal_id: int,
    departamento_id: int,
    estado_id: int,
    descripcion: str,
    monto_afectado,
    fecha_incidente,
    evidencia_url: str | None,
) -> dict[str, Any]:
    """Inserta el reporte y devuelve sus datos con nombres de catálogo."""
    sql = """
        WITH nuevo AS (
            INSERT INTO public.reporte (
                usuario_id, tipo_fraude_id, canal_id, departamento_id,
                estado_id, descripcion, monto_afectado, fecha_incidente,
                evidencia_url
            )
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        )
        SELECT
            n.id,
            tf.nombre AS tipo_fraude,
            c.nombre AS canal,
            d.nombre AS departamento,
            e.nombre AS estado,
            n.descripcion,
            n.monto_afectado,
            n.fecha_incidente,
            n.evidencia_url,
            n.creado_en
        FROM nuevo AS n
        JOIN public.tipo_fraude AS tf ON tf.id = n.tipo_fraude_id
        JOIN public.canal AS c ON c.id = n.canal_id
        JOIN public.departamento AS d ON d.id = n.departamento_id
        JOIN public.estado_reporte AS e ON e.id = n.estado_id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql,
            (
                usuario_id,
                tipo_fraude_id,
                canal_id,
                departamento_id,
                estado_id,
                descripcion,
                monto_afectado,
                fecha_incidente,
                evidencia_url,
            ),
        )
        return cur.fetchone()


def listar_reportes_usuario(
    conn: Connection, usuario_id: str
) -> list[dict[str, Any]]:
    """Lista los reportes del usuario con su estado."""
    sql = """
        SELECT
            r.id,
            tf.nombre AS tipo_fraude,
            c.nombre AS canal,
            d.nombre AS departamento,
            e.nombre AS estado,
            r.descripcion,
            r.monto_afectado,
            r.fecha_incidente,
            r.evidencia_url,
            r.creado_en
        FROM public.reporte AS r
        JOIN public.tipo_fraude AS tf ON tf.id = r.tipo_fraude_id
        JOIN public.canal AS c ON c.id = r.canal_id
        JOIN public.departamento AS d ON d.id = r.departamento_id
        JOIN public.estado_reporte AS e ON e.id = r.estado_id
        WHERE r.usuario_id = %s::uuid
        ORDER BY r.creado_en DESC, r.id DESC
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchall()


def contar_alertas(conn: Connection) -> int:
    """Cuenta los reportes validados."""
    sql = """
        SELECT count(*) AS total
        FROM public.reporte AS r
        JOIN public.estado_reporte AS e ON e.id = r.estado_id
        WHERE e.nombre = 'validado'
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchone()["total"]


def listar_alertas(
    conn: Connection, limite: int, offset: int
) -> list[dict[str, Any]]:
    """Lista reportes validados y anonimizados, paginados."""
    sql = """
        SELECT
            tf.nombre AS tipo_fraude,
            c.nombre AS canal,
            d.nombre AS departamento,
            r.fecha_incidente,
            r.descripcion
        FROM public.reporte AS r
        JOIN public.tipo_fraude AS tf ON tf.id = r.tipo_fraude_id
        JOIN public.canal AS c ON c.id = r.canal_id
        JOIN public.departamento AS d ON d.id = r.departamento_id
        JOIN public.estado_reporte AS e ON e.id = r.estado_id
        WHERE e.nombre = 'validado'
        ORDER BY r.creado_en DESC, r.id DESC
        LIMIT %s OFFSET %s
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (limite, offset))
        return cur.fetchall()
