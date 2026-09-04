"""Excepciones del laboratorio."""


class EtapaPendienteAlumno(NotImplementedError):
    """Se lanza cuando el alumno aún no completa un módulo TODO(alumno)."""

    def __init__(self, modulo: str, pista: str) -> None:
        self.modulo = modulo
        self.pista = pista
        mensaje = (
            f"\n[TODO(alumno)] El módulo '{modulo}' aún no está implementado.\n"
            f"    {pista}\n"
        )
        super().__init__(mensaje)


class CapturaError(RuntimeError):
    """Fallo al descargar o procesar una noticia (no detiene el lote)."""
