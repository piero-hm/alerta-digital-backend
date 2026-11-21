"""Schemas del módulo Practicar."""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class OpcionPreguntaOut(BaseModel):
    """Opción de una pregunta, sin revelar si es correcta."""

    id: int
    texto: str


class PreguntaOut(BaseModel):
    """Pregunta activa con sus opciones."""

    id: int
    enunciado: str
    mensaje_simulado: str | None = None
    opciones: list[OpcionPreguntaOut]


class RespuestaCreate(BaseModel):
    """Opción elegida por el usuario."""

    opcion_id: int = Field(gt=0)


class RespuestaOut(BaseModel):
    """Resultado de responder una pregunta."""

    es_correcta: bool
    explicacion: str


class ProgresoTemaOut(BaseModel):
    """Progreso del usuario en un tema."""

    tema_id: int
    slug: str
    titulo: str
    total_preguntas: int
    correctas: int
    porcentaje: float
    completado: bool


class EnlaceCreate(BaseModel):
    """URL que se desea verificar."""

    url: HttpUrl = Field(max_length=2048)


class EnlaceOut(BaseModel):
    """Resultado del verificador de enlaces."""

    resultado: Literal["seguro", "sospechoso", "peligroso"]
