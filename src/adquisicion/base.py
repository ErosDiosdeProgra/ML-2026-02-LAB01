"""Clase abstracta de un capturador de noticias por fuente."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.adquisicion.http import ClienteHTTP


class CapturadorFuente(ABC):
    """Contrato común: ¿acepto esta URL? → descargo HTML → extraigo el cuerpo.

    Cada medio (BioBio, Cooperativa, La Tercera) implementa selectores propios.
    El capturador genérico es el fallback cuando no hay adaptador o el
    selector no encuentra contenido útil.
    """

    def __init__(self, cliente: ClienteHTTP) -> None:
        self.cliente = cliente

    @abstractmethod
    def acepta(self, url: str, fuente: str | None = None) -> bool:
        """True si este adaptador corresponde a la URL o al nombre de fuente."""

    def obtener_html(self, url: str) -> str:
        """Descarga el HTML completo de la noticia."""
        return self.cliente.texto(url)

    @abstractmethod
    def extraer_cuerpo(self, html: str) -> str:
        """Devuelve el texto del artículo o cadena vacía si no lo encuentra."""

    def _coincide_fuente(self, fuente: str | None, aliases: tuple[str, ...]) -> bool:
        if not fuente:
            return False
        normalizada = fuente.strip().lower().replace(" ", "")
        return any(alias.lower().replace(" ", "") in normalizada for alias in aliases)
