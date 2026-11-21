"""Routers transversales de autenticación y DNI."""

from fastapi import APIRouter, Depends, status

from core.database import get_db
from core.deps import get_current_profile, get_current_user
from schemas.auth import DniOut, PerfilCreate, PerfilOut
from services import dni_service, perfil_service

router = APIRouter(prefix="/auth", tags=["Auth"])
router_dni = APIRouter(prefix="/dni", tags=["DNI"])


@router_dni.get("/{numero}", response_model=DniOut)
def consultar_dni(numero: str):
    """Consulta los datos de una persona por DNI (público)."""
    return dni_service.consultar_dni(numero)


@router.post("/perfil", response_model=PerfilOut, status_code=status.HTTP_201_CREATED)
def crear_perfil(
    body: PerfilCreate,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Crea el perfil del usuario autenticado consultando su DNI."""
    return perfil_service.crear_perfil(
        conn,
        usuario_id=user["sub"],
        email=user.get("email"),
        dni=body.dni,
        acepto_datos=body.acepto_datos,
    )


@router.get("/me", response_model=PerfilOut)
def obtener_mi_perfil(perfil=Depends(get_current_profile)):
    """Devuelve el perfil del usuario autenticado y su rol."""
    return perfil
