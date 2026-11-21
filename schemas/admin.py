"""Schemas del módulo transversal de administración."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

PublicoObjetivo = Literal["todos", "adulto_mayor", "joven"]
TipoBloque = Literal["texto", "imagen", "video", "alerta", "lista"]


class ReporteAdminOut(BaseModel):
    """Reporte visible para moderadores y administradores."""

    id: int
    usuario_id: UUID
    email: str
    tipo_fraude: str
    canal: str
    departamento: str
    descripcion: str
    monto_afectado: float
    fecha_incidente: date
    evidencia_url: str | None = None
    estado: str
    creado_en: datetime


class EstadoReporteUpdate(BaseModel):
    """Nuevo estado permitido para moderar un reporte."""

    estado: Literal["validado", "rechazado"]


class TemaAdminOut(BaseModel):
    """Tema visible para administradores."""

    id: int
    slug: str
    titulo: str
    resumen: str | None = None
    publico_objetivo: PublicoObjetivo
    publicado: bool


class TemaAdminCreate(BaseModel):
    """Datos para crear un tema."""

    slug: str = Field(
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    titulo: str = Field(min_length=1, max_length=200)
    resumen: str | None = None
    publico_objetivo: PublicoObjetivo = "todos"


class TemaAdminUpdate(BaseModel):
    """Campos opcionales para editar un tema."""

    slug: str = Field(
        default=None,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    titulo: str = Field(default=None, min_length=1, max_length=200)
    resumen: str | None = None
    publico_objetivo: PublicoObjetivo = None


class PublicacionUpdate(BaseModel):
    """Cambia el estado de publicación de un tema."""

    publicado: bool


class BloqueAdminOut(BaseModel):
    """Bloque de un tema."""

    id: int
    tema_id: int
    orden: int
    tipo: TipoBloque
    contenido: str | None = None
    recurso_url: str | None = None


class BloqueAdminCreate(BaseModel):
    """Datos para crear un bloque."""

    orden: int = Field(ge=1)
    tipo: TipoBloque
    contenido: str | None = None
    recurso_url: str | None = Field(default=None, max_length=500)


class BloqueAdminUpdate(BaseModel):
    """Campos opcionales para editar un bloque."""

    orden: int = Field(default=None, ge=1)
    tipo: TipoBloque = None
    contenido: str | None = None
    recurso_url: str | None = Field(default=None, max_length=500)


class OpcionAdminOut(BaseModel):
    """Opción de una pregunta."""

    id: int
    pregunta_id: int
    texto: str
    es_correcta: bool


class OpcionAdminCreate(BaseModel):
    """Datos para crear una opción."""

    texto: str = Field(min_length=1, max_length=300)
    es_correcta: bool = False


class OpcionAdminUpdate(BaseModel):
    """Campos opcionales para editar una opción."""

    texto: str = Field(default=None, min_length=1, max_length=300)
    es_correcta: bool = None


class PreguntaAdminOut(BaseModel):
    """Pregunta con sus opciones."""

    id: int
    tema_id: int
    enunciado: str
    mensaje_simulado: str | None = None
    explicacion: str
    activa: bool
    opciones: list[OpcionAdminOut] = Field(default_factory=list)


class PreguntaAdminCreate(BaseModel):
    """Datos para crear una pregunta."""

    enunciado: str = Field(min_length=1)
    mensaje_simulado: str | None = None
    explicacion: str = Field(min_length=1)
    activa: bool = True


class PreguntaAdminUpdate(BaseModel):
    """Campos opcionales para editar una pregunta."""

    enunciado: str = Field(default=None, min_length=1)
    mensaje_simulado: str | None = None
    explicacion: str = Field(default=None, min_length=1)
    activa: bool = None


class TemaAdminDetalleOut(TemaAdminOut):
    """Tema con sus bloques y preguntas."""

    bloques: list[BloqueAdminOut] = Field(default_factory=list)
    preguntas: list[PreguntaAdminOut] = Field(default_factory=list)
