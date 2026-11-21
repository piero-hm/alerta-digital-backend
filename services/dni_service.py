"""Cliente del proveedor externo de DNI y caché en memoria."""

import re
import threading
import time
from typing import Any

import httpx

from core.config import get_settings
from core.exceptions import DniInvalido, DniNoEncontrado, ServicioExternoNoDisponible

TTL_CACHE_SEGUNDOS = 3600
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


def consultar_dni(numero: str) -> dict[str, Any]:
    """Valida el DNI, usa la caché si está vigente y consulta al proveedor."""
    numero = str(numero or "").strip()
    if not re.fullmatch(r"\d{8}", numero):
        raise DniInvalido("El DNI debe tener exactamente 8 dígitos")

    ahora = time.monotonic()
    with _cache_lock:
        entrada = _cache.get(numero)
        if entrada is not None and entrada[0] > ahora:
            return dict(entrada[1])

    datos = _consultar_proveedor(numero)

    with _cache_lock:
        _cache[numero] = (time.monotonic() + TTL_CACHE_SEGUNDOS, datos)
    return dict(datos)


def _consultar_proveedor(numero: str) -> dict[str, Any]:
    """Consulta apisperu.com y normaliza la respuesta."""
    settings = get_settings()
    if not settings.dni_api_token:
        raise ServicioExternoNoDisponible(
            "El servicio de consulta de DNI no está configurado"
        )

    url = f"{settings.dni_api_url.rstrip('/')}/{numero}"
    try:
        respuesta = httpx.get(
            url,
            params={"token": settings.dni_api_token},
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        raise ServicioExternoNoDisponible(
            "No se pudo consultar el DNI. Intenta nuevamente."
        ) from exc

    if respuesta.status_code == 404:
        raise DniNoEncontrado("DNI no encontrado")
    if respuesta.status_code >= 400:
        raise ServicioExternoNoDisponible(
            "No se pudo consultar el DNI. Intenta nuevamente."
        )

    try:
        datos = respuesta.json()
    except ValueError as exc:
        raise ServicioExternoNoDisponible(
            "El proveedor de DNI devolvió una respuesta inválida"
        ) from exc

    if not isinstance(datos, dict):
        raise ServicioExternoNoDisponible(
            "El proveedor de DNI devolvió una respuesta inválida"
        )

    if datos.get("success") is False:
        mensaje = str(datos.get("message", "")).lower()
        if any(
            fragmento in mensaje
            for fragmento in (
                "no encontrado",
                "no encontr",
                "no existe",
                "no está",
                "no esta",
                "not found",
            )
        ):
            raise DniNoEncontrado("DNI no encontrado")
        raise ServicioExternoNoDisponible("No se pudo consultar el DNI")

    if isinstance(datos.get("data"), dict):
        datos = {**datos, **datos["data"]}

    nombres = _texto(datos.get("nombres") or datos.get("first_names"))
    apellido_paterno = _texto(
        datos.get("apellidoPaterno")
        or datos.get("apellido_paterno")
        or datos.get("paternal_surname")
    )
    apellido_materno = _texto(
        datos.get("apellidoMaterno")
        or datos.get("apellido_materno")
        or datos.get("maternal_surname")
    )

    if not nombres or not apellido_paterno:
        raise ServicioExternoNoDisponible(
            "El proveedor de DNI devolvió datos incompletos"
        )

    return {
        "dni": numero,
        "nombres": nombres,
        "apellido_paterno": apellido_paterno,
        "apellido_materno": apellido_materno or None,
    }


def _texto(valor: Any) -> str:
    """Convierte un valor del proveedor a texto limpio."""
    return str(valor).strip() if valor is not None else ""
