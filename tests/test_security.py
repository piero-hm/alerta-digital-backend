"""Pruebas de la validación de JWT de Supabase."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from core import security
from core.config import get_settings
from core.exceptions import NoAutenticado


class _FirmaFalsa:
    def __init__(self, key):
        self.key = key


class _JwksFalso:
    def __init__(self, key):
        self._key = key

    def get_signing_key_from_jwt(self, token):
        return _FirmaFalsa(self._key)


@pytest.fixture
def clave_privada():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def jwks_falso(monkeypatch, clave_privada):
    monkeypatch.setattr(
        security, "_jwks_client", lambda: _JwksFalso(clave_privada.public_key())
    )


def _payload(**cambios):
    settings = get_settings()
    datos = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "persona@ejemplo.com",
        "aud": "authenticated",
        "iss": settings.supabase_issuer,
        "exp": int(time.time()) + 60,
    }
    datos.update(cambios)
    return datos


def test_token_valido_devuelve_sub_y_email(clave_privada):
    token = jwt.encode(_payload(), clave_privada, algorithm="ES256")

    usuario = security.validar_token(token)

    assert usuario == {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "persona@ejemplo.com",
    }


def test_token_expirado_es_rechazado(clave_privada):
    token = jwt.encode(_payload(exp=int(time.time()) - 60), clave_privada, algorithm="ES256")

    with pytest.raises(NoAutenticado):
        security.validar_token(token)


def test_token_con_audience_incorrecta_es_rechazado(clave_privada):
    token = jwt.encode(_payload(aud="otro"), clave_privada, algorithm="ES256")

    with pytest.raises(NoAutenticado):
        security.validar_token(token)


def test_token_con_issuer_incorrecto_es_rechazado(clave_privada):
    token = jwt.encode(_payload(iss="https://otro.example/auth/v1"), clave_privada, algorithm="ES256")

    with pytest.raises(NoAutenticado):
        security.validar_token(token)


def test_token_hs256_es_rechazado():
    token = jwt.encode(_payload(), "secreto-de-prueba-suficientemente-largo", algorithm="HS256")

    with pytest.raises(NoAutenticado):
        security.validar_token(token)


def test_token_sin_sub_es_rechazado(clave_privada):
    datos = _payload()
    datos.pop("sub")
    token = jwt.encode(datos, clave_privada, algorithm="ES256")

    with pytest.raises(NoAutenticado):
        security.validar_token(token)
