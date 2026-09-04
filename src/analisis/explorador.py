"""Data Understanding sobre el corpus estructurado.

TODO(alumno): las visualizaciones no son decoración; deben revelar
cobertura, sesgos y problemas de calidad (nulos, JSON inválidos, nombres
inconsistentes).
"""

from __future__ import annotations

from src.excepciones import EtapaPendienteAlumno


class ExploradorDatos:
    """Estadísticas y gráficos mínimos del laboratorio."""

    def noticias_por_fuente(self) -> None:
        # TODO(alumno): gráfico de barras con pandas + matplotlib.
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.noticias_por_fuente",
            pista="Cuente noticias por la columna fuente (urls.csv o JSON).",
        )

    def delitos_frecuentes(self) -> None:
        # TODO(alumno): top 10 delitos a partir de data/json/*.json.
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.delitos_frecuentes",
            pista="Aplane la lista delitos de cada JSON y use value_counts().",
        )

    def lugares_frecuentes(self) -> None:
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.lugares_frecuentes",
            pista="Cuente menciones de comunas/regiones y grafique las más frecuentes.",
        )

    def campos_faltantes(self) -> None:
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.campos_faltantes",
            pista="Calcule el porcentaje de null/listas vacías por campo del JSON.",
        )

    def evolucion_temporal(self) -> None:
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.evolucion_temporal",
            pista="Si fecha_publicacion está disponible, grafique noticias por mes.",
        )

    def ejecutar(self) -> None:
        """Corre todas las visualizaciones pedidas en la guía."""
        raise EtapaPendienteAlumno(
            modulo="src.analisis.explorador.ExploradorDatos.ejecutar",
            pista=(
                "Implemente y llame a noticias_por_fuente, delitos_frecuentes, "
                "lugares_frecuentes, campos_faltantes y evolucion_temporal. "
                "Interprete cada gráfico en el informe."
            ),
        )
