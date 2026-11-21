"""Pruebas del módulo transversal de administración y moderación."""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from core.deps import get_current_profile
from main import app
from repositories import admin_repository

USUARIO_ID = "11111111-1111-1111-1111-111111111111"

PERFIL_ADMIN = {
    "id": USUARIO_ID,
    "sub": USUARIO_ID,
    "email": "admin@ejemplo.com",
    "rol": "admin",
}

PERFIL_MODERADOR = {
    "id": USUARIO_ID,
    "sub": USUARIO_ID,
    "email": "moderador@ejemplo.com",
    "rol": "moderador",
}

PERFIL_CIUDADANO = {
    "id": USUARIO_ID,
    "sub": USUARIO_ID,
    "email": "persona@ejemplo.com",
    "rol": "ciudadano",
}

REPORTE = {
    "id": 1,
    "usuario_id": USUARIO_ID,
    "email": "persona@ejemplo.com",
    "estado_id": 1,
    "estado": "pendiente",
    "tipo_fraude": "phishing",
    "canal": "whatsapp",
    "departamento": "Lima",
    "descripcion": "Recibí un mensaje falso pidiendo mis datos.",
    "monto_afectado": Decimal("150.00"),
    "fecha_incidente": date(2026, 11, 18),
    "evidencia_url": None,
    "creado_en": datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc),
}

TEMA = {
    "id": 1,
    "slug": "phishing",
    "titulo": "Phishing",
    "resumen": "Aprende a reconocer mensajes falsos.",
    "publico_objetivo": "todos",
    "publicado": False,
}

BLOQUE = {
    "id": 10,
    "tema_id": 1,
    "orden": 1,
    "tipo": "texto",
    "contenido": "Contenido del bloque.",
    "recurso_url": None,
}

PREGUNTA = {
    "id": 20,
    "tema_id": 1,
    "enunciado": "¿Qué haces?",
    "mensaje_simulado": None,
    "explicacion": "No compartas tus datos.",
    "activa": True,
}

OPCION = {
    "id": 30,
    "pregunta_id": 20,
    "texto": "Opción A",
    "es_correcta": True,
}


@pytest.fixture
def admin():
    app.dependency_overrides[get_current_profile] = lambda: dict(PERFIL_ADMIN)
    yield
    app.dependency_overrides.pop(get_current_profile, None)


@pytest.fixture
def moderador():
    app.dependency_overrides[get_current_profile] = lambda: dict(
        PERFIL_MODERADOR
    )
    yield
    app.dependency_overrides.pop(get_current_profile, None)


@pytest.fixture
def ciudadano():
    app.dependency_overrides[get_current_profile] = lambda: dict(
        PERFIL_CIUDADANO
    )
    yield
    app.dependency_overrides.pop(get_current_profile, None)


def test_listar_reportes_como_moderador(client, moderador, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_estado_id", lambda conn, nombre: 1
    )
    monkeypatch.setattr(
        admin_repository,
        "listar_reportes",
        lambda conn, estado: [dict(REPORTE)],
    )

    respuesta = client.get("/api/v1/admin/reportes?estado=pendiente")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["estado"] == "pendiente"
    assert respuesta.json()[0]["email"] == "persona@ejemplo.com"


def test_listar_reportes_sin_filtro(client, moderador, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "listar_reportes",
        lambda conn, estado: [dict(REPORTE)],
    )

    respuesta = client.get("/api/v1/admin/reportes")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["id"] == 1


def test_listar_reportes_estado_invalido(client, moderador, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_estado_id", lambda conn, nombre: None
    )

    respuesta = client.get("/api/v1/admin/reportes?estado=otro")

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_listar_reportes_sin_token(client):
    respuesta = client.get("/api/v1/admin/reportes")

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_listar_reportes_como_ciudadano(client, ciudadano):
    respuesta = client.get("/api/v1/admin/reportes")

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SIN_PERMISO"


def test_cambiar_estado_reporte(client, moderador, monkeypatch, caplog):
    monkeypatch.setattr(
        admin_repository,
        "obtener_reporte_admin",
        lambda conn, rid: dict(REPORTE),
    )
    monkeypatch.setattr(
        admin_repository, "obtener_estado_id", lambda conn, nombre: 2
    )
    capturado = {}

    def _actualizar(conn, reporte_id, estado_id, estado_actual_id):
        capturado.update(
            {
                "reporte_id": reporte_id,
                "estado_id": estado_id,
                "estado_actual_id": estado_actual_id,
            }
        )
        return {**REPORTE, "estado": "validado", "estado_id": 2}

    monkeypatch.setattr(
        admin_repository, "actualizar_estado_reporte", _actualizar
    )

    with caplog.at_level(logging.INFO, logger="services.admin_service"):
        respuesta = client.patch(
            "/api/v1/admin/reportes/1/estado",
            json={"estado": "validado"},
        )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "validado"
    assert capturado == {
        "reporte_id": 1,
        "estado_id": 2,
        "estado_actual_id": 1,
    }
    assert "Reporte 1" in caplog.text
    assert "moderador@ejemplo.com" in caplog.text
    assert "pendiente" in caplog.text
    assert "validado" in caplog.text


def test_cambiar_estado_reporte_no_pendiente(
    client, moderador, monkeypatch
):
    monkeypatch.setattr(
        admin_repository,
        "obtener_reporte_admin",
        lambda conn, rid: {**REPORTE, "estado": "validado", "estado_id": 2},
    )

    respuesta = client.patch(
        "/api/v1/admin/reportes/1/estado",
        json={"estado": "rechazado"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_cambiar_estado_reporte_inexistente(
    client, moderador, monkeypatch
):
    monkeypatch.setattr(
        admin_repository, "obtener_reporte_admin", lambda conn, rid: None
    )

    respuesta = client.patch(
        "/api/v1/admin/reportes/999/estado",
        json={"estado": "validado"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_cambiar_estado_reporte_estado_invalido(client, moderador):
    respuesta = client.patch(
        "/api/v1/admin/reportes/1/estado",
        json={"estado": "pendiente"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_cambiar_estado_reporte_sin_token(client):
    respuesta = client.patch(
        "/api/v1/admin/reportes/1/estado",
        json={"estado": "validado"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_cambiar_estado_reporte_como_ciudadano(client, ciudadano):
    respuesta = client.patch(
        "/api/v1/admin/reportes/1/estado",
        json={"estado": "validado"},
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SIN_PERMISO"


def test_listar_temas_admin(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "listar_temas_admin", lambda conn: [dict(TEMA)]
    )

    respuesta = client.get("/api/v1/admin/temas")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["slug"] == "phishing"


def test_obtener_detalle_tema(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository,
        "listar_bloques",
        lambda conn, tid: [dict(BLOQUE)],
    )
    monkeypatch.setattr(
        admin_repository,
        "listar_preguntas_admin",
        lambda conn, tid: [dict(PREGUNTA)],
    )
    monkeypatch.setattr(
        admin_repository,
        "listar_opciones_admin",
        lambda conn, tid: [dict(OPCION)],
    )

    respuesta = client.get("/api/v1/admin/temas/1")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["bloques"][0]["orden"] == 1
    assert datos["preguntas"][0]["opciones"][0]["es_correcta"] is True


def test_obtener_detalle_tema_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_tema_admin", lambda conn, tid: None
    )

    respuesta = client.get("/api/v1/admin/temas/999")

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_crear_tema(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "existe_slug", lambda conn, slug: False
    )
    monkeypatch.setattr(
        admin_repository, "crear_tema", lambda conn, **kwargs: dict(TEMA)
    )

    respuesta = client.post(
        "/api/v1/admin/temas",
        json={
            "slug": "phishing",
            "titulo": "Phishing",
            "resumen": "Aprende a reconocer mensajes falsos.",
            "publico_objetivo": "todos",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["publicado"] is False


def test_crear_tema_slug_duplicado(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "existe_slug", lambda conn, slug: True
    )

    respuesta = client.post(
        "/api/v1/admin/temas",
        json={"slug": "phishing", "titulo": "Phishing"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_crear_tema_sin_rol_admin(client, ciudadano):
    respuesta = client.post(
        "/api/v1/admin/temas",
        json={"slug": "phishing", "titulo": "Phishing"},
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SIN_PERMISO"


def test_crear_tema_sin_token(client):
    respuesta = client.post(
        "/api/v1/admin/temas",
        json={"slug": "phishing", "titulo": "Phishing"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "NO_AUTENTICADO"


def test_actualizar_tema(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository,
        "actualizar_tema",
        lambda conn, tid, campos: {**TEMA, **campos},
    )

    respuesta = client.patch(
        "/api/v1/admin/temas/1", json={"titulo": "Phishing avanzado"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Phishing avanzado"


def test_actualizar_tema_slug_duplicado(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository, "existe_slug", lambda conn, slug, excluir_id: True
    )

    respuesta = client.patch(
        "/api/v1/admin/temas/1", json={"slug": "otro-slug"}
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_actualizar_tema_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_tema_admin", lambda conn, tid: None
    )

    respuesta = client.patch(
        "/api/v1/admin/temas/999", json={"titulo": "No existe"}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_publicar_tema(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "actualizar_publicacion",
        lambda conn, tid, publicado: {**TEMA, "publicado": publicado},
    )

    respuesta = client.patch(
        "/api/v1/admin/temas/1/publicacion", json={"publicado": True}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["publicado"] is True


def test_publicar_tema_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "actualizar_publicacion",
        lambda conn, tid, publicado: None,
    )

    respuesta = client.patch(
        "/api/v1/admin/temas/999/publicacion", json={"publicado": True}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_crear_bloque(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_orden_bloque",
        lambda conn, tid, orden: False,
    )
    monkeypatch.setattr(
        admin_repository,
        "crear_bloque",
        lambda conn, **kwargs: dict(BLOQUE),
    )

    respuesta = client.post(
        "/api/v1/admin/temas/1/bloques",
        json={
            "orden": 1,
            "tipo": "texto",
            "contenido": "Contenido del bloque.",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["orden"] == 1


def test_crear_bloque_orden_duplicado(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_orden_bloque",
        lambda conn, tid, orden: True,
    )

    respuesta = client.post(
        "/api/v1/admin/temas/1/bloques",
        json={"orden": 1, "tipo": "texto"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_crear_bloque_tema_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_tema_admin", lambda conn, tid: None
    )

    respuesta = client.post(
        "/api/v1/admin/temas/999/bloques",
        json={"orden": 1, "tipo": "texto"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_crear_bloque_tipo_invalido(client, admin):
    respuesta = client.post(
        "/api/v1/admin/temas/1/bloques",
        json={"orden": 1, "tipo": "otro"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_actualizar_bloque(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_bloque",
        lambda conn, bid: dict(BLOQUE),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_orden_bloque",
        lambda conn, tid, orden, excluir_id: False,
    )
    monkeypatch.setattr(
        admin_repository,
        "actualizar_bloque",
        lambda conn, bid, campos: {**BLOQUE, **campos},
    )

    respuesta = client.patch(
        "/api/v1/admin/bloques/10", json={"orden": 2}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["orden"] == 2


def test_actualizar_bloque_orden_duplicado(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_bloque",
        lambda conn, bid: dict(BLOQUE),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_orden_bloque",
        lambda conn, tid, orden, excluir_id: True,
    )

    respuesta = client.patch(
        "/api/v1/admin/bloques/10", json={"orden": 2}
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_actualizar_bloque_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_bloque", lambda conn, bid: None
    )

    respuesta = client.patch(
        "/api/v1/admin/bloques/999", json={"orden": 2}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_crear_pregunta(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_tema_admin",
        lambda conn, tid: dict(TEMA),
    )
    monkeypatch.setattr(
        admin_repository,
        "crear_pregunta",
        lambda conn, **kwargs: dict(PREGUNTA),
    )

    respuesta = client.post(
        "/api/v1/admin/temas/1/preguntas",
        json={
            "enunciado": "¿Qué haces?",
            "explicacion": "No compartas tus datos.",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["opciones"] == []


def test_crear_pregunta_tema_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_tema_admin", lambda conn, tid: None
    )

    respuesta = client.post(
        "/api/v1/admin/temas/999/preguntas",
        json={
            "enunciado": "¿Qué haces?",
            "explicacion": "No compartas tus datos.",
        },
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_actualizar_pregunta(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_pregunta",
        lambda conn, pid: dict(PREGUNTA),
    )
    monkeypatch.setattr(
        admin_repository,
        "actualizar_pregunta",
        lambda conn, pid, campos: {**PREGUNTA, **campos},
    )
    monkeypatch.setattr(
        admin_repository,
        "listar_opciones_por_pregunta",
        lambda conn, pid: [dict(OPCION)],
    )

    respuesta = client.patch(
        "/api/v1/admin/preguntas/20",
        json={"enunciado": "¿Qué haces ahora?"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["opciones"][0]["id"] == 30


def test_actualizar_pregunta_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_pregunta", lambda conn, pid: None
    )

    respuesta = client.patch(
        "/api/v1/admin/preguntas/999",
        json={"enunciado": "¿Qué haces ahora?"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_crear_opcion(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_pregunta",
        lambda conn, pid: dict(PREGUNTA),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_opcion_correcta",
        lambda conn, pid: False,
    )
    monkeypatch.setattr(
        admin_repository,
        "crear_opcion",
        lambda conn, **kwargs: dict(OPCION),
    )

    respuesta = client.post(
        "/api/v1/admin/preguntas/20/opciones",
        json={"texto": "Opción A", "es_correcta": True},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["es_correcta"] is True


def test_crear_opcion_correcta_duplicada(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_pregunta",
        lambda conn, pid: dict(PREGUNTA),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_opcion_correcta",
        lambda conn, pid: True,
    )

    respuesta = client.post(
        "/api/v1/admin/preguntas/20/opciones",
        json={"texto": "Opción B", "es_correcta": True},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_crear_opcion_pregunta_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_pregunta", lambda conn, pid: None
    )

    respuesta = client.post(
        "/api/v1/admin/preguntas/999/opciones",
        json={"texto": "Opción A"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"


def test_actualizar_opcion(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_opcion",
        lambda conn, oid: dict(OPCION),
    )
    monkeypatch.setattr(
        admin_repository,
        "actualizar_opcion",
        lambda conn, oid, campos: {**OPCION, **campos},
    )

    respuesta = client.patch(
        "/api/v1/admin/opciones/30", json={"texto": "Opción B"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["texto"] == "Opción B"


def test_actualizar_opcion_correcta_duplicada(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository,
        "obtener_opcion",
        lambda conn, oid: dict(OPCION),
    )
    monkeypatch.setattr(
        admin_repository,
        "existe_opcion_correcta",
        lambda conn, pid, excluir_id: True,
    )

    respuesta = client.patch(
        "/api/v1/admin/opciones/30", json={"es_correcta": True}
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "CONFLICTO"


def test_actualizar_opcion_inexistente(client, admin, monkeypatch):
    monkeypatch.setattr(
        admin_repository, "obtener_opcion", lambda conn, oid: None
    )

    respuesta = client.patch(
        "/api/v1/admin/opciones/999", json={"texto": "Opción B"}
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "NO_ENCONTRADO"
