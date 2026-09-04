"""Adaptador para La Tercera."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.adquisicion.base import CapturadorFuente

_DOMINIOS = ("latercera.com",)
_ALIASES_FUENTE = ("LaTercera", "La Tercera")
_SELECTORES = (
    "div.article-body",
    "div.single-content",
    "div.article-content",
    "div.story-content",
    "article",
)
_PARRAFOS = "p.article-body__paragraph, div.article-body__paragraph"


class CapturadorLaTercera(CapturadorFuente):
    """Extrae el cuerpo de una nota de www.latercera.com."""

    def acepta(self, url: str, fuente: str | None = None) -> bool:
        host = urlparse(url).netloc.lower()
        if any(dom in host for dom in _DOMINIOS):
            return True
        return self._coincide_fuente(fuente, _ALIASES_FUENTE)

    def extraer_cuerpo(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        parrafos = soup.select(_PARRAFOS)
        if parrafos:
            texto = "\n".join(p.get_text(" ", strip=True) for p in parrafos)
            if len(texto) > 120:
                return texto
        for selector in _SELECTORES:
            nodo = soup.select_one(selector)
            if nodo:
                texto = nodo.get_text("\n", strip=True)
                if len(texto) > 120:
                    return texto
        return ""
