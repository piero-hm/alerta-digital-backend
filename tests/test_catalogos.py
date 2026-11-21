"""Pruebas del módulo transversal de catálogos."""

from repositories import catalogos_repository


def test_obtener_catalogos(client, monkeypatch):
    monkeypatch.setattr(
        catalogos_repository,
        "listar_departamentos",
        lambda conn: [{"id": 15, "nombre": "Lima"}],
    )
    monkeypatch.setattr(
        catalogos_repository,
        "listar_tipos_fraude",
        lambda conn: [{"id": 1, "nombre": "phishing"}],
    )
    monkeypatch.setattr(
        catalogos_repository,
        "listar_canales",
        lambda conn: [{"id": 1, "nombre": "whatsapp"}],
    )

    respuesta = client.get("/api/v1/catalogos")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "departamentos": [{"id": 15, "nombre": "Lima"}],
        "tipos_fraude": [{"id": 1, "nombre": "phishing"}],
        "canales": [{"id": 1, "nombre": "whatsapp"}],
    }
