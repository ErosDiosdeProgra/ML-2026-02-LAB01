"""Limpieza de HTML a texto plano, según la guía del laboratorio."""

from __future__ import annotations

from bs4 import BeautifulSoup


class LimpiadorHTML:
    """Quita ruido (menús, scripts, publicidad) y deja párrafo útiles."""

    ETIQUETAS_RUIDO = ("script", "style", "nav", "footer", "aside", "noscript", "iframe")
    LARGO_MINIMO_LINEA = 40

    def limpiar(self, html: str) -> str:
        """HTML crudo → texto listo para enviar a un LLM."""
        soup = BeautifulSoup(html, "lxml")
        for etiqueta in soup(list(self.ETIQUETAS_RUIDO)):
            etiqueta.decompose()

        texto = soup.get_text("\n")
        lineas = [linea.strip() for linea in texto.splitlines()]
        lineas = [linea for linea in lineas if len(linea) > self.LARGO_MINIMO_LINEA]
        return "\n".join(lineas)
