"""Router del módulo Aprender."""

from fastapi import APIRouter, Depends, Query

from core.database import get_db
from schemas.aprender import PublicoObjetivo, TemaDetalle, TemaResumen
from services import aprender_service

router = APIRouter(prefix="/aprender", tags=["Aprender"])


@router.get("/temas", response_model=list[TemaResumen])
def listar_temas(
    publico_objetivo: PublicoObjetivo | None = Query(default=None),
    conn=Depends(get_db),
):
    """Lista los temas publicados."""
    return aprender_service.listar_temas(conn, publico_objetivo)


@router.get("/temas/{slug}", response_model=TemaDetalle)
def obtener_tema(slug: str, conn=Depends(get_db)):
    """Devuelve un tema publicado con sus bloques ordenados."""
    return aprender_service.obtener_tema(conn, slug)
