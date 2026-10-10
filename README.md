# FinGuía · Asesor educativo de inversión con RAG

**Equipo:** X-ray

Un chatbot en español que explica conceptos de inversión con referencias verificables y un simulador de aportes. Funciona localmente, sin claves de API ni servicios pagados.

El caso distingue conceptos de fuentes oficiales, carteras **ficticias** y cálculos hipotéticos. No ejecuta operaciones ni consulta cotizaciones en tiempo real.

Para revisar sin ejecutar, abrir [la versión HTML del notebook](FinGuia_RAG_Inversion.html). El paquete `FinGuia_entregable.zip` reúne el material de entrega y excluye los modelos y el entorno virtual.

## Abrir en este Mac

1. Doble clic en **`Iniciar_FinGuia.command`** para abrir la aplicación.
2. Doble clic en **`Abrir_Notebook.command`** para abrir el notebook en JupyterLab.
3. Para el video, muestra y ejecuta la última celda de código del notebook: es la que inicia Gradio. Realiza dos consultas y muestra sus referencias.

Si macOS impide abrir el archivo `.command`, ejecútalo desde una terminal con `bash Iniciar_FinGuia.command` o `bash Abrir_Notebook.command`.

## Instalación en otra máquina

Python 3.12. Se necesitan varios GB de disco para los modelos; 16 GB de RAM son preferibles, aunque el generador utiliza media precisión para reducir consumo.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_models.py
python app.py
```

En Windows, activar con `.venv\Scripts\activate`. La primera descarga necesita internet. Después, modelos, documentos e inferencia quedan locales. Las citas incluyen enlaces externos opcionales; abrir esos sitios sí requiere internet.

Para reproducir el notebook completo:

```bash
python scripts/execute_notebook.py
```

Para abrirlo y ejecutar las celdas manualmente:

```bash
python -m jupyterlab FinGuia_RAG_Inversion.ipynb
```

Las dependencias directas están fijadas en `requirements.txt`; el entorno completo probado en macOS/Python 3.12 está en `requirements-lock-macos-py312.txt`. Las revisiones de modelos están fijadas en `models.lock.json`. No se versionan pesos, cachés, credenciales ni videos.

## Qué incluye

| Entregable | Ubicación |
|---|---|
| Notebook con EDA, experimentos y conclusiones | [FinGuia_RAG_Inversion.ipynb](FinGuia_RAG_Inversion.ipynb) |
| Aplicación Gradio | [app.py](app.py) |
| Corpus y procedencia | [data/manifest.json](data/manifest.json), [data/documents](data/documents) |
| Benchmark anotado y partición fija | [data/questions.json](data/questions.json) |
| Recuperación y generación | [finguia/core.py](finguia/core.py) |
| Evaluación reproducible | [finguia/evaluation.py](finguia/evaluation.py) |
| Simulador y pruebas matemáticas | [finguia/simulator.py](finguia/simulator.py), [tests/test_core.py](tests/test_core.py) |
| Métricas, respuestas crudas y gráficos | [results](results) |
| Guion del video de menos de 2 minutos | [docs/VIDEO.md](docs/VIDEO.md) |
| Mapa de la rúbrica y pendientes | [docs/ENTREGA.md](docs/ENTREGA.md) |

## Diseño experimental

El corpus tiene 10 documentos y 28 secciones; 26 secciones son vigentes. Siete documentos son síntesis propias de páginas de SEC/Investor.gov y FINRA, con atribución; tres son material del laboratorio. Las fichas Horizonte no representan inversiones disponibles. Se conservan documentos locales con SHA-256 para repetir el análisis aunque cambien las webs.

Se comparan TF-IDF, BM25, embeddings multilingual-E5-small e híbrido RRF, con fragmentos de 32/64/128 palabras y k=1/3/5. Son 36 configuraciones. Validación tiene 12 preguntas; test tiene 24. La configuración y el umbral se eligen solo con validación. El generador compara Qwen2.5 de 0.5B y 1.5B con una salida extractiva; esa comparación es exploratoria y conserva errores originales.

Se construye un índice: **no se entrenan los pesos de los modelos**. La comprobación de IDs citados no garantiza fidelidad factual. Cuando el generador no cita correctamente, la aplicación identifica expresamente el reemplazo por fragmentos.

En la ejecución de referencia, el recuperador seleccionado es E5 con secciones de hasta 128 palabras y k=3: Recall por sección de 97,2 % y toda la evidencia recuperada en 17 de 18 preguntas respondibles de test. Son métricas de recuperación en un corpus pequeño; no representan precisión financiera ni porcentaje de respuestas correctas.

## Pruebas

```bash
python -m pytest -q
python scripts/run_experiments.py --generation
```

La prueba visual opcional requiere `playwright==1.55.0` y Chrome instalado (o `python -m playwright install chromium` fuera de macOS):

```bash
python scripts/smoke_app.py
```

Los modelos pequeños pueden equivocarse. El proyecto analiza fallos de recuperación multifuente, mezcla de versiones, cifras intercambiadas y preguntas sin información suficiente. Los supuestos del simulador están documentados en D10 y los escenarios no son pronósticos.

Verificación final: 19 celdas ejecutadas desde un kernel limpio sin errores, 14 pruebas de código aprobadas y prueba de navegador con referencias, enlaces, simulador y vista móvil. Las ocho preguntas adicionales revelaron errores de abstención y citas; están documentados en [la revisión cualitativa](results/qualitative_review.md). Que el programa ejecute no implica que todas sus respuestas sean correctas.
