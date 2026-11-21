"""Reglas de negocio del módulo transversal de dashboard."""

from typing import Any

from repositories import dashboard_repository


def top_estafas(conn) -> list[dict[str, Any]]:
    """Devuelve los tipos de fraude más reportados."""
    return dashboard_repository.top_estafas(conn)


def reportes_por_departamento(conn) -> list[dict[str, Any]]:
    """Devuelve los reportes agrupados por departamento."""
    return dashboard_repository.reportes_por_departamento(conn)


def reportes_mensuales(conn) -> list[dict[str, Any]]:
    """Devuelve los reportes agrupados por mes."""
    return dashboard_repository.reportes_mensuales(conn)
