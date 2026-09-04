"""Fábrica: elige el adaptador según URL o nombre de fuente."""

from __future__ import annotations

from src.adquisicion.base import CapturadorFuente
from src.adquisicion.biobio import CapturadorBioBio
from src.adquisicion.cooperativa import CapturadorCooperativa
from src.adquisicion.generico import CapturadorGenerico
from src.adquisicion.http import ClienteHTTP
from src.adquisicion.latercera import CapturadorLaTercera
from src.limpieza.limpiador import LimpiadorHTML


class FabricaCapturadores:
    """Devuelve el capturador más específico; si no hay match, el genérico."""

    def __init__(
        self,
        cliente: ClienteHTTP | None = None,
        limpiador: LimpiadorHTML | None = None,
    ) -> None:
        self.cliente = cliente or ClienteHTTP()
        self.limpiador = limpiador or LimpiadorHTML()
        self._especificos: list[CapturadorFuente] = [
            CapturadorBioBio(self.cliente),
            CapturadorCooperativa(self.cliente),
            CapturadorLaTercera(self.cliente),
        ]
        self.generico = CapturadorGenerico(self.cliente, self.limpiador)

    def para(self, url: str, fuente: str | None = None) -> CapturadorFuente:
        """Selecciona adaptador por dominio o columna `fuente` de urls.csv."""
        for capturador in self._especificos:
            if capturador.acepta(url, fuente):
                return capturador
        return self.generico
