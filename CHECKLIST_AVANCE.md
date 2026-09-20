# CHECKLIST — Avance del laboratorio

Pipeline de noticias delictuales y Obsidian (Lab 01/02). La columna `[x]`
marca lo implementado y verificado; `[ ]` lo que queda pendiente (tareas
manuales del alumno).

Última actualización: **pipeline 100 % ejecutable**. Se completó la etapa de
**análisis / Data Understanding**, se reforzó la extracción Gemini (reintentos
y recorte), se corrigió un problema del entorno (gráficos matplotlib) y se
generó el corpus real completo (50 noticias → JSON → vault → gráficos).

## Cómo ejecutar

```bash
conda activate lab-noticias-obsidian
python main.py descubrir    # RSS de Google News → data/urls.csv
python main.py capturar     # URLs → data/raw y data/processed
python main.py extraer      # Gemini → data/json (requiere GEMINI_API_KEY en .env)
python main.py obsidian     # data/json → obsidian_vault/
python main.py analizar     # gráficos de Data Understanding → data/analisis/
python main.py pipeline     # flujo completo
```

## Estado por etapa del pipeline

- [x] **Descubrir** — `src/adquisicion/google_news.py` (RSS de Google News → `data/urls.csv`).
- [x] **Captura / limpieza** — fábrica de capturadores, adaptadores (BioBio, Cooperativa, La Tercera, Emol), fallback genérico y `LimpiadorHTML`.
- [x] **Extracción Gemini** — `src/extraccion/gemini.py` con reintentos ante 429/timeouts (`MAX_INTENTOS` + backoff) y recorte de textos largos (`MAX_CARACTERES_TEXTO`).
- [x] **Validación JSON** — `src/validacion/validador.py` (campos obligatorios, tipos lista, claves de objetos) y `resumen_calidad` para el informe.
- [x] **Vault de Obsidian** — `src/conocimiento/obsidian.py` (notas por noticia y entidad, relaciones e índice).
- [x] **Análisis / Data Understanding** — `src/analisis/explorador.py` con `noticias_por_fuente`, `delitos_frecuentes`, `lugares_frecuentes`, `campos_faltantes` y `evolucion_temporal`.

## Checklist — Vault de Obsidian

- [x] `EscritorVaultObsidian.escribir_noticia(data)` — genera `obsidian_vault/Noticias/N001.md`
  - [x] Frontmatter YAML con `id`, `fecha_publicacion`, `fuente`, `url`.
  - [x] Secciones enlazadas: Resumen, Delitos, Personas, Organizaciones, Lugares, Objetos y Relaciones con `[[wiki-links]]`.
- [x] `EscritorVaultObsidian.escribir_entidades(noticias)` — una nota por entidad:
  - [x] `Delitos/`, `Personas/`, `Organizaciones/`, `Lugares/`, `Objetos/`.
  - [x] `Relaciones/` — una nota por **tipo** de relación (`INVESTIGADO_POR`, `OPERA_EN`, …) con cada instancia trazable a su noticia.
- [x] `EscritorVaultObsidian.escribir_indice(noticias)` — genera `obsidian_vault/00_Indice.md` navegable.
- [x] `EscritorVaultObsidian.escribir_vault(noticias)` — orquesta noticia + entidades + índice.
- [x] `cargar_noticias_desde_disco(dir_json)` — lee todos los JSON de `data/json/` (omite fixtures `ejemplo_*`).

### Convención de enlaces

- [x] Nombres de archivo estables con `slugify` (`Tráfico de drogas` → `Trafico_de_drogas.md`).
- [x] Enlaces `[[slug|Nombre original]]` para que Obsidian resuelva el archivo y muestre el nombre legible.

### Integración

- [x] `src/pipeline.py::ejecutar_obsidian` carga los JSON reales y genera el vault.
- [x] Exports actualizados en `src/conocimiento/__init__.py`.
- [x] `_limpiar()` en `escribir_vault`: borra `.md` previos antes de regenerar → sin notas huérfanas.

## Checklist — Data Understanding (implementado en este avance)

- [x] `ExploradorDatos.noticias_por_fuente()` — cobertura por medio (JSON o, si faltan, `urls.csv` como respaldo).
- [x] `ExploradorDatos.noticias_por_categoria()` — distribución por tema (`categoria_busqueda` de `urls.csv`); representa también las noticias no delictuales (vivienda, emergencias, economía).
- [x] `ExploradorDatos.cobertura_delictual()` — noticias con delitos vs. sin delitos (26 de 50 en el corpus real).
- [x] `ExploradorDatos.delitos_frecuentes()` — top 10 delitos mencionados.
- [x] `ExploradorDatos.lugares_frecuentes()` — top 10 lugares mencionados.
- [x] `ExploradorDatos.campos_faltantes()` — porcentaje de noticias sin cada campo del contrato.
- [x] `ExploradorDatos.evolucion_temporal()` — noticias por mes.
- [x] Gráficos PNG en `data/analisis/` con backend matplotlib "Agg" (sin display) y resumen impreso al final.
- [x] `src/pipeline.py::ejecutar_analisis` ejecuta la etapa completa.

## Checklist — Corpus real y robustez de extracción

- [x] Reintentos ante 429/timeouts en `src/extraccion/gemini.py` (`_consultar_con_reintentos`).
- [x] Recorte de textos largos en `construir_prompt` (24 000 caracteres).
- [x] `ValidadorJSON.resumen_calidad` — estadísticas de nulos/errores para el informe.
- [x] Corpus real generado: `capturar` → 50 de 50 textos; `extraer` → 50 de 50 JSON validados (8 requirieron reintento por contrato JSON no cumplido y fueron corregidos con una segunda pasada).
- [x] Vault real: `obsidian_vault/` con 50 noticias y sus entidades/relaciones/índice.
- [x] Data Understanding real: 5 gráficos en `data/analisis/`.

## Infraestructura / entorno (corrección aplicada)

- [x] En Windows el gráfico matplotlib fallaba con excepción nativa `0xc06d007f`
  (el BLAS Intel MKL del entorno crasheaba en operaciones `matmul`). Se
  reinstaló el stack BLAS con OpenBLAS (`conda install blas=*=openblas`) y los
  gráficos funcionan.
- [x] `main.py` fuerza `stdout`/`stderr` a UTF-8 para que la consola Windows
  (cp1252) pueda imprimir símbolos como `→` al redirigir la salida.
- [x] Se respetó `.env`: nunca se leyó su contenido; `GEMINI_API_KEY` se usó
  solo a través del propio pipeline (`load_dotenv` de `src/config.py`).

## Pendiente (manual / del alumno)

- [ ] Auditoría manual de una muestra de noticias procesadas (≥10) y corrección
      de nombres inconsistentes de entidades entre noticias.
- [ ] Abrir `obsidian_vault/` en Obsidian y verificar el grafo de relaciones.
- [ ] Verificación semántica de "entidades inventadas" contrastando JSON vs.
      texto original (no automatizable solo desde el JSON).