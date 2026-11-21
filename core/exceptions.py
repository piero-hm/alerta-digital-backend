"""Excepciones de negocio con el formato de error único de la API."""


class AppError(Exception):
    """Error controlado que se traduce a {"code", "detail"}."""

    code = "ERROR_INTERNO"
    status_code = 500

    def __init__(self, detail: str, code: str | None = None, status_code: int | None = None):
        self.detail = detail
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail)


class NoEncontrado(AppError):
    code = "NO_ENCONTRADO"
    status_code = 404


class Validacion(AppError):
    code = "VALIDACION"
    status_code = 422


class Conflicto(AppError):
    code = "CONFLICTO"
    status_code = 409


class NoAutenticado(AppError):
    code = "NO_AUTENTICADO"
    status_code = 401


class SinPermiso(AppError):
    code = "SIN_PERMISO"
    status_code = 403


class DniInvalido(AppError):
    code = "DNI_INVALIDO"
    status_code = 422


class DniNoEncontrado(AppError):
    code = "DNI_NO_ENCONTRADO"
    status_code = 404


class ServicioExternoNoDisponible(AppError):
    code = "SERVICIO_EXTERNO_NO_DISPONIBLE"
    status_code = 503


class ErrorInterno(AppError):
    code = "ERROR_INTERNO"
    status_code = 500
