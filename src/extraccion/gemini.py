"""Extractor Gemini: texto limpio → JSON del contrato del laboratorio.

Implementación mínima y ejecutable. El laboratorio NO inventa datos:
solo se extrae información explícita en la noticia, en JSON válido.

TODO(alumno) — mejoras opcionales, el código ya corre sin ellas:
- reintentos ante 429 / timeouts
- recorte de textos muy largos antes del prompt
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path

from src.config import DIR_JSON, GEMINI_API_KEY, GEMINI_MODEL, PAUSA_ENTRE_REQUESTS
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

    1. Carga GEMINI_API_KEY desde .env (nunca hardcodear la clave).
    2. Usa el texto ya limpio en noticia.texto_limpio.
    3. Llama al modelo (p. ej. gemini-2.0-flash) con construir_prompt().
    4. Parsea JSON (quita fences markdown si el modelo los agrega).
    5. Guarda data/json/{id_noticia}.json.
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
    MAX_CARACTERES_TEXTO = 24_000
    MAX_INTENTOS = 3

    def __init__(self, dir_json: Path = DIR_JSON) -> None:
        self.dir_json = dir_json
        self.dir_json.mkdir(parents=True, exist_ok=True)
        self._cliente = None

    def construir_prompt(self, noticia: NoticiaFuente) -> str:
        campos = ", ".join(self.CAMPOS_OBLIGATORIOS)
        texto = (noticia.texto_limpio or "").strip()
        if len(texto) > self.MAX_CARACTERES_TEXTO:
            texto = texto[: self.MAX_CARACTERES_TEXTO]
        return (
            "Analiza la siguiente noticia delictual.\n\n"
            "Extrae solamente información explícita. No inventes datos, "
            "entidades, roles, fechas ni relaciones. Un detenido, imputado, "
            "acusado, condenado, víctima o testigo debe conservar exactamente "
            "el rol que indica el texto; no infieras culpabilidad.\n"
            "Devuelve exclusivamente JSON valido, sin markdown ni explicaciones.\n\n"
            f"Campos obligatorios: {campos}.\n"
            "titulo, fecha_publicacion y resumen pueden ser null.\n"
            "delitos, organizaciones y lugares son listas de strings.\n"
            "personas: lista de objetos con claves nombre y rol.\n"
            "objetos: lista de objetos con claves tipo, nombre, cantidad, unidad.\n"
            "relaciones: lista de objetos con claves origen, tipo, destino.\n"
            "Si un dato no aparece, usa null o una lista vacia.\n\n"
            f"id_noticia: {noticia.id_noticia}\n"
            f"fuente: {noticia.fuente}\n"
            f"url: {noticia.url}\n\n"
            "NOTICIA:\n"
            f"{texto}\n"
        )

    def extraer(self, noticia: NoticiaFuente) -> dict:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Copie .env.example a .env y complete la clave. "
                "Nunca suba .env a GitHub."
            )
        cliente = self._obtener_cliente()
        from google.genai import types

        respuesta = self._consultar_con_reintentos(cliente, types, noticia)
        bruto = (getattr(respuesta, "text", None) or "").strip()
        if not bruto:
            raise ValueError(
                f"Gemini devolvió una respuesta vacía para {noticia.id_noticia}."
            )
        data = self._parsear_json(bruto)
        data["id_noticia"] = noticia.id_noticia
        if not data.get("fuente"):
            data["fuente"] = noticia.fuente
        if not data.get("url"):
            data["url"] = noticia.url
        ruta = self.dir_json / f"{noticia.id_noticia}.json"
        ruta.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        time.sleep(PAUSA_ENTRE_REQUESTS)
        return data

    def _consultar_con_reintentos(self, cliente, types, noticia: NoticiaFuente):
        """Reintenta fallos transitorios sin duplicar la escritura del JSON."""
        ultimo_error: Exception | None = None
        for intento in range(1, self.MAX_INTENTOS + 1):
            try:
                return cliente.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=self.construir_prompt(noticia),
                    config=types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        response_mime_type="application/json",
                        temperature=0,
                    ),
                )
            except Exception as exc:  # La SDK usa distintas excepciones según versión.
                ultimo_error = exc
                if intento == self.MAX_INTENTOS:
                    break
                espera = 2 ** (intento - 1)
                print(f"    Gemini falló (intento {intento}/{self.MAX_INTENTOS}); reintentando en {espera}s.")
                time.sleep(espera)
        raise RuntimeError(
            f"Gemini no respondió después de {self.MAX_INTENTOS} intentos para "
            f"{noticia.id_noticia}: {ultimo_error}"
        ) from ultimo_error

    def _obtener_cliente(self):
        if self._cliente is None:
            from google import genai

            self._cliente = genai.Client(api_key=GEMINI_API_KEY)
        return self._cliente

    @staticmethod
    def _parsear_json(bruto: str) -> dict:
        texto = bruto.strip()
        cerca = re.search(r"```(?:json)?\s*(.*?)\s*```", texto, re.DOTALL)
        if cerca:
            texto = cerca.group(1)
        try:
            data = json.loads(texto)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini no devolvió JSON válido: {exc}. "
                f"Respuesta: {texto[:300]!r}"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("La respuesta de Gemini no es un objeto JSON.")
        return data
