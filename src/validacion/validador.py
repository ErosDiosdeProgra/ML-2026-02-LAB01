"""Validación del JSON producido por el LLM.

El LLM no es la fuente de verdad: el código debe verificar el esquema.
"""

from __future__ import annotations

import json
from pathlib import Path


class ValidadorJSON:
    """Comprueba que cada archivo JSON cumpla el contrato de datos."""

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

    CAMPOS_LISTA = [
        "delitos",
        "personas",
        "organizaciones",
        "lugares",
        "objetos",
        "relaciones",
    ]

    CAMPOS_OBJETO = {
        "personas": ("nombre", "rol"),
        "objetos": ("tipo", "nombre", "cantidad", "unidad"),
        "relaciones": ("origen", "tipo", "destino"),
    }

    def __init__(self) -> None:
        self.errores: list[str] = []

    def validar(self, ruta: str | Path) -> dict:
        """Lee, parsea y valida un JSON. Lanza ValueError si el contrato no se cumple.

        Las fallas se registran en ``errores`` para reportarlas durante el
        Data Understanding. La verificación semántica de "entidades inventadas"
        requiere contrastar con el texto original y no se puede decidir solo
        desde un JSON.
        """
        archivo = Path(ruta)
        try:
            data = json.loads(archivo.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return self._error(f"JSON inválido en {archivo}: {exc}", exc)

        if not isinstance(data, dict):
            return self._error(f"{archivo} no contiene un objeto JSON.")

        faltantes = [campo for campo in self.CAMPOS_OBLIGATORIOS if campo not in data]
        if faltantes:
            return self._error(f"{archivo}: faltan campos {faltantes}")

        for campo in self.CAMPOS_LISTA:
            if not isinstance(data[campo], list):
                return self._error(f"{archivo}: '{campo}' debe ser una lista")

        for campo, claves in self.CAMPOS_OBJETO.items():
            for indice, elemento in enumerate(data[campo]):
                if not isinstance(elemento, dict):
                    return self._error(f"{archivo}: {campo}[{indice}] debe ser un objeto")
                faltan_claves = [clave for clave in claves if clave not in elemento]
                if faltan_claves:
                    return self._error(f"{archivo}: {campo}[{indice}] sin claves {faltan_claves}")

        for campo in ("delitos", "organizaciones", "lugares"):
            if any(not isinstance(valor, str) for valor in data[campo]):
                return self._error(f"{archivo}: cada elemento de '{campo}' debe ser texto")

        return data

    def _error(self, mensaje: str, causa: Exception | None = None):
        self.errores.append(mensaje)
        if causa:
            raise ValueError(mensaje) from causa
        raise ValueError(mensaje)

    def resumen_calidad(self, datos: list[dict]) -> dict[str, object]:
        """Resume faltantes del corpus para usarlo en el informe o gráficos."""
        total = len(datos)
        if not total:
            return {"total": 0, "errores_validacion": list(self.errores), "faltantes_pct": {}}
        faltantes = {
            campo: round(sum(d.get(campo) is None or d.get(campo) == "" or d.get(campo) == [] for d in datos) * 100 / total, 2)
            for campo in self.CAMPOS_OBLIGATORIOS
        }
        return {"total": total, "errores_validacion": list(self.errores), "faltantes_pct": faltantes}
