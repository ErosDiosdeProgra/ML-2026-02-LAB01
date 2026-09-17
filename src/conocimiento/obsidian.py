"""Persistencia final: red de notas Markdown para Obsidian.

No se usa SQLite, MongoDB ni Neo4j. Cada noticia y cada entidad debe
tener su propia nota, enlazada con [[wiki-links]] que Obsidian resuelve.

Convención de nombres:
- Los archivos de entidades usan src.conocimiento.utilidades.slugify
  ("Tráfico de drogas" → Delitos/Trafico_de_drogas.md).
- Los enlaces se escriben como [[slug|Nombre original]] para que Obsidian
  encuentre el archivo (primer segmento) y muestre el nombre legible:
  [[Trafico_de_drogas|Tráfico de drogas]].
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path

from src.config import DIR_JSON, DIR_VAULT
from src.conocimiento.utilidades import enlace_obsidian, slugify


def cargar_noticias_desde_disco(dir_json: Path = DIR_JSON) -> list[dict]:
    """Lee todos los JSON de data/json/*.json en orden de id_noticia.

    Se omite cualquier archivo con prefijo `ejemplo_` (fixtures de prueba)
    para que un json de ejemplo nunca colisione con una noticia real. Un
    archivo que no sea JSON válido se omite con aviso.
    """
    if not dir_json.exists():
        return []
    noticias: list[dict] = []
    for ruta in sorted(dir_json.glob("*.json")):
        if ruta.name.startswith("ejemplo_"):
            continue
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("id_noticia"):
                noticias.append(data)
        except Exception as exc:  # noqa: BLE001 — un archivo malo no tumba el vault
            print(f"    [Obsidian] Se omitió {ruta.name}: {exc}")
    return noticias


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
    """Generador del vault del laboratorio.

    Jerarquía esperada:
        obsidian_vault/
        ├── 00_Indice.md
        ├── Noticias/     N001.md ... (una por JSON)
        ├── Delitos/      Trafico_de_drogas.md
        ├── Personas/     Juan_Perez.md
        ├── Organizaciones/
        ├── Lugares/
        ├── Objetos/
        └── Relaciones/   INVESTIGADO_POR.md (una por tipo de relación)
    """

    SUBDIRECTORIOS = (
        "Noticias",
        "Delitos",
        "Personas",
        "Organizaciones",
        "Lugares",
        "Objetos",
        "Relaciones",
    )

    def __init__(self, vault: Path = DIR_VAULT) -> None:
        self.vault = vault
        for subdirectorio in self.SUBDIRECTORIOS:
            (self.vault / subdirectorio).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Utilidades de plantilla
    # ------------------------------------------------------------------

    @staticmethod
    def _yaml(valor: object) -> str:
        """Escapa un escalar YAML (evita romper el frontmatter con ':' → texto)."""
        texto = "" if valor is None else str(valor)
        if not texto:
            return "''"
        if (
            texto[0] in "!&*@%`\"'#|>-,?[]{}:"
            or ": " in texto
            or texto.endswith(":")
            or "\n" in texto
        ):
            return "'" + texto.replace("'", "''") + "'"
        return texto

    @staticmethod
    def _enlace(nombre: str) -> str:
        """[[slug|Nombre]] → el enlace resuelve el archivo y se lee bien."""
        return f"[[{slugify(nombre)}|{nombre}]]"

    @staticmethod
    def _seccion(titulo: str, lineas: list[str]) -> str:
        if not lineas:
            return f"## {titulo}\n- _(sin datos)_"
        cuerpo = "\n".join(f"- {linea}" for linea in lineas)
        return f"## {titulo}\n{cuerpo}"

    @staticmethod
    def _listas_por_noticia(noticias: list[dict]) -> dict[str, dict[str, set[str]]]:
        """id_noticia → {delitos|personas|organizaciones|lugares|objetos: set}."""
        por_noticia: dict[str, dict[str, set[str]]] = {}
        for data in noticias:
            nid = data.get("id_noticia") or ""
            personas = {
                p["nombre"]
                for p in data.get("personas") or []
                if p.get("nombre") and str(p["nombre"]).strip()
            }
            por_noticia[nid] = {
                "delitos": {e for e in data.get("delitos") or [] if str(e).strip()},
                "personas": personas,
                "organizaciones": {
                    e for e in data.get("organizaciones") or [] if str(e).strip()
                },
                "lugares": {e for e in data.get("lugares") or [] if str(e).strip()},
                "objetos": {
                    o["nombre"] for o in data.get("objetos") or [] if o.get("nombre")
                },
            }
        return por_noticia

    @staticmethod
    def _indice_por_entidad(
        por_noticia: dict[str, dict[str, set[str]]],
    ) -> dict[str, dict[str, set[str]]]:
        """tipo → entidad → {id_noticia}. Solo entidades con mención real."""
        indice: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for nid, entidades in por_noticia.items():
            for tipo, valores in entidades.items():
                for entidad in valores:
                    indice[tipo][entidad].add(nid)
        return indice

    def _entidades_relacionadas(
        self,
        por_noticia: dict[str, dict[str, set[str]]],
        tipos: tuple[str, ...],
        noticias_ids: set[str],
        excepto_tipo: str,
        entidad: str,
    ) -> list[str]:
        """Entidades de `tipos` que coaparecen con `entidad` en las noticias."""
        resultado: set[str] = set()
        for nid in noticias_ids:
            for tipo in tipos:
                if tipo == excepto_tipo:
                    continue
                resultado.update(por_noticia[nid][tipo])
        resultado.discard(entidad)
        return sorted(resultado, key=slugify)

    # ------------------------------------------------------------------
    # Nota de noticia
    # ------------------------------------------------------------------

    def _plantilla_noticia(self, data: dict) -> str:
        front = (
            "---\n"
            f"id: {self._yaml(data.get('id_noticia'))}\n"
            f"fecha_publicacion: {self._yaml(data.get('fecha_publicacion'))}\n"
            f"fuente: {self._yaml(data.get('fuente'))}\n"
            f"url: {self._yaml(data.get('url'))}\n"
            "---"
        )

        bloques = [f"# {data.get('titulo') or 'Noticia sin título'}", ""]
        bloques.append("## Resumen")
        bloques.append(str(data.get("resumen") or "_Sin resumen._"))
        bloques.append("")

        delitos = [self._enlace(d) for d in data.get("delitos") or []]
        bloques += [self._seccion("Delitos", delitos), ""]

        personas = [
            (
                f"{self._enlace(p['nombre'])} — {p.get('rol')}"
                if p.get("rol")
                else self._enlace(p["nombre"])
            )
            for p in data.get("personas") or []
            if p.get("nombre")
        ]
        bloques += [self._seccion("Personas", personas), ""]

        organizaciones = [self._enlace(o) for o in data.get("organizaciones") or []]
        bloques += [self._seccion("Organizaciones", organizaciones), ""]

        lugares = [self._enlace(l) for l in data.get("lugares") or []]
        bloques += [self._seccion("Lugares", lugares), ""]

        objetos = [
            f"{self._enlace(o['nombre'])} ({o.get('tipo')})"
            for o in data.get("objetos") or []
            if o.get("nombre")
        ]
        bloques += [self._seccion("Objetos", objetos), ""]

        relaciones = [
            f"{self._enlace(r['origen'])} -- {r.get('tipo')} --> "
            f"{self._enlace(r['destino'])}"
            for r in data.get("relaciones") or []
            if r.get("origen") or r.get("destino")
        ]
        bloques += [self._seccion("Relaciones", relaciones), ""]

        return front + "\n\n" + "\n".join(bloques).rstrip() + "\n"

    def escribir_noticia(self, data: dict) -> Path:
        ruta = self.vault / "Noticias" / f"{data['id_noticia']}.md"
        ruta.write_text(self._plantilla_noticia(data), encoding="utf-8")
        return ruta

    # ------------------------------------------------------------------
    # Notas de entidades
    # ------------------------------------------------------------------

    def _escribir_delitos(self, por_noticia, indice) -> None:
        for delito in sorted(indice["delitos"], key=slugify):
            noticias_ids = indice["delitos"][delito]
            personas = self._entidades_relacionadas(
                por_noticia, ("personas",), noticias_ids, "delitos", delito
            )
            organizaciones = self._entidades_relacionadas(
                por_noticia, ("organizaciones",), noticias_ids, "delitos", delito
            )
            lugares = self._entidades_relacionadas(
                por_noticia, ("lugares",), noticias_ids, "delitos", delito
            )
            notas = [
                f"# {delito}",
                "",
                "Tipo: Delito",
                "",
                self._seccion(
                    "Noticias relacionadas",
                    [enlace_obsidian(nid) for nid in sorted(noticias_ids)],
                ),
                "",
                self._seccion("Personas relacionadas", [self._enlace(p) for p in personas]),
                "",
                self._seccion(
                    "Organizaciones relacionadas",
                    [self._enlace(o) for o in organizaciones],
                ),
                "",
                self._seccion("Lugares", [self._enlace(l) for l in lugares]),
                "",
            ]
            ruta = self.vault / "Delitos" / f"{slugify(delito)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def _escribir_personas(self, por_noticia, indice, roles_por_persona) -> None:
        for persona in sorted(indice["personas"], key=slugify):
            noticias_ids = indice["personas"][persona]
            roles = ", ".join(sorted(roles_por_persona[persona])) or "sin rol declarado"
            delitos = self._entidades_relacionadas(
                por_noticia, ("delitos",), noticias_ids, "personas", persona
            )
            organizaciones = self._entidades_relacionadas(
                por_noticia, ("organizaciones",), noticias_ids, "personas", persona
            )
            lugares = self._entidades_relacionadas(
                por_noticia, ("lugares",), noticias_ids, "personas", persona
            )
            notas = [
                f"# {persona}",
                "",
                "Tipo: Persona",
                f"Rol observado: {roles}",
                "",
                self._seccion(
                    "Noticias donde aparece",
                    [enlace_obsidian(nid) for nid in sorted(noticias_ids)],
                ),
                "",
                self._seccion("Delitos asociados", [self._enlace(d) for d in delitos]),
                "",
                self._seccion(
                    "Organizaciones relacionadas",
                    [self._enlace(o) for o in organizaciones],
                ),
                "",
                self._seccion("Lugares", [self._enlace(l) for l in lugares]),
                "",
            ]
            ruta = self.vault / "Personas" / f"{slugify(persona)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def _escribir_organizaciones(self, por_noticia, indice) -> None:
        for org in sorted(indice["organizaciones"], key=slugify):
            noticias_ids = indice["organizaciones"][org]
            delitos = self._entidades_relacionadas(
                por_noticia, ("delitos",), noticias_ids, "organizaciones", org
            )
            personas = self._entidades_relacionadas(
                por_noticia, ("personas",), noticias_ids, "organizaciones", org
            )
            lugares = self._entidades_relacionadas(
                por_noticia, ("lugares",), noticias_ids, "organizaciones", org
            )
            notas = [
                f"# {org}",
                "",
                "Tipo: Organización",
                "",
                self._seccion(
                    "Noticias donde aparece",
                    [enlace_obsidian(nid) for nid in sorted(noticias_ids)],
                ),
                "",
                self._seccion("Delitos asociados", [self._enlace(d) for d in delitos]),
                "",
                self._seccion("Personas relacionadas", [self._enlace(p) for p in personas]),
                "",
                self._seccion("Lugares", [self._enlace(l) for l in lugares]),
                "",
            ]
            ruta = self.vault / "Organizaciones" / f"{slugify(org)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def _escribir_lugares(self, por_noticia, indice) -> None:
        for lugar in sorted(indice["lugares"], key=slugify):
            noticias_ids = indice["lugares"][lugar]
            delitos = self._entidades_relacionadas(
                por_noticia, ("delitos",), noticias_ids, "lugares", lugar
            )
            personas = self._entidades_relacionadas(
                por_noticia, ("personas",), noticias_ids, "lugares", lugar
            )
            organizaciones = self._entidades_relacionadas(
                por_noticia, ("organizaciones",), noticias_ids, "lugares", lugar
            )
            notas = [
                f"# {lugar}",
                "",
                "Tipo: Lugar",
                "",
                self._seccion(
                    "Noticias donde aparece",
                    [enlace_obsidian(nid) for nid in sorted(noticias_ids)],
                ),
                "",
                self._seccion("Delitos asociados", [self._enlace(d) for d in delitos]),
                "",
                self._seccion("Personas relacionadas", [self._enlace(p) for p in personas]),
                "",
                self._seccion(
                    "Organizaciones relacionadas",
                    [self._enlace(o) for o in organizaciones],
                ),
                "",
            ]
            ruta = self.vault / "Lugares" / f"{slugify(lugar)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def _escribir_objetos(self, indice) -> None:
        for objeto in sorted(indice["objetos"], key=slugify):
            noticias_ids = indice["objetos"][objeto]
            notas = [
                f"# {objeto}",
                "",
                "Tipo: Objeto",
                "",
                self._seccion(
                    "Noticias donde aparece",
                    [enlace_obsidian(nid) for nid in sorted(noticias_ids)],
                ),
                "",
            ]
            ruta = self.vault / "Objetos" / f"{slugify(objeto)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def _escribir_relaciones(self, noticias: list[dict]) -> None:
        """Una nota por tipo de enlace (INVESTIGADO_POR, OPERA_EN, ...)."""
        por_tipo: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        nids_por_tipo: dict[str, set[str]] = defaultdict(set)
        for data in noticias:
            nid = data.get("id_noticia")
            for rel in data.get("relaciones") or []:
                origen = rel.get("origen")
                destino = rel.get("destino")
                tipo = rel.get("tipo")
                if not tipo or not (origen or destino):
                    continue
                por_tipo[tipo].append((origen or "?", destino or "?", nid))
                nids_por_tipo[tipo].add(nid)

        for tipo in sorted(por_tipo):
            instancias = [
                f"{self._enlace(origen)} -- {tipo} --> {self._enlace(destino)}  "
                f"`({nid})`"
                for origen, destino, nid in por_tipo[tipo]
            ]
            notas = [
                f"# {tipo}",
                "",
                "Tipo: Relación",
                "",
                self._seccion("Instancias", instancias),
                "",
                self._seccion(
                    "Noticias relacionadas",
                    [enlace_obsidian(nid) for nid in sorted(nids_por_tipo[tipo])],
                ),
                "",
            ]
            ruta = self.vault / "Relaciones" / f"{slugify(tipo)}.md"
            ruta.write_text("\n".join(notas).rstrip() + "\n", encoding="utf-8")

    def escribir_entidades(self, noticias: list[dict]) -> None:
        por_noticia = self._listas_por_noticia(noticias)
        indice = self._indice_por_entidad(por_noticia)

        roles_por_persona: dict[str, set[str]] = defaultdict(set)
        for data in noticias:
            for persona in data.get("personas") or []:
                if persona.get("nombre"):
                    roles_por_persona[persona["nombre"]].add(
                        str(persona.get("rol") or "")
                    )

        self._escribir_delitos(por_noticia, indice)
        self._escribir_personas(por_noticia, indice, roles_por_persona)
        self._escribir_organizaciones(por_noticia, indice)
        self._escribir_lugares(por_noticia, indice)
        self._escribir_objetos(indice)
        self._escribir_relaciones(noticias)

    # ------------------------------------------------------------------
    # Índice y orquestación
    # ------------------------------------------------------------------

    def escribir_indice(self, noticias: list[dict]) -> Path:
        por_noticia = self._listas_por_noticia(noticias)
        indice = self._indice_por_entidad(por_noticia)
        tipos_relacion = sorted(
            {
                r.get("tipo")
                for data in noticias
                for r in (data.get("relaciones") or [])
                if r.get("tipo")
            }
        )
        ruta = self.vault / "00_Indice.md"

        bloques = [
            "# Índice — Bóveda de noticias delictuales",
            "",
            "> Vault generado automáticamente por `python main.py obsidian`.",
            "",
            f"## Noticias ({len(noticias)})",
        ]
        bloques += [
            f"- {enlace_obsidian(data['id_noticia'])}"
            for data in sorted(noticias, key=lambda d: d["id_noticia"])
        ]
        bloques.append("")

        etiquetas = {
            "delitos": "Delitos",
            "personas": "Personas",
            "organizaciones": "Organizaciones",
            "lugares": "Lugares",
            "objetos": "Objetos",
        }
        for tipo, etiqueta in etiquetas.items():
            entidades = sorted(indice[tipo], key=slugify)
            bloques.append(f"## {etiqueta} ({len(entidades)})")
            bloques += [f"- {self._enlace(e)}" for e in entidades] or [
                "- _(sin datos aún)_"
            ]
            bloques.append("")

        bloques.append(f"## Relaciones ({len(tipos_relacion)})")
        bloques += [f"- {enlace_obsidian(t)}" for t in tipos_relacion] or [
            "- _(sin datos aún)_"
        ]
        bloques.append("")

        ruta.write_text("\n".join(bloques).rstrip() + "\n", encoding="utf-8")
        return ruta

    def _limpiar(self) -> None:
        """Elimina notas previas para que no queden huérfanas entre corridas."""
        for ruta in self.vault.rglob("*.md"):
            ruta.unlink(missing_ok=True)

    def escribir_vault(self, noticias: list[dict]) -> None:
        self._limpiar()
        for data in sorted(noticias, key=lambda d: d["id_noticia"]):
            self.escribir_noticia(data)
        self.escribir_entidades(noticias)
        self.escribir_indice(noticias)