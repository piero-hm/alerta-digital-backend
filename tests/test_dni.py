"""Pruebas del endpoint público de DNI y de la caché del proveedor."""

import time

import pytest

from core.exceptions import DniNoEncontrado, ServicioExternoNoDisponible
from services import dni_service

DNI = {
    "dni": "42948117",
    "nombres": "JOSE WILLIANS",
    "apellido_paterno": "NAVARRO",
    "apellido_materno": "YOVERA",
}


@pytest.fixture(autouse=True)
def limpiar_cache():
    dni_service._cache.clear()
    yield
    dni_service._cache.clear()


def test_consultar_dni_publico(client, monkeypatch):
    monkeypatch.setattr(dni_service, "_consultar_proveedor", lambda numero: dict(DNI))

    respuesta = client.get("/api/v1/dni/42948117")

    assert respuesta.status_code == 200
    assert respuesta.json() == DNI


def test_dni_con_formato_invalido(client):
    respuesta = client.get("/api/v1/dni/123")

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "DNI_INVALIDO"


def test_dni_no_encontrado(client, monkeypatch):
    def _no_encontrado(numero):
        raise DniNoEncontrado("DNI no encontrado")

    monkeypatch.setattr(dni_service, "_consultar_proveedor", _no_encontrado)

    respuesta = client.get("/api/v1/dni/42948117")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "DNI_NO_ENCONTRADO"


def test_proveedor_no_disponible(client, monkeypatch):
    def _falla(numero):
        raise ServicioExternoNoDisponible("No se pudo consultar el DNI")

    monkeypatch.setattr(dni_service, "_consultar_proveedor", _falla)

    respuesta = client.get("/api/v1/dni/42948117")

    assert respuesta.status_code == 503
    assert respuesta.json()["code"] == "SERVICIO_EXTERNO_NO_DISPONIBLE"


def test_consulta_exitosa_se_cachea(monkeypatch):
    llamadas = []

    def _proveedor(numero):
        llamadas.append(numero)
        return dict(DNI)

    monkeypatch.setattr(dni_service, "_consultar_proveedor", _proveedor)

    assert dni_service.consultar_dni("42948117") == DNI
    assert dni_service.consultar_dni("42948117") == DNI
    assert llamadas == ["42948117"]


def test_error_del_proveedor_no_se_cachea(monkeypatch):
    llamadas = []

    def _proveedor(numero):
        llamadas.append(numero)
        raise DniNoEncontrado("DNI no encontrado")

    monkeypatch.setattr(dni_service, "_consultar_proveedor", _proveedor)

    with pytest.raises(DniNoEncontrado):
        dni_service.consultar_dni("42948117")
    with pytest.raises(DniNoEncontrado):
        dni_service.consultar_dni("42948117")

    assert llamadas == ["42948117", "42948117"]


def test_normaliza_respuesta_camel_case(monkeypatch):
    class _Respuesta:
        status_code = 200

        def json(self):
            return {
                "dni": "42948117",
                "nombres": "JOSE WILLIANS",
                "apellidoPaterno": "NAVARRO",
                "apellidoMaterno": "YOVERA",
                "codVerifica": "7",
            }

    monkeypatch.setattr(dni_service.httpx, "get", lambda *args, **kwargs: _Respuesta())

    assert dni_service._consultar_proveedor("42948117") == DNI


def test_proveedor_responde_404(monkeypatch):
    class _Respuesta:
        status_code = 404

    monkeypatch.setattr(dni_service.httpx, "get", lambda *args, **kwargs: _Respuesta())

    with pytest.raises(DniNoEncontrado):
        dni_service._consultar_proveedor("42948117")


def test_proveedor_responde_success_false(monkeypatch):
    class _Respuesta:
        status_code = 200

        def json(self):
            return {"success": False, "message": "DNI no encontrado"}

    monkeypatch.setattr(dni_service.httpx, "get", lambda *args, **kwargs: _Respuesta())

    with pytest.raises(DniNoEncontrado):
        dni_service._consultar_proveedor("42948117")


def test_cache_expirada_consulta_de_nuevo(monkeypatch):
    llamadas = []

    def _proveedor(numero):
        llamadas.append(numero)
        return dict(DNI)

    monkeypatch.setattr(dni_service, "_consultar_proveedor", _proveedor)
    dni_service._cache["42948117"] = (time.monotonic() - 1, dict(DNI))

    assert dni_service.consultar_dni("42948117") == DNI
    assert llamadas == ["42948117"]


def test_sin_token_configurado(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        dni_service,
        "get_settings",
        lambda: SimpleNamespace(
            dni_api_token="", dni_api_url="https://dniruc.apisperu.com/api/v1/dni"
        ),
    )

    with pytest.raises(ServicioExternoNoDisponible):
        dni_service._consultar_proveedor("42948117")
