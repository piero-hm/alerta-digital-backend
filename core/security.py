"""Validación de los JWT emitidos por Supabase Auth (ES256 + JWKS)."""

from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from core.config import get_settings
from core.exceptions import NoAutenticado


@lru_cache
def _jwks_client() -> PyJWKClient:
    """Cliente JWKS con caché de claves (no se pide en cada request)."""
    settings = get_settings()
    return PyJWKClient(settings.supabase_jwks_url, cache_keys=True)


def validar_token(token: str) -> dict[str, Any]:
    """Valida firma, expiración, audience e issuer; devuelve sub y email."""
    settings = get_settings()
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=settings.supabase_issuer,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise NoAutenticado("Token inválido o expirado") from exc

    sub = payload.get("sub")
    if not sub:
        raise NoAutenticado("El token no contiene el identificador del usuario")

    return {"sub": sub, "email": payload.get("email")}
