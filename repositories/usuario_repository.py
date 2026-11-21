"""Consultas SQL del usuario (perfil y rol)."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


def obtener_perfil(conn: Connection, usuario_id: str) -> dict[str, Any] | None:
    """Busca la fila del usuario con el nombre de su rol."""
    sql = """
        SELECT
            u.id,
            u.rol_id,
            r.nombre AS rol,
            u.dni,
            u.nombres,
            u.apellido_paterno,
            u.apellido_materno,
            u.email,
            u.acepto_datos_en,
            u.activo,
            u.creado_en
        FROM public.usuario AS u
        JOIN public.rol AS r ON r.id = u.rol_id
        WHERE u.id = %s::uuid
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (usuario_id,))
        return cur.fetchone()


def existe_dni(conn: Connection, dni: str) -> bool:
    """Indica si el DNI ya está registrado."""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM public.usuario WHERE dni = %s", (dni,))
        return cur.fetchone() is not None


def obtener_rol_id(conn: Connection, nombre: str) -> int | None:
    """Busca el id de un rol por su nombre (no se asumen ids)."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM public.rol WHERE nombre = %s", (nombre,))
        fila = cur.fetchone()
        return fila[0] if fila else None


def crear_usuario(
    conn: Connection,
    *,
    usuario_id: str,
    rol_id: int,
    dni: str,
    nombres: str,
    apellido_paterno: str,
    apellido_materno: str | None,
    email: str,
) -> dict[str, Any]:
    """Inserta el usuario y devuelve su perfil con el nombre del rol."""
    sql = """
        WITH nuevo AS (
            INSERT INTO public.usuario (
                id, rol_id, dni, nombres, apellido_paterno,
                apellido_materno, email, acepto_datos_en
            )
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, now())
            RETURNING *
        )
        SELECT
            n.id,
            n.rol_id,
            r.nombre AS rol,
            n.dni,
            n.nombres,
            n.apellido_paterno,
            n.apellido_materno,
            n.email,
            n.acepto_datos_en,
            n.activo,
            n.creado_en
        FROM nuevo AS n
        JOIN public.rol AS r ON r.id = n.rol_id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql,
            (
                usuario_id,
                rol_id,
                dni,
                nombres,
                apellido_paterno,
                apellido_materno,
                email,
            ),
        )
        return cur.fetchone()
