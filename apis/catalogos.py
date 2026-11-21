"""Router del módulo transversal de catálogos."""

from fastapi import APIRouter, Depends

from core.database import get_db
from schemas.catalogos import CatalogosOut
from services import catalogos_service

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get("", response_model=CatalogosOut)
def obtener_catalogos(conn=Depends(get_db)):
    """Devuelve departamentos, tipos de fraude y canales."""
    return catalogos_service.obtener_catalogos(conn)
