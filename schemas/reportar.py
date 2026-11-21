"""Schemas del módulo Reportar."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ReporteCreate(BaseModel):
    """Datos para crear un reporte de estafa."""

    tipo_fraude_id: int = Field(gt=0)
    canal_id: int = Field(gt=0)
    departamento_id: int = Field(gt=0)
    descripcion: str = Field(min_length=20, max_length=3000)
    monto_afectado: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )
    fecha_incidente: date
    evidencia_url: str | None = Field(default=None, max_length=500)

    @field_validator("fecha_incidente")
    @classmethod
    def fecha_no_futura(cls, valor: date) -> date:
        """La fecha del incidente no puede ser posterior a hoy."""
        if valor > date.today():
            raise ValueError("La fecha del incidente no puede ser futura")
        return valor


class ReporteOut(BaseModel):
    """Reporte con nombres de catálogo y estado."""

    id: int
    tipo_fraude: str
    canal: str
    departamento: str
    estado: str
    descripcion: str
    monto_afectado: float
    fecha_incidente: date
    evidencia_url: str | None = None
    creado_en: datetime


class AlertaOut(BaseModel):
    """Reporte validado y anonimizado para consulta pública."""

    tipo_fraude: str
    canal: str
    departamento: str
    fecha_incidente: date
    descripcion: str


class AlertasPageOut(BaseModel):
    """Página de alertas públicas."""

    total: int
    pagina: int
    limite: int
    alertas: list[AlertaOut]
