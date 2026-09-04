"""Adaptador para Cooperativa.cl."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.adquisicion.base import CapturadorFuente

_DOMINIOS = ("cooperativa.cl",)
_ALIASES_FUENTE = ("Cooperativa", "RadioCooperativa")
_SELECTORES = (
    "div.texto-nota",
    "div.noticia-contenido",
    "div#contenido",
    "article",
    "div.article-body",
)


class CapturadorCooperativa(CapturadorFuente):
    """Extrae el cuerpo de una nota de www.cooperativa.cl."""

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
