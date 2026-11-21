"""Pruebas del módulo Aprender."""

from repositories import aprender_repository

TEMA = {
    "id": 1,
    "slug": "phishing-que-es",
    "titulo": "¿Qué es el phishing?",
    "resumen": "Aprende a reconocer mensajes falsos.",
    "publico_objetivo": "todos",
}

BLOQUES = [
    {
        "id": 10,
        "orden": 1,
        "tipo": "texto",
        "contenido": "El phishing es un intento de engaño.",
        "recurso_url": None,
    },
    {
        "id": 11,
        "orden": 2,
        "tipo": "video",
        "contenido": None,
        "recurso_url": "dQw4w9WgXcQ",
    },
]


def test_listar_temas_publicados(client, monkeypatch):
    monkeypatch.setattr(
        aprender_repository,
        "listar_temas_publicados",
        lambda conn, publico_objetivo=None: [TEMA],
    )

    respuesta = client.get("/api/v1/aprender/temas")

    assert respuesta.status_code == 200
    assert respuesta.json() == [TEMA]


def test_listar_temas_filtra_por_publico(client, monkeypatch):
    capturado = {}

    def _fake(conn, publico_objetivo=None):
        capturado["publico_objetivo"] = publico_objetivo
        return []

    monkeypatch.setattr(aprender_repository, "listar_temas_publicados", _fake)

    respuesta = client.get(
        "/api/v1/aprender/temas", params={"publico_objetivo": "adulto_mayor"}
    )

    assert respuesta.status_code == 200
    assert capturado["publico_objetivo"] == "adulto_mayor"


def test_listar_temas_publico_invalido(client):
    respuesta = client.get(
        "/api/v1/aprender/temas", params={"publico_objetivo": "ninos"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["code"] == "VALIDACION"


def test_obtener_tema_con_bloques(client, monkeypatch):
    monkeypatch.setattr(
        aprender_repository,
        "obtener_tema_publicado",
        lambda conn, slug: dict(TEMA),
    )
    monkeypatch.setattr(
        aprender_repository,
        "listar_bloques",
        lambda conn, tema_id: list(BLOQUES),
    )

    respuesta = client.get("/api/v1/aprender/temas/phishing-que-es")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["slug"] == "phishing-que-es"
    assert [bloque["orden"] for bloque in cuerpo["bloques"]] == [1, 2]


def test_obtener_tema_inexistente(client, monkeypatch):
    monkeypatch.setattr(
        aprender_repository,
        "obtener_tema_publicado",
        lambda conn, slug: None,
    )

    respuesta = client.get("/api/v1/aprender/temas/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "code": "NO_ENCONTRADO",
        "detail": "Tema no encontrado",
    }
