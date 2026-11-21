"""Pruebas de los endpoints de perfil (auth)."""

import pytest

from core.deps import get_current_profile, get_current_user
from core.exceptions import DniNoEncontrado, ServicioExternoNoDisponible
from main import app
from repositories import usuario_repository
from services import dni_service

USUARIO = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "email": "persona@ejemplo.com",
}

DNI = {
    "dni": "42948117",
    "nombres": "JOSE WILLIANS",
    "apellido_paterno": "NAVARRO",
    "apellido_materno": "YOVERA",
}

PERFIL = {
    "id": "11111111-1111-1111-1111-111111111111",
    "dni": "42948117",
    "nombres": "JOSE WILLIANS",
    "apellido_paterno": "NAVARRO",
    "apellido_materno": "YOVERA",
    "email": "persona@ejemplo.com",
    "rol": "ciudadano",
    "activo": True,
    "acepto_datos_en": "2026-11-19T12:00:00Z",
    "creado_en": "2026-11-19T12:00:00Z",
}


@pytest.fixture
def autenticado():
    app.dependency_overrides[get_current_user] = lambda: dict(USUARIO)
    yield
    app.dependency_overrides.pop(get_current_user, None)


def _sin_perfil(monkeypatch):
    monkeypatch.setattr(usuario_repository, "obtener_perfil", lambda conn, uid: None)


def _dni_valido(monkeypatch):
    monkeypatch.setattr(dni_service, "consultar_dni", lambda dni: dict(DNI))


def test_crear_perfil(client, autenticado, monkeypatch):
    _sin_perfil(monkeypatch)
    monkeypatch.setattr(usuario_repository, "existe_dni", lambda conn, dni: False)
    monkeypatch.setattr(usuario_repository, "obtener_rol_id", lambda conn, nombre: 1)
    monkeypatch.setattr(
        usuario_repository,
        "crear_usuario",
        lambda conn, **kwargs: dict(PERFIL),
    )
    _dni_valido(monkeypatch)

    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["rol"] == "ciudadano"
    assert respuesta.json()["dni"] == "42948117"


def test_crear_perfil_sin_aceptar_datos(client, autenticado):
    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": False},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_perfil_con_dni_invalido(client, autenticado):
    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "123", "acepto_datos": True},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_perfil_ya_existente(client, autenticado, monkeypatch):
    monkeypatch.setattr(
        usuario_repository, "obtener_perfil", lambda conn, uid: dict(PERFIL)
    )

    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_crear_perfil_con_dni_repetido(client, autenticado, monkeypatch):
    _sin_perfil(monkeypatch)
    monkeypatch.setattr(usuario_repository, "existe_dni", lambda conn, dni: True)

    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_crear_perfil_con_dni_inexistente(client, autenticado, monkeypatch):
    _sin_perfil(monkeypatch)
    monkeypatch.setattr(usuario_repository, "existe_dni", lambda conn, dni: False)

    def _no_encontrado(dni):
        raise DniNoEncontrado("DNI no encontrado")

    monkeypatch.setattr(dni_service, "consultar_dni", _no_encontrado)

    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "DNI_NO_ENCONTRADO"


def test_crear_perfil_con_proveedor_caido(client, autenticado, monkeypatch):
    _sin_perfil(monkeypatch)
    monkeypatch.setattr(usuario_repository, "existe_dni", lambda conn, dni: False)

    def _falla(dni):
        raise ServicioExternoNoDisponible("No se pudo consultar el DNI")

    monkeypatch.setattr(dni_service, "consultar_dni", _falla)

    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["code"] == "SERVICIO_EXTERNO_NO_DISPONIBLE"


def test_crear_perfil_sin_token(client):
    respuesta = client.post(
        "/api/v1/auth/perfil",
        json={"dni": "42948117", "acepto_datos": True},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_obtener_mi_perfil(client, autenticado, monkeypatch):
    monkeypatch.setattr(
        usuario_repository, "obtener_perfil", lambda conn, uid: dict(PERFIL)
    )

    respuesta = client.get("/api/v1/auth/me")

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "ciudadano"
    assert respuesta.json()["email"] == USUARIO["email"]


def test_obtener_mi_perfil_sin_perfil(client, autenticado, monkeypatch):
    _sin_perfil(monkeypatch)

    respuesta = client.get("/api/v1/auth/me")

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "code": "SIN_PERMISO",
        "detail": "Falta completar el perfil",
    }


def test_obtener_mi_perfil_sin_token(client):
    respuesta = client.get("/api/v1/auth/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"
