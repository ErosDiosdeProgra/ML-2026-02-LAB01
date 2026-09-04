"""Paquete de adquisición de noticias."""

from src.adquisicion.fabrica import FabricaCapturadores
from src.adquisicion.google_news import DescubridorGoogleNews
from src.adquisicion.repositorio import RepositorioNoticias

__all__ = [
    "FabricaCapturadores",
    "DescubridorGoogleNews",
    "RepositorioNoticias",
]
