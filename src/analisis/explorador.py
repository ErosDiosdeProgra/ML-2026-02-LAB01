"""Data Understanding sobre el corpus estructurado.

Los gráficos se guardan en ``data/analisis`` para poder incorporarlos al
informe sin depender de una ventana interactiva de matplotlib.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

# El laboratorio también debe funcionar desde terminal o PyCharm sin display.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config import DIR_JSON, RUTA_URLS


class ExploradorDatos:
    """Estadísticas y gráficos mínimos del laboratorio."""

    def __init__(
        self,
        dir_json: Path = DIR_JSON,
        ruta_urls: Path = RUTA_URLS,
        dir_salida: Path | None = None,
    ) -> None:
        self.dir_json = Path(dir_json)
        self.ruta_urls = Path(ruta_urls)
        self.dir_salida = Path(dir_salida) if dir_salida else self.dir_json.parent / "analisis"
        self.dir_salida.mkdir(parents=True, exist_ok=True)

    def _cargar_noticias(self) -> list[dict]:
        """Carga solo objetos JSON legibles; informa archivos defectuosos."""
        noticias: list[dict] = []
        invalidos: list[str] = []
        for ruta in sorted(self.dir_json.glob("*.json")):
            try:
                data = json.loads(ruta.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    noticias.append(data)
                else:
                    invalidos.append(ruta.name)
            except (OSError, json.JSONDecodeError):
                invalidos.append(ruta.name)
        if invalidos:
            print(f"JSON omitidos por formato inválido: {', '.join(invalidos)}")
        return noticias

    def _guardar_barras(self, series: pd.Series, titulo: str, nombre: str, xlabel: str) -> Path | None:
        if series.empty:
            print(f"Sin datos para: {titulo}.")
            return None
        fig, ax = plt.subplots(figsize=(9, 5))
        series.sort_values().plot.barh(ax=ax, color="#2c7fb8")
        ax.set_title(titulo)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("")
        fig.tight_layout()
        ruta = self.dir_salida / nombre
        fig.savefig(ruta, dpi=160)
        plt.close(fig)
        print(f"Gráfico guardado: {ruta}")
        return ruta

    def noticias_por_fuente(self) -> pd.Series:
        """Cuenta la cobertura por medio desde los JSON o, si faltan, URLs."""
        noticias = self._cargar_noticias()
        fuentes = [n.get("fuente") for n in noticias if n.get("fuente")]
        if not fuentes and self.ruta_urls.exists():
            fuentes = pd.read_csv(self.ruta_urls).get("fuente", pd.Series(dtype=str)).dropna().tolist()
        serie = pd.Series(fuentes, dtype="object").value_counts()
        self._guardar_barras(serie, "Noticias por fuente", "noticias_por_fuente.png", "Noticias")
        return serie

    def delitos_frecuentes(self) -> pd.Series:
        delitos = [d for n in self._cargar_noticias() for d in n.get("delitos", []) if isinstance(d, str) and d.strip()]
        serie = pd.Series(delitos, dtype="object").value_counts().head(10)
        self._guardar_barras(serie, "Top 10 delitos mencionados", "delitos_frecuentes.png", "Menciones")
        return serie

    def lugares_frecuentes(self) -> pd.Series:
        lugares = [l for n in self._cargar_noticias() for l in n.get("lugares", []) if isinstance(l, str) and l.strip()]
        serie = pd.Series(lugares, dtype="object").value_counts().head(10)
        self._guardar_barras(serie, "Top 10 lugares mencionados", "lugares_frecuentes.png", "Menciones")
        return serie

    def campos_faltantes(self) -> pd.Series:
        noticias = self._cargar_noticias()
        campos = ("titulo", "fecha_publicacion", "fuente", "url", "resumen", "delitos", "personas", "organizaciones", "lugares", "objetos", "relaciones")
        if not noticias:
            return pd.Series(dtype=float)
        faltantes = {campo: sum(n.get(campo) is None or n.get(campo) == "" or n.get(campo) == [] for n in noticias) * 100 / len(noticias) for campo in campos}
        serie = pd.Series(faltantes).sort_values(ascending=False)
        self._guardar_barras(serie, "Campos faltantes", "campos_faltantes.png", "Porcentaje de noticias")
        return serie

    def evolucion_temporal(self) -> pd.Series:
        fechas = pd.to_datetime([n.get("fecha_publicacion") for n in self._cargar_noticias()], errors="coerce")
        serie = pd.Series(fechas).dropna().dt.to_period("M").value_counts().sort_index()
        serie.index = serie.index.astype(str)
        self._guardar_barras(serie, "Noticias por mes", "evolucion_temporal.png", "Noticias")
        return serie

    def noticias_por_categoria(self) -> pd.Series:
        """Distribución por tema usando `categoria_busqueda` de urls.csv.

        Representa también las noticias no delictuales (vivienda, emergencias,
        economía), que no aparecen en ``delitos_frecuentes``.
        """
        noticias = self._cargar_noticias()
        categorias: dict[str, str] = {}
        if self.ruta_urls.exists():
            urls = pd.read_csv(self.ruta_urls)
            if {"id_noticia", "categoria_busqueda"}.issubset(urls.columns):
                categorias = dict(
                    zip(urls["id_noticia"].astype(str), urls["categoria_busqueda"].fillna(""))
                )
        serie = pd.Series(
            [categorias.get(str(n.get("id_noticia")), "") or "Sin categoría" for n in noticias],
            dtype="object",
        ).value_counts()
        self._guardar_barras(serie, "Noticias por categoría", "noticias_por_categoria.png", "Noticias")
        return serie

    def cobertura_delictual(self) -> pd.Series:
        """Cuenta noticias que mencionan delitos y las que no (vivienda, emergencias, etc.)."""
        noticias = self._cargar_noticias()
        if not noticias:
            return pd.Series(dtype="object")
        con = sum(bool(n.get("delitos")) for n in noticias)
        serie = pd.Series(
            {"Noticias con delitos": con, "Noticias sin delitos": len(noticias) - con},
            dtype="object",
        )
        self._guardar_barras(serie, "Noticias con y sin delitos", "cobertura_delictual.png", "Noticias")
        return serie

    def ejecutar(self) -> dict[str, pd.Series]:
        """Corre todas las visualizaciones pedidas en la guía."""
        if not self._cargar_noticias() and not self.ruta_urls.exists():
            print("No hay datos: ejecute capturar y extraer antes de analizar.")
            return {}
        resultados = {
            "noticias_por_fuente": self.noticias_por_fuente(),
            "noticias_por_categoria": self.noticias_por_categoria(),
            "cobertura_delictual": self.cobertura_delictual(),
            "delitos_frecuentes": self.delitos_frecuentes(),
            "lugares_frecuentes": self.lugares_frecuentes(),
            "campos_faltantes": self.campos_faltantes(),
            "evolucion_temporal": self.evolucion_temporal(),
        }
        noticias = self._cargar_noticias()
        if noticias:
            con = sum(bool(n.get("delitos")) for n in noticias)
            print(
                f"Resumen: {len(noticias)} noticias; {con} mencionan delitos y "
                f"{len(noticias) - con} son temas no delictuales "
                f"(vivienda, emergencias, economía, etc.)."
            )
        print(f"Análisis finalizado. Resultados en: {self.dir_salida}")
        return resultados
