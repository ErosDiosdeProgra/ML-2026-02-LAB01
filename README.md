# Laboratorio: noticias delictuales, LLM y Obsidian

Pipeline académico para transformar **noticias delictuales no estructuradas** en un grafo de conocimiento en Obsidian.

El repositorio cubre dos entregas:

1. **Lab 01:** captura (Google News + medios chilenos) y limpieza de texto.
2. **Lab 02:** extracción con Gemini, validación JSON, **vault de Obsidian** y gráficos de **Data Understanding**.

La implementación de Gemini es **mínima y ejecutable**, con reintentos ante
429/timeouts y recorte de textos largos ya incluidos.

No se entrena clustering. Los grupos de noticias se forman por **relaciones explícitas** (mismo delito, persona, organización o lugar).

## Requisitos

- [Conda](https://docs.conda.io/) (Miniconda o Anaconda)
- Uso académico de sitios de prensa: respetar términos de uso, no sobrecargar servidores
- Cuenta de [Google AI Studio](https://aistudio.google.com/) y `GEMINI_API_KEY` para `python main.py extraer`

## Entorno conda

No use `pip install` ni `requirements.txt`. El entorno oficial es `environment.yml`.

```bash
conda env create -f environment.yml
conda activate lab-noticias-obsidian
```

Para recrearlo:

```bash
conda env update -f environment.yml --prune
```

Copie las variables de entorno (la clave de Gemini **nunca** se sube a Git):

```bash
cp .env.example .env
# edite .env y complete GEMINI_API_KEY
```

## Cómo ejecutar

Desde la raíz del repositorio, con el entorno activado:

```bash
python main.py descubrir   # RSS de Google News → actualiza data/urls.csv
python main.py capturar    # URLs → data/raw/*.html y data/processed/*.txt
python main.py extraer     # Gemini → data/json/*.json (requiere GEMINI_API_KEY)
python main.py obsidian    # data/json/*.json → vault Markdown (obsidian_vault/)
python main.py analizar    # gráficos de Data Understanding → data/analisis/
python main.py pipeline    # flujo completo
```

El identificador `id_noticia` se conserva en todo el flujo: `N001.html` → `N001.txt` → `N001.json` → `Noticias/N001.md`.

El escritor de Obsidian se probó durante el desarrollo con un JSON de ejemplo, que ya fue eliminado para no interferir con el corpus real. Ejecute `python main.py obsidian` una vez que `data/json/` contenga los JSON reales.

## Qué está implementado y qué debe completar

| Módulo | Estado | Qué hace |
| --- | --- | --- |
| `src/adquisicion/` | Listo | Google News (RSS), fábrica de capturadores, adaptadores BioBio / Cooperativa / La Tercera, fallback genérico |
| `src/limpieza/` | Listo | `LimpiadorHTML`: quita menús, scripts y líneas cortas |
| `src/modelos.py` | Listo | Dataclasses del contrato JSON |
| `src/pipeline.py` + `main.py` | Listo | Orquestación por etapas |
| `src/conocimiento/utilidades.py` | Listo | `slugify` y `[[wiki-links]]` |
| `src/extraccion/` | Listo | Prompt estructurado, recorte de textos, reintentos y `data/json/` |
| `src/validacion/` | Listo | JSON, campos obligatorios, tipos y resumen de calidad |
| `src/conocimiento/obsidian.py` | Listo | Notas Markdown enlazadas por noticia y entidad + `00_Indice.md` |
| `src/analisis/` | Listo | Cobertura por fuente y por categoría (tema), noticias con/sin delitos, delitos, lugares, faltantes y evolución temporal |

Si ejecuta una etapa pendiente, el programa imprime una pista y **no falla en silencio**.

## Diseño en breve

`PipelineLaboratorio` coordina:

1. `DescubridorGoogleNews` consulta el RSS público (`hl=es-419`, `gl=CL`). **No scrapea** el HTML de `news.google.com`. Resuelve redirects hasta la URL del medio y agrega filas a `data/urls.csv` sin duplicar.
2. `FabricaCapturadores.para(url, fuente)` elige un adaptador por dominio. Si el selector CSS no encuentra el artículo, usa `CapturadorGenerico` (fallback).
3. El HTML queda en `data/raw/` y el texto útil en `data/processed/`.
4. `ExtractorGemini` lee el texto, llama a Gemini y guarda JSON en `data/json/`. `ValidadorJSON` comprueba el contrato.
5. `EscritorVaultObsidian` convierte cada JSON en notas Markdown enlazadas dentro de `obsidian_vault/`.

Clases principales: `PipelineLaboratorio` coordina descubridor, fábrica de capturadores, extractor Gemini, validador y escritor Obsidian.

## Contrato JSON

Cada noticia extraída debe incluir: `id_noticia`, `titulo`, `fecha_publicacion`, `fuente`, `url`, `resumen`, `delitos`, `personas` (nombre y rol), `organizaciones`, `lugares`, `objetos`, `relaciones` (`origen`, `tipo`, `destino`).

Si un dato no aparece en el texto, use `null` o una lista vacía. **No invente** entidades ni culpabilidad.

## Vault de Obsidian (objetivo del alumno)

```
obsidian_vault/
├── 00_Indice.md
├── Noticias/
├── Delitos/
├── Personas/
├── Organizaciones/
├── Lugares/
├── Objetos/
└── Relaciones/
```

Las relaciones se expresan con enlaces `[[...]]`. No se usa SQLite, MongoDB ni Neo4j.

## Datos de ejemplo

- [data/consultas.csv](data/consultas.csv): búsquedas semilla para Google News
- [data/urls.csv](data/urls.csv): noticias públicas (BioBioChile, Cooperativa, La Tercera, Emol)

Las URLs de prensa cambian con el tiempo. Si una descarga falla, el lote continúa y registra el error. Puede ampliar `urls.csv` a mano (30–50 URLs verificadas, como pide la guía).

## Ética

- El análisis es académico y exploratorio.
- Cite siempre la fuente y conserve la URL.
- Los roles (detenido, imputado, acusado, condenado, víctima, testigo) **no son equivalentes**.
- No afirme culpabilidad si la noticia no lo dice de forma explícita.
- Respete los términos de uso de cada medio y de Google News (solo RSS).

## Presentación del laboratorio

Las presentaciones Beamer y los Colab viven en `docs/` **solo en la copia local** (la carpeta está en `.gitignore` y no se publica en GitHub).

## Estructura del repositorio

```
main.py                 Orquestador CLI
environment.yml         Entorno conda
src/pipeline.py         PipelineLaboratorio
src/adquisicion/        Captura (implementada)
src/limpieza/           Limpieza HTML (implementada)
src/extraccion/         Gemini (implementación simple)
src/validacion/         Validación JSON (implementación simple)
src/conocimiento/       Interfaz Obsidian + slugify
src/analisis/           Interfaz Data Understanding
data/                   URLs, HTML, texto, JSON
obsidian_vault/         Bóveda (a generar por el alumno)
```
