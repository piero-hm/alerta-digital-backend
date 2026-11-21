"""Reglas de negocio del módulo Reportar."""

from typing import Any

from core.exceptions import ErrorInterno, Validacion
from repositories import reportar_repository
from schemas.reportar import ReporteCreate

ESTADO_INICIAL = "pendiente"


def _validar_catalogos(conn, datos: ReporteCreate) -> None:
    """Comprueba que los ids de catálogo enviados existan."""
    if not reportar_repository.existe_tipo_fraude(conn, datos.tipo_fraude_id):
        raise Validacion("El tipo de fraude no existe")
    if not reportar_repository.existe_canal(conn, datos.canal_id):
        raise Validacion("El canal no existe")
    if not reportar_repository.existe_departamento(
        conn, datos.departamento_id
    ):
        raise Validacion("El departamento no existe")


def crear_reporte(
    conn, usuario_id: str, datos: ReporteCreate
) -> dict[str, Any]:
    """Valida catálogos y crea el reporte con estado pendiente."""
    _validar_catalogos(conn, datos)

    estado_id = reportar_repository.obtener_estado_id(conn, ESTADO_INICIAL)
    if estado_id is None:
        raise ErrorInterno("No se encontró el estado inicial del reporte")

    return reportar_repository.crear_reporte(
        conn,
        usuario_id=usuario_id,
        tipo_fraude_id=datos.tipo_fraude_id,
        canal_id=datos.canal_id,
        departamento_id=datos.departamento_id,
        estado_id=estado_id,
        descripcion=datos.descripcion,
        monto_afectado=datos.monto_afectado,
        fecha_incidente=datos.fecha_incidente,
        evidencia_url=datos.evidencia_url,
    )


def listar_mios(conn, usuario_id: str) -> list[dict[str, Any]]:
    """Devuelve los reportes del usuario autenticado."""
    return reportar_repository.listar_reportes_usuario(conn, usuario_id)


def listar_alertas(conn, pagina: int, limite: int) -> dict[str, Any]:
    """Devuelve una página de reportes validados y anonimizados."""
    total = reportar_repository.contar_alertas(conn)
    offset = (pagina - 1) * limite
    alertas = reportar_repository.listar_alertas(conn, limite, offset)
    return {
        "total": total,
        "pagina": pagina,
        "limite": limite,
        "alertas": alertas,
    }
