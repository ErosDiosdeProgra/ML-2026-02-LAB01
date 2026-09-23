"""Extractor Gemini: texto limpio → JSON del contrato del laboratorio.

Implementación mínima y ejecutable. El laboratorio NO inventa datos:
solo se extrae información explícita en la noticia, en JSON válido.

Robustez implementada en este avance:
- reintentos ante 429 / timeouts (MAX_INTENTOS con backoff exponencial)
- recorte de textos muy largos antes del prompt (MAX_CARACTERES_TEXTO)
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
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
            "NORMALIZACIÓN DE ENTIDADES: usa una única forma canónica por entidad "
            "en toda la respuesta. Para personas, usa el nombre completo tal como "
            "aparece por primera vez y sin títulos (por ejemplo, usa 'María Pérez', "
            "no 'Sra. María Pérez' ni 'María Perez'). Reutiliza exactamente esa misma "
            "forma en personas y relaciones. No repitas una entidad por cambios de "
            "mayúsculas, tildes, espacios o abreviaciones. Si el texto no permite "
            "saber que dos menciones se refieren a la misma entidad, mantenlas separadas.\n"
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
        data = self._deduplicar_entidades(data)
        ruta = self.dir_json / f"{noticia.id_noticia}.json"
        ruta.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        time.sleep(PAUSA_ENTRE_REQUESTS)
        return data

    @staticmethod
    def _clave_entidad(valor: object) -> str:
        """Clave conservadora: iguala solo tildes, espacios y mayúsculas."""
        texto = " ".join(str(valor or "").split()).casefold()
        return "".join(
            caracter
            for caracter in unicodedata.normalize("NFKD", texto)
            if not unicodedata.combining(caracter)
        )

    @classmethod
    def _deduplicar_entidades(cls, data: dict) -> dict:
        """Elimina duplicados evidentes y conserva la primera forma del modelo.

        No intenta unir apodos, iniciales o personas parecidas: eso exigiría una
        decisión semántica que podría inventar una identidad.
        """
        alias_a_canonico: dict[str, str] = {}

        def unicos(valores: object) -> list[str]:
            resultado: list[str] = []
            vistos: set[str] = set()
            for valor in valores if isinstance(valores, list) else []:
                if not isinstance(valor, str) or not valor.strip():
                    continue
                clave = cls._clave_entidad(valor)
                if clave not in vistos:
                    canonico = " ".join(valor.split())
                    vistos.add(clave)
                    resultado.append(canonico)
                    alias_a_canonico[clave] = canonico
            return resultado

        for campo in ("delitos", "organizaciones", "lugares"):
            data[campo] = unicos(data.get(campo))

        personas, vistas_personas = [], set()
        for persona in data.get("personas") or []:
            if not isinstance(persona, dict) or not persona.get("nombre"):
                continue
            clave = cls._clave_entidad(persona["nombre"])
            if clave in vistas_personas:
                continue
            vistas_personas.add(clave)
            copia = dict(persona)
            copia["nombre"] = " ".join(str(persona["nombre"]).split())
            personas.append(copia)
            alias_a_canonico[clave] = copia["nombre"]
        data["personas"] = personas

        objetos, vistos_objetos = [], set()
        for objeto in data.get("objetos") or []:
            if not isinstance(objeto, dict) or not objeto.get("nombre"):
                continue
            clave = cls._clave_entidad(objeto["nombre"])
            if clave in vistos_objetos:
                continue
            vistos_objetos.add(clave)
            copia = dict(objeto)
            copia["nombre"] = " ".join(str(objeto["nombre"]).split())
            objetos.append(copia)
            alias_a_canonico.setdefault(clave, copia["nombre"])
        data["objetos"] = objetos

        relaciones, vistas_relaciones = [], set()
        for relacion in data.get("relaciones") or []:
            if not isinstance(relacion, dict):
                continue
            copia = dict(relacion)
            for extremo in ("origen", "destino"):
                if isinstance(copia.get(extremo), str):
                    clave = cls._clave_entidad(copia[extremo])
                    copia[extremo] = alias_a_canonico.get(clave, " ".join(copia[extremo].split()))
            clave_relacion = tuple(cls._clave_entidad(copia.get(campo)) for campo in ("origen", "tipo", "destino"))
            if clave_relacion not in vistas_relaciones:
                vistas_relaciones.add(clave_relacion)
                relaciones.append(copia)
        data["relaciones"] = relaciones
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
