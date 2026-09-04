"""Persistencia final: red de notas Markdown para Obsidian.

No se usa SQLite, MongoDB ni Neo4j. Cada noticia y cada entidad debe
tener su propia nota, enlazada con [[wiki-links]].
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.config import DIR_VAULT
from src.excepciones import EtapaPendienteAlumno


class EscritorObsidian(ABC):
    """Contrato para generar la bóveda a partir de JSON validado."""

    @abstractmethod
    def escribir_noticia(self, data: dict) -> Path:
        """Crea obsidian_vault/Noticias/{id_noticia}.md con frontmatter y enlaces."""

    @abstractmethod
    def escribir_entidades(self, noticias: list[dict]) -> None:
        """Agrega notas de delitos, personas, organizaciones, lugares y objetos."""

    @abstractmethod
    def escribir_indice(self, noticias: list[dict]) -> Path:
        """Crea obsidian_vault/00_Indice.md."""

    @abstractmethod
    def escribir_vault(self, noticias: list[dict]) -> None:
        """Orquesta noticia + entidades + índice."""


class EscritorVaultObsidian(EscritorObsidian):
    """Implementación objetivo del laboratorio.

    Use src.conocimiento.utilidades.slugify y enlace_obsidian.
    Jerarquía esperada:
        obsidian_vault/
        ├── 00_Indice.md
        ├── Noticias/
        ├── Delitos/
        ├── Personas/
        ├── Organizaciones/
        ├── Lugares/
        ├── Objetos/
        └── Relaciones/
    """

    def __init__(self, vault: Path = DIR_VAULT) -> None:
        self.vault = vault

    def escribir_noticia(self, data: dict) -> Path:
        # TODO(alumno): plantilla Markdown con YAML, resumen y [[enlaces]].
        raise EtapaPendienteAlumno(
            modulo="src.conocimiento.obsidian.EscritorVaultObsidian.escribir_noticia",
            pista="Genere Noticias/{id}.md con delitos, personas, lugares y relaciones enlazadas.",
        )

    def escribir_entidades(self, noticias: list[dict]) -> None:
        # TODO(alumno): índices con defaultdict(set) agrupando por entidad.
        raise EtapaPendienteAlumno(
            modulo="src.conocimiento.obsidian.EscritorVaultObsidian.escribir_entidades",
            pista="Una nota por delito/persona/lugar con la lista de noticias relacionadas.",
        )

    def escribir_indice(self, noticias: list[dict]) -> Path:
        # TODO(alumno): índice navegable de toda la bóveda.
        raise EtapaPendienteAlumno(
            modulo="src.conocimiento.obsidian.EscritorVaultObsidian.escribir_indice",
            pista="Escriba 00_Indice.md listando noticias y entidades.",
        )

    def escribir_vault(self, noticias: list[dict]) -> None:
        # TODO(alumno): llamar a los tres métodos anteriores en orden.
        raise EtapaPendienteAlumno(
            modulo="src.conocimiento.obsidian.EscritorVaultObsidian.escribir_vault",
            pista="Recorra data/json/*.json, valide y escriba la jerarquía completa del vault.",
        )
