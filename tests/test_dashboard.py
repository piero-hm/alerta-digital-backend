"""Pruebas del módulo transversal de dashboard."""

from datetime import datetime, timezone
from decimal import Decimal

from repositories import dashboard_repository


def test_top_estafas(client, monkeypatch):
    monkeypatch.setattr(
        dashboard_repository,
        "top_estafas",
        lambda conn: [{"tipo_fraude": "phishing", "total": 12}],
    )

    respuesta = client.get("/api/v1/dashboard/top-estafas")

    assert respuesta.status_code == 200
    assert respuesta.json() == [{"tipo_fraude": "phishing", "total": 12}]


def test_reportes_por_departamento(client, monkeypatch):
    monkeypatch.setattr(
        dashboard_repository,
        "reportes_por_departamento",
        lambda conn: [{"departamento": "Lima", "total": 8}],
    )

    respuesta = client.get("/api/v1/dashboard/por-departamento")

    assert respuesta.status_code == 200
    assert respuesta.json() == [{"departamento": "Lima", "total": 8}]


def test_reportes_mensuales(client, monkeypatch):
    monkeypatch.setattr(
        dashboard_repository,
        "reportes_mensuales",
        lambda conn: [
            {
                "mes": datetime(2026, 11, 1, tzinfo=timezone.utc),
                "total": 5,
                "monto_afectado": Decimal("1250.50"),
            }
        ],
    )

    respuesta = client.get("/api/v1/dashboard/mensual")

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos[0]["total"] == 5
    assert datos[0]["monto_afectado"] == 1250.5
    assert datos[0]["mes"].startswith("2026-11-01T00:00:00")
