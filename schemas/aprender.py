"""Schemas del módulo Aprender."""

from typing import Literal

from pydantic import BaseModel, Field

PublicoObjetivo = Literal["todos", "adulto_mayor", "joven"]
TipoBloque = Literal["texto", "imagen", "video", "alerta", "lista"]


class TemaResumen(BaseModel):
    """Datos de un tema para el listado."""

    id: int
    slug: str
    titulo: str
    resumen: str | None = None
    publico_objetivo: PublicoObjetivo


class BloqueOut(BaseModel):
    """Bloque de contenido de un tema."""

    id: int
    orden: int
    tipo: TipoBloque
    contenido: str | None = None
    recurso_url: str | None = None


class TemaDetalle(TemaResumen):
    """Tema con sus bloques ordenados por 'orden'."""

    bloques: list[BloqueOut] = Field(default_factory=list)
