"""Router del módulo transversal de administración y moderación."""

from fastapi import APIRouter, Depends, Query, status

from core.database import get_db
from core.deps import require_role
from schemas.admin import (
    BloqueAdminCreate,
    BloqueAdminOut,
    BloqueAdminUpdate,
    EstadoReporteUpdate,
    OpcionAdminCreate,
    OpcionAdminOut,
    OpcionAdminUpdate,
    PreguntaAdminCreate,
    PreguntaAdminOut,
    PreguntaAdminUpdate,
    PublicacionUpdate,
    ReporteAdminOut,
    TemaAdminCreate,
    TemaAdminDetalleOut,
    TemaAdminOut,
    TemaAdminUpdate,
)
from services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/reportes", response_model=list[ReporteAdminOut])
def listar_reportes(
    estado: str | None = Query(None),
    perfil=Depends(require_role("moderador", "admin")),
    conn=Depends(get_db),
):
    """Lista reportes para moderación, con filtro opcional por estado."""
    return admin_service.listar_reportes(conn, estado)


@router.patch(
    "/reportes/{reporte_id}/estado", response_model=ReporteAdminOut
)
def cambiar_estado_reporte(
    reporte_id: int,
    body: EstadoReporteUpdate,
    perfil=Depends(require_role("moderador", "admin")),
    conn=Depends(get_db),
):
    """Modera un reporte pendiente y registra el cambio."""
    return admin_service.cambiar_estado_reporte(
        conn, reporte_id, body.estado, perfil
    )


@router.get("/temas", response_model=list[TemaAdminOut])
def listar_temas(
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Lista todos los temas, publicados o no."""
    return admin_service.listar_temas(conn)


@router.get("/temas/{tema_id}", response_model=TemaAdminDetalleOut)
def obtener_detalle_tema(
    tema_id: int,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Devuelve un tema con sus bloques y preguntas."""
    return admin_service.obtener_detalle_tema(conn, tema_id)


@router.post(
    "/temas",
    response_model=TemaAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_tema(
    body: TemaAdminCreate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Crea un tema no publicado."""
    return admin_service.crear_tema(conn, body)


@router.patch("/temas/{tema_id}", response_model=TemaAdminOut)
def actualizar_tema(
    tema_id: int,
    body: TemaAdminUpdate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Edita un tema."""
    return admin_service.actualizar_tema(conn, tema_id, body)


@router.patch("/temas/{tema_id}/publicacion", response_model=TemaAdminOut)
def cambiar_publicacion(
    tema_id: int,
    body: PublicacionUpdate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Publica o despublica un tema."""
    return admin_service.cambiar_publicacion(conn, tema_id, body.publicado)


@router.post(
    "/temas/{tema_id}/bloques",
    response_model=BloqueAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_bloque(
    tema_id: int,
    body: BloqueAdminCreate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Crea un bloque dentro de un tema."""
    return admin_service.crear_bloque(conn, tema_id, body)


@router.patch("/bloques/{bloque_id}", response_model=BloqueAdminOut)
def actualizar_bloque(
    bloque_id: int,
    body: BloqueAdminUpdate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Edita un bloque."""
    return admin_service.actualizar_bloque(conn, bloque_id, body)


@router.post(
    "/temas/{tema_id}/preguntas",
    response_model=PreguntaAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_pregunta(
    tema_id: int,
    body: PreguntaAdminCreate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Crea una pregunta para un tema."""
    return admin_service.crear_pregunta(conn, tema_id, body)


@router.patch("/preguntas/{pregunta_id}", response_model=PreguntaAdminOut)
def actualizar_pregunta(
    pregunta_id: int,
    body: PreguntaAdminUpdate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Edita una pregunta."""
    return admin_service.actualizar_pregunta(conn, pregunta_id, body)


@router.post(
    "/preguntas/{pregunta_id}/opciones",
    response_model=OpcionAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_opcion(
    pregunta_id: int,
    body: OpcionAdminCreate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Crea una opción para una pregunta."""
    return admin_service.crear_opcion(conn, pregunta_id, body)


@router.patch("/opciones/{opcion_id}", response_model=OpcionAdminOut)
def actualizar_opcion(
    opcion_id: int,
    body: OpcionAdminUpdate,
    perfil=Depends(require_role("admin")),
    conn=Depends(get_db),
):
    """Edita una opción."""
    return admin_service.actualizar_opcion(conn, opcion_id, body)
