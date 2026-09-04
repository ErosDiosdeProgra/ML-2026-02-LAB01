"""Capturador genérico: cualquier URL, limpieza heurística de HTML."""

from __future__ import annotations

from urllib.parse import urlparse

from src.adquisicion.base import CapturadorFuente
from src.adquisicion.http import ClienteHTTP
from src.limpieza.limpiador import LimpiadorHTML


class CapturadorGenerico(CapturadorFuente):
    """Fallback: acepta cualquier URL y extrae texto con LimpiadorHTML."""

    def __init__(self, cliente: ClienteHTTP, limpiador: LimpiadorHTML | None = None) -> None:
        super().__init__(cliente)
        self.limpiador = limpiador or LimpiadorHTML()

    def acepta(self, url: str, fuente: str | None = None) -> bool:
        """Siempre acepta: es el último recurso de la fábrica."""
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)

    def extraer_cuerpo(self, html: str) -> str:
        return self.limpiador.limpiar(html)
