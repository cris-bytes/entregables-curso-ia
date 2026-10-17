# BiblioLab · LangChain, herramientas y evidencia

**Grupo X-Ray · Sesión 6**

Asistente local para una biblioteca universitaria ficticia. Consulta reglamentos, busca disponibilidad en un catálogo y calcula vencimientos con un calendario explícito. Los datos son originales del laboratorio; no describen a una universidad real.

## Abrir la entrega

- [Notebook principal](BiblioLab_LangChain.ipynb): problema, EDA, código, experimentos, respuestas y conclusiones.
- [Notebook en HTML](BiblioLab_LangChain.html): lectura con resultados sin instalar Python.
- [Guía de entrega](docs/ENTREGA.md) y [video](docs/VIDEO.md).
- [Video de demostración: 59 segundos](video/BiblioLab_demo.mp4), con ejecución real de Gradio y dos consultas citadas. Grabación sin narración.
- En este Mac: doble clic en `Abrir_Notebook.command` o `Iniciar_BiblioLab.command`.

## Qué cambia respecto al proyecto anterior

Este caso implementa un agente con LangChain y herramientas para datos estructurados y cálculo. Dos servidores exponen las capacidades; el cliente descubre sus contratos y las invoca. Se conservan recuperación documental y referencias, pero la respuesta también puede depender de un inventario o un cálculo verificable. La guía de la [sesión 6](https://github.com/Ohtar10/icesi-nlp/tree/main/Sesion6) usa clima y calculadora; aquí se sustituyen por un caso propio. Los hashes y enlaces a la revisión consultada están en `data/guide_sources.json`.

## Instalación reproducible

Python 3.12. Para los dos modelos se descargan aproximadamente 3 GB. Se recomienda un equipo con 16 GB de memoria; la inferencia en CPU puede ser considerablemente más lenta que en el equipo de referencia.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows, activar con `.venv\Scripts\activate`. Instalar [Ollama](https://ollama.com/download), y descargar los dos modelos con el servidor habitual de Ollama activo:

```bash
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
```

Configurar la URL de ese servidor antes de ejecutar. En macOS/Linux:

```bash
export BIBLIOLAB_OLLAMA_URL=http://127.0.0.1:11434
python -m jupyterlab BiblioLab_LangChain.ipynb
```

En PowerShell: `$env:BIBLIOLAB_OLLAMA_URL="http://127.0.0.1:11434"`.

En el Mac preparado para esta entrega, Ollama y los pesos están en `.runtime/`, y el proyecto usa `127.0.0.1:11435`. Los lanzadores lo inician automáticamente si hace falta. Esa carpeta es local y se excluye de GitHub y del ZIP; otro equipo debe instalar y descargar los modelos.

El notebook guarda las salidas reales. Para repetir toda la ejecución y exportar HTML:

```bash
python -m scripts.execute_notebook
```

Para abrir únicamente la aplicación:

```bash
python app.py
```

La primera descarga requiere internet; la aplicación y las herramientas funcionan localmente. No requieren claves ni llamadas a servicios de pago. Se fijan dependencias directas; `requirements-lock-macos-py312.txt` conserva el entorno probado completo. `models.lock.json` registra los digests y la cuantización; las etiquetas de Ollama pueden cambiar, por lo que debe verificarse ese archivo al reproducir.

## Diseño experimental

- 8 documentos, 17 secciones, 32 títulos y un calendario acotado al último trimestre de 2026.
- 16 configuraciones: TF-IDF por palabras, TF-IDF por caracteres, BM25 y RRF; fragmentos de 35/90 palabras y k de 1/3.
- Selección por 8 consultas de validación. Otras 12 consultas son exploratorias porque ya se observaron durante el desarrollo. Seis consultas adicionales se reservan para una comprobación posterior a congelar la propuesta.
- 4 estrategias con Qwen2.5 3B: modelo solo, RAG fijo, agente autónomo y flujo guiado. Comparación adicional de 1,5B con el mismo flujo guiado.
- Se conservan errores, llamadas, salidas de herramientas, citas y tiempos. Los chequeos automáticos de contenido son parciales; no se denominan exactitud factual.

No se entrenan pesos. El flujo guiado utiliza reglas explícitas, no selección autónoma. El modo predeterminado usa 3B y muestra fuentes de la última consulta. Una referencia válida no garantiza fidelidad. El asistente no registra préstamos ni reservas. La disponibilidad corresponde al corte **2026-10-16**, no al momento de la consulta.

## Organización

| Ruta | Contenido |
|---|---|
| `BiblioLab_LangChain.ipynb` | Notebook ejecutable y narrativa |
| `bibliolab/core.py` | Recuperación, catálogo, calendario y verificaciones |
| `bibliolab/server.py` | Servicios de normas y circulación |
| `bibliolab/assistant.py` | Agente, cadenas LangChain y flujo guiado |
| `bibliolab/evaluation.py` | EDA, métricas y experimentos |
| `data/` | Documentos, tablas, preguntas, procedencia y hashes |
| `results/` | Respuestas originales, tablas, revisión y gráficos |
| `tests/` | Pruebas de reglas y conexión real |
| `app.py` | Interfaz Gradio compartida con el notebook |

## Verificación

```bash
python -m pytest -q
```

La prueba de navegador y grabación requiere dependencias opcionales de `requirements-dev.txt`, Google Chrome instalado y `python -m playwright install ffmpeg`. Los registros de ejecución, pruebas y video permiten distinguir lo verificado de lo pendiente.

Verificación de referencia: **14/14 celdas ejecutadas sin errores, 17 pruebas aprobadas y video de 58,92 segundos**. Ver `results/notebook_execution.json`, `results/environment.json` y `results/video_recording.json`. La [revisión cualitativa](results/qualitative_review.md) documenta falsas abstenciones y errores de interpretación del modelo; estas comprobaciones técnicas no garantizan exactitud de todas sus respuestas.

## Fuentes técnicas

- [Notebooks de la sesión 6](https://github.com/Ohtar10/icesi-nlp/tree/main/Sesion6).
- [ChatOllama en LangChain](https://docs.langchain.com/oss/python/integrations/chat/ollama).
- [Adaptador utilizado](https://github.com/langchain-ai/langchain-mcp-adapters).
- [SDK de los servicios](https://github.com/modelcontextprotocol/python-sdk).
- [API de Ollama](https://docs.ollama.com/api/chat).

El material documental es de autoría propia para este laboratorio; esas fuentes técnicas no son la fuente de los reglamentos ficticios.
