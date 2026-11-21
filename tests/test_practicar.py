"""Pruebas del módulo Practicar y del verificador de enlaces."""

from types import SimpleNamespace

import httpx
import pytest

from core.deps import get_current_profile
from core.exceptions import ServicioExternoNoDisponible
from main import app
from repositories import practicar_repository
from services import enlaces_service

USUARIO_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def autenticado():
    app.dependency_overrides[get_current_profile] = lambda: {
        "id": USUARIO_ID,
        "sub": USUARIO_ID,
        "email": "persona@ejemplo.com",
        "rol": "ciudadano",
    }
    yield
    app.dependency_overrides.pop(get_current_profile, None)


def test_obtener_preguntas_sin_revelar_correcta(client, monkeypatch):
    monkeypatch.setattr(
        practicar_repository,
        "obtener_tema_publicado",
        lambda conn, slug: {"id": 1, "slug": slug, "titulo": "Tema"},
    )
    monkeypatch.setattr(
        practicar_repository,
        "listar_preguntas_activas",
        lambda conn, tema_id: [
            {"id": 10, "enunciado": "¿Qué haces?", "mensaje_simulado": None}
        ],
    )
    monkeypatch.setattr(
        practicar_repository,
        "listar_opciones_por_tema",
        lambda conn, tema_id: [
            {"id": 100, "pregunta_id": 10, "texto": "Opción A"},
            {"id": 101, "pregunta_id": 10, "texto": "Opción B"},
        ],
    )

    respuesta = client.get("/api/v1/practicar/temas/phishing/preguntas")

    assert respuesta.status_code == 200
    pregunta = respuesta.json()[0]
    assert pregunta["opciones"] == [
        {"id": 100, "texto": "Opción A"},
        {"id": 101, "texto": "Opción B"},
    ]
    assert "es_correcta" not in pregunta["opciones"][0]
    assert "explicacion" not in pregunta


def test_obtener_preguntas_tema_inexistente(client, monkeypatch):
    monkeypatch.setattr(
        practicar_repository, "obtener_tema_publicado", lambda conn, slug: None
    )

    respuesta = client.get("/api/v1/practicar/temas/no-existe/preguntas")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_responder_guarda_historial_y_devuelve_resultado(
    client, autenticado, monkeypatch
):
    guardadas = []
    monkeypatch.setattr(
        practicar_repository,
        "obtener_opcion_para_responder",
        lambda conn, opcion_id: {
            "id": opcion_id,
            "es_correcta": True,
            "explicacion": "Muy bien, no compartas tus datos.",
        },
    )
    monkeypatch.setattr(
        practicar_repository,
        "guardar_respuesta",
        lambda conn, usuario_id, opcion_id: guardadas.append(
            (usuario_id, opcion_id)
        ),
    )

    respuesta = client.post(
        "/api/v1/practicar/responder", json={"opcion_id": 100}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "es_correcta": True,
        "explicacion": "Muy bien, no compartas tus datos.",
    }
    assert guardadas == [(USUARIO_ID, 100)]


def test_responder_opcion_inexistente(client, autenticado, monkeypatch):
    monkeypatch.setattr(
        practicar_repository, "obtener_opcion_para_responder", lambda conn, oid: None
    )

    respuesta = client.post(
        "/api/v1/practicar/responder", json={"opcion_id": 999}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_responder_opcion_invalida(client, autenticado):
    respuesta = client.post(
        "/api/v1/practicar/responder", json={"opcion_id": 0}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_responder_sin_token(client):
    respuesta = client.post(
        "/api/v1/practicar/responder", json={"opcion_id": 100}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_progreso_calcula_porcentaje_y_completado(client, autenticado, monkeypatch):
    monkeypatch.setattr(
        practicar_repository,
        "obtener_progreso",
        lambda conn, usuario_id: [
            {
                "tema_id": 1,
                "slug": "tema-a",
                "titulo": "Tema A",
                "total_preguntas": 3,
                "correctas": 2,
            },
            {
                "tema_id": 2,
                "slug": "tema-b",
                "titulo": "Tema B",
                "total_preguntas": 3,
                "correctas": 3,
            },
            {
                "tema_id": 3,
                "slug": "tema-c",
                "titulo": "Tema C",
                "total_preguntas": 0,
                "correctas": 0,
            },
        ],
    )

    respuesta = client.get("/api/v1/practicar/progreso/me")

    assert respuesta.status_code == 200
    progreso = respuesta.json()
    assert progreso[0]["porcentaje"] == 66.67
    assert progreso[0]["completado"] is False
    assert progreso[1]["porcentaje"] == 100.0
    assert progreso[1]["completado"] is True
    assert progreso[2]["porcentaje"] == 0.0
    assert progreso[2]["completado"] is False


def test_progreso_sin_token(client):
    respuesta = client.get("/api/v1/practicar/progreso/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_verificar_enlace_endpoint(client, monkeypatch):
    monkeypatch.setattr(enlaces_service, "verificar_enlace", lambda url: "seguro")

    respuesta = client.post(
        "/api/v1/practicar/verificar-enlace",
        json={"url": "https://ejemplo.com"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"resultado": "seguro"}


def test_verificar_enlace_url_invalida(client):
    respuesta = client.post(
        "/api/v1/practicar/verificar-enlace", json={"url": "no-es-una-url"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_verificar_enlace_sin_api_key(client, monkeypatch):
    monkeypatch.setattr(
        enlaces_service,
        "get_settings",
        lambda: SimpleNamespace(safe_browsing_api_key=None),
    )

    respuesta = client.post(
        "/api/v1/practicar/verificar-enlace",
        json={"url": "https://ejemplo.com"},
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["code"] == "SERVICIO_EXTERNO_NO_DISPONIBLE"


def test_safe_browsing_detecta_amenaza(monkeypatch):
    class _Respuesta:
        status_code = 200

        def json(self):
            return {"matches": [{"threatType": "MALWARE"}]}

    monkeypatch.setattr(
        enlaces_service,
        "get_settings",
        lambda: SimpleNamespace(safe_browsing_api_key="clave"),
    )
    monkeypatch.setattr(
        enlaces_service.httpx, "post", lambda *args, **kwargs: _Respuesta()
    )

    assert enlaces_service.verificar_enlace("https://ejemplo.com") == "peligroso"


def test_safe_browsing_sin_amenaza(monkeypatch):
    class _Respuesta:
        status_code = 200

        def json(self):
            return {}

    monkeypatch.setattr(
        enlaces_service,
        "get_settings",
        lambda: SimpleNamespace(safe_browsing_api_key="clave"),
    )
    monkeypatch.setattr(
        enlaces_service.httpx, "post", lambda *args, **kwargs: _Respuesta()
    )

    assert enlaces_service.verificar_enlace("https://ejemplo.com") == "seguro"


def test_safe_browsing_falla(monkeypatch):
    def _falla(*args, **kwargs):
        raise httpx.ConnectError("sin conexión")

    monkeypatch.setattr(
        enlaces_service,
        "get_settings",
        lambda: SimpleNamespace(safe_browsing_api_key="clave"),
    )
    monkeypatch.setattr(enlaces_service.httpx, "post", _falla)

    with pytest.raises(ServicioExternoNoDisponible):
        enlaces_service.verificar_enlace("https://ejemplo.com")


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("http://ejemplo.com", "sospechoso"),
        ("https://192.168.1.1", "sospechoso"),
        ("https://bit.ly/abc", "sospechoso"),
        ("https://xn--90a3ac.com", "sospechoso"),
        ("https://ejemplo.com/login", "sospechoso"),
        ("https://ejemplo.com", "seguro"),
    ],
)
def test_heuristicas_de_enlaces(url, esperado, monkeypatch):
    monkeypatch.setattr(
        enlaces_service,
        "get_settings",
        lambda: SimpleNamespace(safe_browsing_api_key="clave"),
    )
    monkeypatch.setattr(
        enlaces_service, "_consultar_safe_browsing", lambda url, key: False
    )

    assert enlaces_service.verificar_enlace(url) == esperado
