"""Consultas SQL del módulo transversal de administración."""

from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

_REPORTE_ADMIN_SELECT = """
    SELECT
        r.id,
        r.usuario_id,
        u.email,
        r.estado_id,
        e.nombre AS estado,
        tf.nombre AS tipo_fraude,
        c.nombre AS canal,
        d.nombre AS departamento,
        r.descripcion,
        r.monto_afectado,
        r.fecha_incidente,
        r.evidencia_url,
        r.creado_en
    FROM public.reporte AS r
    JOIN public.usuario AS u ON u.id = r.usuario_id
    JOIN public.tipo_fraude AS tf ON tf.id = r.tipo_fraude_id
    JOIN public.canal AS c ON c.id = r.canal_id
    JOIN public.departamento AS d ON d.id = r.departamento_id
    JOIN public.estado_reporte AS e ON e.id = r.estado_id
"""

_TEMA_COLUMNS = "id, slug, titulo, resumen, publico_objetivo, publicado"
_BLOQUE_COLUMNS = "id, tema_id, orden, tipo, contenido, recurso_url"
_PREGUNTA_COLUMNS = (
    "id, tema_id, enunciado, mensaje_simulado, explicacion, activa"
)
_OPCION_COLUMNS = "id, pregunta_id, texto, es_correcta"


def listar_reportes(
    conn: Connection, estado: str | None
) -> list[dict[str, Any]]:
    """Lista reportes para moderación, con filtro opcional por estado."""
    sql = _REPORTE_ADMIN_SELECT
    params: tuple[Any, ...] = ()
    if estado is not None:
        sql += " WHERE e.nombre = %s"
        params = (estado,)
    sql += " ORDER BY r.creado_en DESC, r.id DESC"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def obtener_reporte_admin(
    conn: Connection, reporte_id: int
) -> dict[str, Any] | None:
    """Busca un reporte con datos de usuario y catálogos."""
    sql = _REPORTE_ADMIN_SELECT + " WHERE r.id = %s"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (reporte_id,))
        return cur.fetchone()


def obtener_estado_id(conn: Connection, nombre: str) -> int | None:
    """Busca el id de un estado por su nombre."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM public.estado_reporte WHERE nombre = %s", (nombre,)
        )
        fila = cur.fetchone()
        return fila[0] if fila else None


def actualizar_estado_reporte(
    conn: Connection,
    reporte_id: int,
    estado_id: int,
    estado_actual_id: int,
) -> dict[str, Any] | None:
    """Cambia el estado solo si el reporte sigue en el estado esperado."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE public.reporte
            SET estado_id = %s
            WHERE id = %s AND estado_id = %s
            """,
            (estado_id, reporte_id, estado_actual_id),
        )
        if cur.rowcount == 0:
            return None
    return obtener_reporte_admin(conn, reporte_id)


def listar_temas_admin(conn: Connection) -> list[dict[str, Any]]:
    """Lista todos los temas, publicados o no."""
    sql = f"SELECT {_TEMA_COLUMNS} FROM public.tema ORDER BY id"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql)
        return cur.fetchall()


def obtener_tema_admin(
    conn: Connection, tema_id: int
) -> dict[str, Any] | None:
    """Busca un tema por id."""
    sql = f"SELECT {_TEMA_COLUMNS} FROM public.tema WHERE id = %s"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchone()


def existe_slug(
    conn: Connection, slug: str, excluir_id: int | None = None
) -> bool:
    """Indica si el slug ya está usado por otro tema."""
    if excluir_id is None:
        sql = "SELECT 1 FROM public.tema WHERE slug = %s"
        params = (slug,)
    else:
        sql = "SELECT 1 FROM public.tema WHERE slug = %s AND id <> %s"
        params = (slug, excluir_id)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None


def crear_tema(
    conn: Connection,
    *,
    slug: str,
    titulo: str,
    resumen: str | None,
    publico_objetivo: str,
) -> dict[str, Any]:
    """Crea un tema no publicado."""
    sql = f"""
        INSERT INTO public.tema (
            slug, titulo, resumen, publico_objetivo, publicado
        )
        VALUES (%s, %s, %s, %s, false)
        RETURNING {_TEMA_COLUMNS}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (slug, titulo, resumen, publico_objetivo))
        return cur.fetchone()


def _actualizar_tabla(
    conn: Connection,
    tabla: str,
    columnas_permitidas: set[str],
    fila_id: int,
    campos: dict[str, Any],
    columnas_salida: str,
) -> dict[str, Any] | None:
    """Actualiza columnas whitelisteadas de una tabla."""
    asignaciones = []
    valores = []
    for columna, valor in campos.items():
        if columna in columnas_permitidas:
            asignaciones.append(f"{columna} = %s")
            valores.append(valor)
    if not asignaciones:
        return None
    valores.append(fila_id)
    sql = (
        f"UPDATE public.{tabla} SET {', '.join(asignaciones)} "
        f"WHERE id = %s RETURNING {columnas_salida}"
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, tuple(valores))
        return cur.fetchone()


def actualizar_tema(
    conn: Connection, tema_id: int, campos: dict[str, Any]
) -> dict[str, Any] | None:
    """Actualiza campos permitidos de un tema."""
    return _actualizar_tabla(
        conn,
        "tema",
        {"slug", "titulo", "resumen", "publico_objetivo"},
        tema_id,
        campos,
        _TEMA_COLUMNS,
    )


def actualizar_publicacion(
    conn: Connection, tema_id: int, publicado: bool
) -> dict[str, Any] | None:
    """Publica o despublica un tema."""
    sql = f"""
        UPDATE public.tema
        SET publicado = %s
        WHERE id = %s
        RETURNING {_TEMA_COLUMNS}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (publicado, tema_id))
        return cur.fetchone()


def listar_bloques(
    conn: Connection, tema_id: int
) -> list[dict[str, Any]]:
    """Lista los bloques de un tema ordenados por orden."""
    sql = f"""
        SELECT {_BLOQUE_COLUMNS}
        FROM public.bloque
        WHERE tema_id = %s
        ORDER BY orden, id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()


def obtener_bloque(
    conn: Connection, bloque_id: int
) -> dict[str, Any] | None:
    """Busca un bloque por id."""
    sql = f"SELECT {_BLOQUE_COLUMNS} FROM public.bloque WHERE id = %s"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (bloque_id,))
        return cur.fetchone()


def existe_orden_bloque(
    conn: Connection,
    tema_id: int,
    orden: int,
    excluir_id: int | None = None,
) -> bool:
    """Indica si el orden ya está usado en el tema."""
    if excluir_id is None:
        sql = "SELECT 1 FROM public.bloque WHERE tema_id = %s AND orden = %s"
        params = (tema_id, orden)
    else:
        sql = """
            SELECT 1 FROM public.bloque
            WHERE tema_id = %s AND orden = %s AND id <> %s
        """
        params = (tema_id, orden, excluir_id)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None


def crear_bloque(
    conn: Connection,
    *,
    tema_id: int,
    orden: int,
    tipo: str,
    contenido: str | None,
    recurso_url: str | None,
) -> dict[str, Any]:
    """Crea un bloque dentro de un tema."""
    sql = f"""
        INSERT INTO public.bloque (
            tema_id, orden, tipo, contenido, recurso_url
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING {_BLOQUE_COLUMNS}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql, (tema_id, orden, tipo, contenido, recurso_url)
        )
        return cur.fetchone()


def actualizar_bloque(
    conn: Connection, bloque_id: int, campos: dict[str, Any]
) -> dict[str, Any] | None:
    """Actualiza campos permitidos de un bloque."""
    return _actualizar_tabla(
        conn,
        "bloque",
        {"orden", "tipo", "contenido", "recurso_url"},
        bloque_id,
        campos,
        _BLOQUE_COLUMNS,
    )


def listar_preguntas_admin(
    conn: Connection, tema_id: int
) -> list[dict[str, Any]]:
    """Lista las preguntas de un tema."""
    sql = f"""
        SELECT {_PREGUNTA_COLUMNS}
        FROM public.pregunta
        WHERE tema_id = %s
        ORDER BY id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()


def listar_opciones_admin(
    conn: Connection, tema_id: int
) -> list[dict[str, Any]]:
    """Lista las opciones de todas las preguntas de un tema."""
    sql = f"""
        SELECT o.id, o.pregunta_id, o.texto, o.es_correcta
        FROM public.opcion AS o
        JOIN public.pregunta AS p ON p.id = o.pregunta_id
        WHERE p.tema_id = %s
        ORDER BY o.pregunta_id, o.id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (tema_id,))
        return cur.fetchall()


def listar_opciones_por_pregunta(
    conn: Connection, pregunta_id: int
) -> list[dict[str, Any]]:
    """Lista las opciones de una pregunta."""
    sql = f"""
        SELECT {_OPCION_COLUMNS}
        FROM public.opcion
        WHERE pregunta_id = %s
        ORDER BY id
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (pregunta_id,))
        return cur.fetchall()


def obtener_pregunta(
    conn: Connection, pregunta_id: int
) -> dict[str, Any] | None:
    """Busca una pregunta por id."""
    sql = f"SELECT {_PREGUNTA_COLUMNS} FROM public.pregunta WHERE id = %s"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (pregunta_id,))
        return cur.fetchone()


def crear_pregunta(
    conn: Connection,
    *,
    tema_id: int,
    enunciado: str,
    mensaje_simulado: str | None,
    explicacion: str,
    activa: bool,
) -> dict[str, Any]:
    """Crea una pregunta para un tema."""
    sql = f"""
        INSERT INTO public.pregunta (
            tema_id, enunciado, mensaje_simulado, explicacion, activa
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING {_PREGUNTA_COLUMNS}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            sql,
            (tema_id, enunciado, mensaje_simulado, explicacion, activa),
        )
        return cur.fetchone()


def actualizar_pregunta(
    conn: Connection, pregunta_id: int, campos: dict[str, Any]
) -> dict[str, Any] | None:
    """Actualiza campos permitidos de una pregunta."""
    return _actualizar_tabla(
        conn,
        "pregunta",
        {"enunciado", "mensaje_simulado", "explicacion", "activa"},
        pregunta_id,
        campos,
        _PREGUNTA_COLUMNS,
    )


def existe_opcion_correcta(
    conn: Connection, pregunta_id: int, excluir_id: int | None = None
) -> bool:
    """Indica si la pregunta ya tiene otra opción correcta."""
    if excluir_id is None:
        sql = """
            SELECT 1 FROM public.opcion
            WHERE pregunta_id = %s AND es_correcta
        """
        params = (pregunta_id,)
    else:
        sql = """
            SELECT 1 FROM public.opcion
            WHERE pregunta_id = %s AND es_correcta AND id <> %s
        """
        params = (pregunta_id, excluir_id)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None


def crear_opcion(
    conn: Connection,
    *,
    pregunta_id: int,
    texto: str,
    es_correcta: bool,
) -> dict[str, Any]:
    """Crea una opción para una pregunta."""
    sql = f"""
        INSERT INTO public.opcion (pregunta_id, texto, es_correcta)
        VALUES (%s, %s, %s)
        RETURNING {_OPCION_COLUMNS}
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (pregunta_id, texto, es_correcta))
        return cur.fetchone()


def obtener_opcion(
    conn: Connection, opcion_id: int
) -> dict[str, Any] | None:
    """Busca una opción por id."""
    sql = f"SELECT {_OPCION_COLUMNS} FROM public.opcion WHERE id = %s"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (opcion_id,))
        return cur.fetchone()


def actualizar_opcion(
    conn: Connection, opcion_id: int, campos: dict[str, Any]
) -> dict[str, Any] | None:
    """Actualiza campos permitidos de una opción."""
    return _actualizar_tabla(
        conn,
        "opcion",
        {"texto", "es_correcta"},
        opcion_id,
        campos,
        _OPCION_COLUMNS,
    )
