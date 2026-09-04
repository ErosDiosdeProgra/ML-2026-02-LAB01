"""Persistencia de HTML crudo y texto limpio, con id_noticia como clave."""

from __future__ import annotations

from pathlib import Path

from src.config import DIR_PROCESSED, DIR_RAW
from src.modelos import NoticiaFuente


class RepositorioNoticias:
    """Guarda y lee archivos intermedios del pipeline de captura."""

    def __init__(
        self,
        dir_raw: Path = DIR_RAW,
        dir_processed: Path = DIR_PROCESSED,
    ) -> None:
        self.dir_raw = dir_raw
        self.dir_processed = dir_processed
        self.dir_raw.mkdir(parents=True, exist_ok=True)
        self.dir_processed.mkdir(parents=True, exist_ok=True)

    def guardar_html(self, noticia: NoticiaFuente, html: str) -> Path:
        ruta = self.dir_raw / f"{noticia.id_noticia}.html"
        ruta.write_text(html, encoding="utf-8")
        return ruta

    def guardar_texto(self, noticia: NoticiaFuente, texto: str) -> Path:
        ruta = self.dir_processed / f"{noticia.id_noticia}.txt"
        ruta.write_text(texto, encoding="utf-8")
        return ruta

    def leer_texto(self, id_noticia: str) -> str:
        return (self.dir_processed / f"{id_noticia}.txt").read_text(encoding="utf-8")
