"""Router del módulo Reportar."""

from fastapi import APIRouter, Depends, Query, status

from core.database import get_db
from core.deps import get_current_profile, require_role
from schemas.reportar import AlertasPageOut, ReporteCreate, ReporteOut
from services import reportar_service

router = APIRouter(prefix="/reportar", tags=["Reportar"])


@router.post("", response_model=ReporteOut, status_code=status.HTTP_201_CREATED)
def crear_reporte(
    body: ReporteCreate,
    perfil=Depends(require_role("ciudadano")),
    conn=Depends(get_db),
):
    """Crea un reporte de estafa con estado pendiente."""
    return reportar_service.crear_reporte(conn, perfil["id"], body)


@router.get("/mios", response_model=list[ReporteOut])
def listar_mios(
    perfil=Depends(get_current_profile),
    conn=Depends(get_db),
):
    """Lista los reportes del usuario autenticado con su estado."""
    return reportar_service.listar_mios(conn, perfil["id"])


@router.get("/alertas", response_model=AlertasPageOut)
def listar_alertas(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    """Lista reportes validados y anonimizados, paginados."""
    return reportar_service.listar_alertas(conn, pagina, limite)
