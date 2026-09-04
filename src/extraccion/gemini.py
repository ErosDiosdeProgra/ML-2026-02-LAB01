"""Contrato de extracción con un LLM.

TODO(alumno): completar ExtractorGemini. El laboratorio NO inventa datos:
solo se extrae información explícita en la noticia, en JSON válido.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.excepciones import EtapaPendienteAlumno
from src.modelos import NoticiaFuente


class ExtractorLLM(ABC):
    """Interfaz de cualquier extractor basado en modelo generativo."""

    @abstractmethod
    def construir_prompt(self, noticia: NoticiaFuente) -> str:
        """Arma el prompt con el esquema JSON y el texto de la noticia."""

    @abstractmethod
    def extraer(self, noticia: NoticiaFuente) -> dict:
        """Devuelve un diccionario que cumple el contrato JSON del laboratorio."""


class ExtractorGemini(ExtractorLLM):
    """Extractor oficial del laboratorio (Gemini).

    Pasos sugeridos:
    1. Cargar GEMINI_API_KEY desde .env (nunca hardcodear la clave).
    2. Leer data/processed/{id_noticia}.txt
    3. Llamar al modelo (p. ej. gemini-1.5-flash) con construir_prompt().
    4. Devolver exclusivamente JSON válido (sin markdown ni explicaciones).
    5. Si un campo no aparece en la noticia, usar null o lista vacía.
    """

    CAMPOS_OBLIGATORIOS = [
        "id_noticia",
        "titulo",
        "fecha_publicacion",
        "fuente",
        "url",
        "resumen",
        "delitos",
        "personas",
        "organizaciones",
        "lugares",
        "objetos",
        "relaciones",
    ]

    def construir_prompt(self, noticia: NoticiaFuente) -> str:
        # TODO(alumno): reemplazar este método. Debe exigir JSON válido y
        # prohibir inventar entidades, roles o relaciones.
        raise EtapaPendienteAlumno(
            modulo="src.extraccion.gemini.ExtractorGemini.construir_prompt",
            pista=(
                "Diseñe un prompt estricto con los campos "
                f"{self.CAMPOS_OBLIGATORIOS} y el texto de la noticia."
            ),
        )

    def extraer(self, noticia: NoticiaFuente) -> dict:
        # TODO(alumno): llamar a google.generativeai, parsear response.text
        # y guardar data/json/{id_noticia}.json
        raise EtapaPendienteAlumno(
            modulo="src.extraccion.gemini.ExtractorGemini.extraer",
            pista=(
                "Configure genai con GEMINI_API_KEY, genere el contenido y "
                "devuelva un dict. No suba la clave a GitHub."
            ),
        )
