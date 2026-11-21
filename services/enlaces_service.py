"""Cliente del verificador de enlaces (Safe Browsing + heurísticas básicas)."""

from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

import httpx

from core.config import get_settings
from core.exceptions import ServicioExternoNoDisponible

SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
TIMEOUT_SEGUNDOS = 5.0

TIPOS_AMENAZA = [
    "MALWARE",
    "SOCIAL_ENGINEERING",
    "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION",
]

ACORTADORES = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "shorturl.at",
    "rebrand.ly",
    "tiny.cc",
}

PALABRAS_SOSPECHOSAS = (
    "login",
    "iniciar-sesion",
    "verificar",
    "actualizar",
    "contrasena",
    "contraseña",
    "clave",
    "cuenta",
    "premio",
    "gratis",
    "urgente",
    "ganador",
    "sorteo",
    "regalo",
    "factura",
    "pago",
    "seguridad",
    "soporte",
)


def verificar_enlace(url: str) -> str:
    """Devuelve seguro, sospechoso o peligroso. No guarda nada."""
    settings = get_settings()
    if not settings.safe_browsing_api_key:
        raise ServicioExternoNoDisponible(
            "El verificador de enlaces no está configurado"
        )

    if _consultar_safe_browsing(url, settings.safe_browsing_api_key):
        return "peligroso"
    if _es_sospechoso(url):
        return "sospechoso"
    return "seguro"


def _consultar_safe_browsing(url: str, api_key: str) -> bool:
    """Consulta Google Safe Browsing y dice si la URL tiene amenazas."""
    payload: dict[str, Any] = {
        "client": {
            "clientId": "alerta-digital",
            "clientVersion": "1.0.0",
        },
        "threatInfo": {
            "threatTypes": TIPOS_AMENAZA,
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        respuesta = httpx.post(
            SAFE_BROWSING_URL,
            params={"key": api_key},
            json=payload,
            timeout=TIMEOUT_SEGUNDOS,
        )
    except httpx.HTTPError as exc:
        raise ServicioExternoNoDisponible(
            "No se pudo verificar el enlace. Intenta nuevamente."
        ) from exc

    if respuesta.status_code >= 400:
        raise ServicioExternoNoDisponible(
            "No se pudo verificar el enlace. Intenta nuevamente."
        )

    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise ServicioExternoNoDisponible(
            "El verificador de enlaces devolvió una respuesta inválida"
        ) from exc

    if not isinstance(datos, dict):
        raise ServicioExternoNoDisponible(
            "El verificador de enlaces devolvió una respuesta inválida"
        )

    return bool(datos.get("matches"))


def _es_sospechoso(url: str) -> bool:
    """Aplica heurísticas simples para advertir enlaces dudosos."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if not hostname:
        return True
    if parsed.scheme != "https":
        return True
    if _es_ip(hostname):
        return True
    if "xn--" in hostname:
        return True
    if hostname in ACORTADORES:
        return True

    try:
        puerto = parsed.port
    except ValueError:
        return True
    if puerto not in (None, 80, 443):
        return True

    if parsed.username or parsed.password:
        return True
    if hostname.count(".") >= 4:
        return True
    if len(url) > 200:
        return True

    texto = url.lower()
    return any(palabra in texto for palabra in PALABRAS_SOSPECHOSAS)


def _es_ip(hostname: str) -> bool:
    """Indica si el hostname es una dirección IP literal."""
    try:
        ip_address(hostname)
        return True
    except ValueError:
        return False
