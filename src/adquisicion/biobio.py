"""Adaptador para BioBioChile."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.adquisicion.base import CapturadorFuente

_DOMINIOS = ("biobiochile.cl",)
_ALIASES_FUENTE = ("BioBioChile", "BioBio", "Bío Bío", "biobio")
_SELECTORES = (
    "div.nota-contenido",
    "div.post-content",
    "div.article-content",
    "article .content",
    "article",
)


class CapturadorBioBio(CapturadorFuente):
    """Extrae el cuerpo de una nota de www.biobiochile.cl."""

    def acepta(self, url: str, fuente: str | None = None) -> bool:
        host = urlparse(url).netloc.lower()
        if any(dom in host for dom in _DOMINIOS):
            return True
        return self._coincide_fuente(fuente, _ALIASES_FUENTE)

    def extraer_cuerpo(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for selector in _SELECTORES:
            nodo = soup.select_one(selector)
            if nodo:
                texto = nodo.get_text("\n", strip=True)
                if len(texto) > 120:
                    return texto
        return ""
