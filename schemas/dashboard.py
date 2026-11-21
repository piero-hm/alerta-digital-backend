"""Schemas del módulo transversal de dashboard."""

from datetime import datetime

from pydantic import BaseModel


class TopEstafaOut(BaseModel):
    """Tipo de fraude con su cantidad de reportes validados."""

    tipo_fraude: str
    total: int


class ReportesDepartamentoOut(BaseModel):
    """Departamento con su cantidad de reportes validados."""

    departamento: str
    total: int


class ReporteMensualOut(BaseModel):
    """Totales agregados por mes."""

    mes: datetime
    total: int
    monto_afectado: float
