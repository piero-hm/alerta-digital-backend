"""Router del módulo transversal de dashboard."""

from fastapi import APIRouter, Depends

from core.database import get_db
from schemas.dashboard import (
    ReporteMensualOut,
    ReportesDepartamentoOut,
    TopEstafaOut,
)
from services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/top-estafas", response_model=list[TopEstafaOut])
def top_estafas(conn=Depends(get_db)):
    """Tipos de fraude con más reportes validados."""
    return dashboard_service.top_estafas(conn)


@router.get(
    "/por-departamento", response_model=list[ReportesDepartamentoOut]
)
def reportes_por_departamento(conn=Depends(get_db)):
    """Reportes validados agrupados por departamento."""
    return dashboard_service.reportes_por_departamento(conn)


@router.get("/mensual", response_model=list[ReporteMensualOut])
def reportes_mensuales(conn=Depends(get_db)):
    """Reportes validados agrupados por mes."""
    return dashboard_service.reportes_mensuales(conn)
