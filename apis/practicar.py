"""Router del módulo Practicar."""

from fastapi import APIRouter, Depends

from core.database import get_db
from core.deps import get_current_profile
from schemas.practicar import (
    EnlaceCreate,
    EnlaceOut,
    PreguntaOut,
    ProgresoTemaOut,
    RespuestaCreate,
    RespuestaOut,
)
from services import enlaces_service, practicar_service

router = APIRouter(prefix="/practicar", tags=["Practicar"])


@router.get("/temas/{slug}/preguntas", response_model=list[PreguntaOut])
def obtener_preguntas(slug: str, conn=Depends(get_db)):
    """Lista las preguntas activas de un tema, sin revelar la correcta."""
    return practicar_service.obtener_preguntas(conn, slug)


@router.post("/responder", response_model=RespuestaOut)
def responder(
    body: RespuestaCreate,
    perfil=Depends(get_current_profile),
    conn=Depends(get_db),
):
    """Guarda una respuesta y devuelve si era correcta y su explicación."""
    return practicar_service.responder(conn, perfil["id"], body.opcion_id)


@router.get("/progreso/me", response_model=list[ProgresoTemaOut])
def obtener_progreso(
    perfil=Depends(get_current_profile),
    conn=Depends(get_db),
):
    """Devuelve el progreso del usuario autenticado por tema."""
    return practicar_service.obtener_progreso(conn, perfil["id"])


@router.post("/verificar-enlace", response_model=EnlaceOut)
def verificar_enlace(body: EnlaceCreate):
    """Verifica una URL con Safe Browsing y heurísticas básicas."""
    return {"resultado": enlaces_service.verificar_enlace(str(body.url))}
