# Laboratorio: noticias delictuales, LLM y Obsidian

Pipeline académico para transformar **noticias delictuales no estructuradas** en un grafo de conocimiento en Obsidian.

El repositorio es un *starter*: la **captura** (Google News + medios chilenos) ya funciona. Gemini, la validación JSON, el vault de Obsidian y las visualizaciones son **interfaces** que el alumno debe completar (`TODO(alumno)`).

No se entrena clustering. Los grupos de noticias se forman por **relaciones explícitas** (mismo delito, persona, organización o lugar).

## Requisitos

- [Conda](https://docs.conda.io/) (Miniconda o Anaconda)
- Uso académico de sitios de prensa: respetar términos de uso, no sobrecargar servidores
- Cuenta de Google AI Studio (cuando implemente Gemini)

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
# edite .env y complete GEMINI_API_KEY cuando implemente la extracción
```

## Cómo ejecutar

Desde la raíz del repositorio, con el entorno activado:

```bash
python main.py descubrir   # RSS de Google News → actualiza data/urls.csv
python main.py capturar    # URLs → data/raw/*.html y data/processed/*.txt
python main.py extraer     # TODO(alumno): Gemini
python main.py obsidian    # TODO(alumno): vault Markdown
python main.py analizar    # TODO(alumno): Data Understanding
python main.py pipeline    # descubrir + capturar; avisa etapas pendientes
```

El identificador `id_noticia` se conserva en todo el flujo: `N001.html` → `N001.txt` → `N001.json` → `Noticias/N001.md`.

## Qué está implementado y qué debe completar

| Módulo | Estado | Qué hace |
| --- | --- | --- |
| `src/adquisicion/` | Listo | Google News (RSS), fábrica de capturadores, adaptadores BioBio / Cooperativa / La Tercera, fallback genérico |
| `src/limpieza/` | Listo | `LimpiadorHTML`: quita menús, scripts y líneas cortas |
| `src/modelos.py` | Listo | Dataclasses del contrato JSON |
| `src/pipeline.py` + `main.py` | Listo | Orquestación por etapas |
| `src/conocimiento/utilidades.py` | Listo | `slugify` y `[[wiki-links]]` para cuando complete Obsidian |
| `src/extraccion/` | `TODO(alumno)` | Prompt + llamada a Gemini + JSON |
| `src/validacion/` | `TODO(alumno)` | `json.loads` y campos obligatorios |
| `src/conocimiento/obsidian.py` | `TODO(alumno)` | Notas Markdown enlazadas |
| `src/analisis/` | `TODO(alumno)` | Gráficos de calidad y cobertura |

Si ejecuta una etapa pendiente, el programa imprime una pista y **no falla en silencio**.

## Diseño en breve

`PipelineLaboratorio` coordina:

1. `DescubridorGoogleNews` consulta el RSS público (`hl=es-419`, `gl=CL`). **No scrapea** el HTML de `news.google.com`. Resuelve redirects hasta la URL del medio y agrega filas a `data/urls.csv` sin duplicar.
2. `FabricaCapturadores.para(url, fuente)` elige un adaptador por dominio. Si el selector CSS no encuentra el artículo, usa `CapturadorGenerico` (fallback).
3. El HTML queda en `data/raw/` y el texto útil en `data/processed/`.
4. El alumno completa Gemini → JSON en `data/json/` → vault en `obsidian_vault/`.

Clases principales: diagrama PlantUML en [docs/diseno-poo.puml](docs/diseno-poo.puml) (imagen [docs/diseno-poo.png](docs/diseno-poo.png) incluida en la presentación). Regenerar:

```bash
cd docs
plantuml -tpng diseno-poo.puml
# o: curl -sS -X POST --data-binary @diseno-poo.puml https://kroki.io/plantuml/png -o diseno-poo.png
```

## Contrato JSON

Cada noticia extraída debe incluir: `id_noticia`, `titulo`, `fecha_publicacion`, `fuente`, `url`, `resumen`, `delitos`, `personas` (nombre y rol), `organizaciones`, `lugares`, `objetos`, `relaciones` (`origen`, `tipo`, `destino`).

Si un dato no aparece en el texto, use `null` o una lista vacía. **No invente** entidades ni culpabilidad.

## Vault de Obsidian (objetivo)

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
- [data/urls.csv](data/urls.csv): cuatro noticias públicas (BioBioChile, Cooperativa, La Tercera)

Las URLs de prensa cambian con el tiempo. Si una descarga falla, el lote continúa y registra el error. Puede ampliar `urls.csv` a mano (30–50 URLs verificadas, como pide la guía).

## Ética

- El análisis es académico y exploratorio.
- Cite siempre la fuente y conserve la URL.
- Los roles (detenido, imputado, acusado, condenado, víctima, testigo) **no son equivalentes**.
- No afirme culpabilidad si la noticia no lo dice de forma explícita.
- Respete los términos de uso de cada medio y de Google News (solo RSS).

## Presentación del laboratorio

Fuentes LaTeX en `docs/` (tema Auriga, mismo estilo de la guía). El diagrama de clases es `diseno-poo.png` (junto al `.tex`). Compilación:

```bash
cd docs
pdflatex lab-noticias-obsidian.tex
```

Si usa LuaLaTeX y tiene las fuentes Raleway / Lato / Hack, el tema las cargará. Con pdfLaTeX se usan las fuentes por defecto, sin cambiar colores ni layout.

## Estructura del repositorio

```
main.py                 Orquestador CLI
environment.yml         Entorno conda
src/pipeline.py         PipelineLaboratorio
src/adquisicion/        Captura (implementada)
src/limpieza/           Limpieza HTML (implementada)
src/extraccion/         Interfaz Gemini
src/validacion/         Interfaz JSON
src/conocimiento/       Interfaz Obsidian + slugify
src/analisis/           Interfaz Data Understanding
data/                   URLs, HTML, texto, JSON
obsidian_vault/         Bóveda (a generar)
docs/                   Presentación Beamer
```
