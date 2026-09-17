# CHECKLIST — Avance del laboratorio (25%)

Pipeline de noticias delictuales y Observable (Lab 01/02). La columna `[x]`
marca lo implementado; `[ ]` lo que queda pendiente. Última actualización:
se implementó la etapa **vault de Obsidian**.

## Cómo ejecutar

```bash
conda activate lab-noticias-obsidian
python main.py obsidian    # lee data/json/*.json → obsidian_vault/
```

## Estado por etapa del pipeline

- [x] **Descubrir** — `src/adquisicion/google_news.py` (RSS de Google News → `data/urls.csv`).
- [x] **Captura / limpieza** — fábrica de capturadores, adaptadores (BioBio, Cooperativa, La Tercera), fallback genérico y `LimpiadorHTML`.
- [x] **Extracción Gemini** — `src/extraccion/gemini.py` (implementación mínima ejecutable; mejoras opcionales pendientes).
- [x] **Validación JSON** — `src/validacion/validador.py` (campos obligatorios y tipos lista).
- [x] **Vault de Obsidian** — `src/conocimiento/obsidian.py` (NUEVO: realizado en este avance).
- [ ] **Análisis / Data Understanding** — `src/analisis/explorador.py` (sigue siendo TODO del alumno).

## Checklist — Vault de Obsidian (implementado en este avance)

- [x] `EscritorVaultObsidian.escribir_noticia(data)` — genera `obsidian_vault/Noticias/N001.md`
  - [x] Frontmatter YAML con `id`, `fecha_publicacion`, `fuente`, `url`.
  - [x] Secciones enlazadas: Resumen, Delitos, Personas, Organizaciones, Lugares, Objetos y Relaciones con `[[wiki-links]]`.
- [x] `EscritorVaultObsidian.escribir_entidades(noticias)` — una nota por entidad:
  - [x] `Delitos/` (noticias, personas, organizaciones y lugares asociados).
  - [x] `Personas/` (rol observado, delitos, organizaciones y lugares).
  - [x] `Organizaciones/` (noticias, delitos, personas y lugares).
  - [x] `Lugares/` (noticias, delitos, personas y organizaciones).
  - [x] `Objetos/` (noticias donde aparece).
  - [x] `Relaciones/` — una nota por **tipo** de relación (`INVESTIGADO_POR`, `OPERA_EN`, …) con cada instancia trazable a su noticia.
- [x] `EscritorVaultObsidian.escribir_indice(noticias)` — genera `obsidian_vault/00_Indice.md` navegable.
- [x] `EscritorVaultObsidian.escribir_vault(noticias)` — orquesta noticia + entidades + índice.
- [x] `cargar_noticias_desde_disco(dir_json)` — lee todos los JSON de `data/json/` (helper nuevo).

### Convención de enlaces

- [x] Nombres de archivo estables con `slugify` (`Tráfico de drogas` → `Trafico_de_drogas.md`).
- [x] Enlaces `[[slug|Nombre original]]` para que Obsidian resuelva el archivo y muestre el nombre legible.

### Integración

- [x] `src/pipeline.py::ejecutar_obsidian` ahora carga los JSON reales y genera el vault (antes pasaba `[]`).
- [x] Exports actualizados en `src/conocimiento/__init__.py` (`cargar_noticias_desde_disco`).
- [x] Docstrings de `main.py`/`src/pipeline.py` y tabla de estados en `README.md` actualizados.

### Limpieza de datos de prueba (segunda iteración)

- [x] Eliminado `data/json/ejemplo_N001.json` (fixture de prueba, sin relación con las 50 URLs reales).
- [x] Eliminadas las notas `.md` de prueba en `obsidian_vault/` (se conservan carpetas y `.gitkeep`).
- [x] `_limpiar()` en `EscritorVaultObsidian.escribir_vault`: borra `.md` previos antes de regenerar → sin notas huérfanas entre corridas.
- [x] `cargar_noticias_desde_disco` filtra `ejemplo_*` (defensa para futuros fixtures).
- [x] `README.md`: eliminadas las referencias al fixture.

## Pruebas realizadas

- [x] `python main.py obsidian` con el fixture `data/json/ejemplo_N001.json` → generó el vault (verificado durante el desarrollo).
- [x] Verificación manual del contenido: `Noticias/N001.md`, `Delitos/Trafico_de_drogas.md`, `Relaciones/INVESTIGADO_POR.md` y `00_Indice.md` correctos.
- [x] Prueba con 3 noticias sintéticas (fuera del repo): agrupación por delito compartido, enlaces cruzados personas/organizaciones/lugares y notas de relación sin errores.
- [x] `python main.py obsidian` con `data/json/` vacío → avisa y no toca el vault.
- [x] Prueba sintética de limpieza: con corpus vacío tras una corrida previa no quedan notas huérfanas, y un `ejemplo_*.json` no genera notas.
- [x] `python main.py analizar` sigue avisando el `TODO(alumno)` sin fallar en silencio.

## Pendiente (siguiente 75%)

- [ ] Extracción: reintentos ante 429/timeouts y recorte de textos largos en `src/extraccion/gemini.py` (mejoras opcionales).
- [ ] Validación: registrar estadísticas de nulos/tipos/entidades inventadas para Data Understanding.
- [ ] **Data Understanding**: `noticias_por_fuente`, `delitos_frecuentes`, `lugares_frecuentes`, `campos_faltantes`, `evolución_temporal` en `src/analisis/explorador.py`.
- [ ] Generar el corpus real completo: `python main.py descubrir` → `capturar` → `extraer` (requiere `GEMINI_API_KEY` en `.env`).
- [ ] Auditoría manual de una muestra de noticias procesadas (≥10) y corrección de nombres inconsistentes.
- [ ] Abrir `obsidian_vault/` en Obsidian y verificar el grafo de relaciones.

## Notas

- No se leyó ni modificó `.env` (solo se usa `.env.example` como referencia).
- Todos los datos de prueba fueron eliminados. El vault se generará recién cuando existan los JSON reales en `data/json/`.