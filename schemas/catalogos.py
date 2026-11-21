"""Schemas del módulo transversal de catálogos."""

from pydantic import BaseModel


class ItemCatalogo(BaseModel):
    """Elemento simple de un catálogo."""

    id: int
    nombre: str


class CatalogosOut(BaseModel):
    """Catálogos usados por los formularios del frontend."""

    departamentos: list[ItemCatalogo]
    tipos_fraude: list[ItemCatalogo]
    canales: list[ItemCatalogo]
