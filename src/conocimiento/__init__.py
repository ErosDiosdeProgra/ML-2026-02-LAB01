"""Paquete de generación del vault Obsidian."""

from src.conocimiento.obsidian import (
    EscritorObsidian,
    EscritorVaultObsidian,
    cargar_noticias_desde_disco,
)
from src.conocimiento.utilidades import enlace_obsidian, slugify

__all__ = [
    "EscritorObsidian",
    "EscritorVaultObsidian",
    "cargar_noticias_desde_disco",
    "slugify",
    "enlace_obsidian",
]
