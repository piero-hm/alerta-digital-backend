"""Pruebas del módulo Reportar."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from core.deps import get_current_profile, get_current_user
from main import app
from repositories import reportar_repository, usuario_repository

USUARIO_ID = "11111111-1111-1111-1111-111111111111"
HOY = date.today().isoformat()
MANANA = (date.today() + timedelta(days=1)).isoformat()

PERFIL = {
    "id": USUARIO_ID,
    "sub": USUARIO_ID,
    "email": "persona@ejemplo.com",
    "rol": "ciudadano",
}

REPORTE = {
    "id": 1,
    "tipo_fraude": "phishing",
    "canal": "whatsapp",
    "departamento": "Lima",
    "estado": "pendiente",
    "descripcion": "Recibí un mensaje falso pidiendo mis datos.",
    "monto_afectado": Decimal("150.00"),
    "fecha_incidente": date(2026, 11, 18),
    "evidencia_url": "https://ejemplo.com/captura.png",
    "creado_en": datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc),
}


def _body(**cambios):
    body = {
        "tipo_fraude_id": 1,
        "canal_id": 2,
        "departamento_id": 3,
        "descripcion": "Recibí un mensaje falso pidiendo mis datos.",
        "monto_afectado": 150.00,
        "fecha_incidente": HOY,
        "evidencia_url": "https://ejemplo.com/captura.png",
    }
    body.update(cambios)
    return body


@pytest.fixture
def autenticado():
    app.dependency_overrides[get_current_profile] = lambda: dict(PERFIL)
    yield
    app.dependency_overrides.pop(get_current_profile, None)


@pytest.fixture
def moderador():
    app.dependency_overrides[get_current_profile] = lambda: {
        **PERFIL,
        "rol": "moderador",
    }
    yield
    app.dependency_overrides.pop(get_current_profile, None)


def _catalogos_validos(monkeypatch):
    monkeypatch.setattr(
        reportar_repository, "existe_tipo_fraude", lambda conn, id_: True
    )
    monkeypatch.setattr(
        reportar_repository, "existe_canal", lambda conn, id_: True
    )
    monkeypatch.setattr(
        reportar_repository, "existe_departamento", lambda conn, id_: True
    )
    monkeypatch.setattr(
        reportar_repository, "obtener_estado_id", lambda conn, nombre: 3
    )


def test_crear_reporte_pendiente(client, autenticado, monkeypatch):
    _catalogos_validos(monkeypatch)
    capturado = {}

    def _crear(conn, **kwargs):
        capturado.update(kwargs)
        return dict(REPORTE)

    monkeypatch.setattr(reportar_repository, "crear_reporte", _crear)

    respuesta = client.post("/api/v1/reportar", json=_body())

    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "pendiente"
    assert datos["monto_afectado"] == 150.0
    assert capturado["usuario_id"] == USUARIO_ID
    assert capturado["estado_id"] == 3
    assert capturado["descripcion"] == _body()["descripcion"]


@pytest.mark.parametrize(
    "campo", ["tipo_fraude", "canal", "departamento"]
)
def test_crear_reporte_catalogo_inexistente(
    client, autenticado, monkeypatch, campo
):
    _catalogos_validos(monkeypatch)
    monkeypatch.setattr(
        reportar_repository,
        f"existe_{campo}",
        lambda conn, id_: False,
    )

    respuesta = client.post("/api/v1/reportar", json=_body())

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_reporte_fecha_futura(client, autenticado):
    respuesta = client.post(
        "/api/v1/reportar", json=_body(fecha_incidente=MANANA)
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_reporte_monto_negativo(client, autenticado):
    respuesta = client.post(
        "/api/v1/reportar", json=_body(monto_afectado=-1)
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_reporte_descripcion_corta(client, autenticado):
    respuesta = client.post(
        "/api/v1/reportar", json=_body(descripcion="corto")
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_crear_reporte_sin_token(client):
    respuesta = client.post("/api/v1/reportar", json=_body())

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_crear_reporte_rol_no_ciudadano(client, moderador):
    respuesta = client.post("/api/v1/reportar", json=_body())

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SIN_PERMISO"


def test_crear_reporte_sin_perfil(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": USUARIO_ID,
        "email": "persona@ejemplo.com",
    }
    monkeypatch.setattr(
        usuario_repository, "obtener_perfil", lambda conn, uid: None
    )

    respuesta = client.post("/api/v1/reportar", json=_body())

    assert respuesta.status_code == 403
    assert respuesta.json() == {
        "code": "SIN_PERMISO",
        "detail": "Falta completar el perfil",
    }


def test_listar_mis_reportes(client, autenticado, monkeypatch):
    monkeypatch.setattr(
        reportar_repository,
        "listar_reportes_usuario",
        lambda conn, uid: [dict(REPORTE)],
    )

    respuesta = client.get("/api/v1/reportar/mios")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["estado"] == "pendiente"


def test_listar_mis_reportes_sin_token(client):
    respuesta = client.get("/api/v1/reportar/mios")

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_listar_alertas_paginadas(client, monkeypatch):
    monkeypatch.setattr(reportar_repository, "contar_alertas", lambda conn: 42)
    capturado = {}

    def _listar(conn, limite, offset):
        capturado["limite"] = limite
        capturado["offset"] = offset
        return [
            {
                "tipo_fraude": "phishing",
                "canal": "whatsapp",
                "departamento": "Lima",
                "fecha_incidente": date(2026, 11, 18),
                "descripcion": "Mensaje falso pidiendo datos.",
            }
        ]

    monkeypatch.setattr(reportar_repository, "listar_alertas", _listar)

    respuesta = client.get("/api/v1/reportar/alertas?pagina=2&limite=10")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total"] == 42
    assert datos["pagina"] == 2
    assert datos["limite"] == 10
    assert capturado == {"limite": 10, "offset": 10}
    assert set(datos["alertas"][0]) == {
        "tipo_fraude",
        "canal",
        "departamento",
        "fecha_incidente",
        "descripcion",
    }


def test_listar_alertas_paginacion_por_defecto(client, monkeypatch):
    monkeypatch.setattr(reportar_repository, "contar_alertas", lambda conn: 0)
    capturado = {}

    def _listar(conn, limite, offset):
        capturado["limite"] = limite
        capturado["offset"] = offset
        return []

    monkeypatch.setattr(reportar_repository, "listar_alertas", _listar)

    respuesta = client.get("/api/v1/reportar/alertas")

    assert respuesta.status_code == 200
    assert respuesta.json()["pagina"] == 1
    assert respuesta.json()["limite"] == 20
    assert capturado == {"limite": 20, "offset": 0}


@pytest.mark.parametrize("query", ["pagina=0", "limite=0", "limite=101"])
def test_listar_alertas_paginacion_invalida(client, query):
    respuesta = client.get(f"/api/v1/reportar/alertas?{query}")

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"
