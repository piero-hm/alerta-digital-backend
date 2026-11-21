"""Configuración común de las pruebas (sin base de datos real)."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://prueba:prueba@localhost:6543/postgres")
os.environ.setdefault("SUPABASE_URL", "https://ejemplo.supabase.co")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:4200")
os.environ.setdefault("DNI_API_TOKEN", "token-de-prueba")

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from main import app


@pytest.fixture
def client():
    """Cliente de pruebas con la conexión a base de datos reemplazada."""

    def _db_falsa():
        yield object()

    app.dependency_overrides[get_db] = _db_falsa
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
