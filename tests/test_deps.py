"""Pruebas de las dependencias de autenticación y autorización."""

import pytest

from core import deps
from core.exceptions import NoAutenticado, SinPermiso
from repositories import usuario_repository

USUARIO = {"sub": "11111111-1111-1111-1111-111111111111", "email": "persona@ejemplo.com"}


def test_get_current_user_sin_token():
    with pytest.raises(NoAutenticado):
        deps.get_current_user(credentials=None)


def test_get_current_user_valida_token(monkeypatch):
    monkeypatch.setattr(deps, "validar_token", lambda token: dict(USUARIO))

    class Credenciales:
        credentials = "token-de-prueba"

    assert deps.get_current_user(credentials=Credenciales()) == USUARIO


def test_get_current_profile_sin_fila(monkeypatch):
    monkeypatch.setattr(
        usuario_repository, "obtener_perfil", lambda conn, usuario_id: None
    )

    with pytest.raises(SinPermiso) as error:
        deps.get_current_profile(user=USUARIO, conn=object())

    assert error.value.code == "SIN_PERMISO"
    assert error.value.detail == "Falta completar el perfil"


def test_get_current_profile_con_fila(monkeypatch):
    monkeypatch.setattr(
        usuario_repository,
        "obtener_perfil",
        lambda conn, usuario_id: {"id": usuario_id, "rol": "ciudadano"},
    )

    perfil = deps.get_current_profile(user=USUARIO, conn=object())

    assert perfil["sub"] == USUARIO["sub"]
    assert perfil["rol"] == "ciudadano"


def test_require_role_permite_y_rechaza():
    verificar_admin = deps.require_role("admin")

    with pytest.raises(SinPermiso):
        verificar_admin(perfil={"rol": "ciudadano"})

    assert verificar_admin(perfil={"rol": "admin"})["rol"] == "admin"
