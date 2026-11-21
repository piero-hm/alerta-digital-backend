"""Punto de entrada de la API de Alerta Digital."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from apis import admin, aprender, auth, catalogos, dashboard, practicar, reportar
from core.config import get_settings
from core.database import close_pool
from core.exceptions import AppError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cierra el pool de conexiones al apagar la aplicación."""
    yield
    close_pool()


app = FastAPI(
    title="Alerta Digital API",
    description="API REST de la plataforma educativa Alerta Digital.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AppError)
async def manejar_app_error(request: Request, exc: AppError):
    """Traduce las excepciones de negocio al formato único de error."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, exc: RequestValidationError):
    """Devuelve los errores de validación con code VALIDACION."""
    partes = []
    for error in exc.errors():
        ubicacion = [str(parte) for parte in error.get("loc", ())]
        if ubicacion and ubicacion[0] in {"body", "query", "path", "header", "cookie"}:
            ubicacion = ubicacion[1:]
        mensaje = error.get("msg", "Dato inválido")
        partes.append(f"{'.'.join(ubicacion)}: {mensaje}" if ubicacion else mensaje)
    detalle = "; ".join(partes) or "Datos inválidos"
    return JSONResponse(
        status_code=422,
        content={"code": "VALIDACION", "detail": detalle},
    )


_CODIGOS_HTTP = {
    401: "NO_AUTENTICADO",
    403: "SIN_PERMISO",
    404: "NO_ENCONTRADO",
    409: "CONFLICTO",
    503: "SERVICIO_EXTERNO_NO_DISPONIBLE",
}


@app.exception_handler(StarletteHTTPException)
async def manejar_http_error(request: Request, exc: StarletteHTTPException):
    """Normaliza los HTTPException de FastAPI/Starlette."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": _CODIGOS_HTTP.get(exc.status_code, "ERROR_INTERNO"),
            "detail": exc.detail if isinstance(exc.detail, str) else "Error HTTP",
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def manejar_error_interno(request: Request, exc: Exception):
    """Registra el error y oculta los detalles técnicos al cliente."""
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": "ERROR_INTERNO", "detail": "Ocurrió un error interno"},
    )


@app.get("/health", tags=["Salud"])
def health():
    """Verificación simple de que el servicio está vivo."""
    return {"status": "ok"}


app.include_router(aprender.router, prefix=API_PREFIX)
app.include_router(practicar.router, prefix=API_PREFIX)
app.include_router(reportar.router, prefix=API_PREFIX)
app.include_router(catalogos.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(auth.router_dni, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
