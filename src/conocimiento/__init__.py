"""Paquete de generación del vault Obsidian."""

from src.conocimiento.obsidian import EscritorObsidian, EscritorVaultObsidian
from src.conocimiento.utilidades import enlace_obsidian, slugify

__all__ = [
    "EscritorObsidian",
    "EscritorVaultObsidian",
    "slugify",
    "enlace_obsidian",
]
