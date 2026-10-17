from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(text):cells.append(nbf.v4.new_markdown_cell(text.strip()))
def code(text):cells.append(nbf.v4.new_code_cell(text.strip()))

md('''# BiblioLab · Un asistente con LangChain y herramientas verificables
**Grupo X-Ray · Sesión 6 · Caso propio**

Una biblioteca universitaria ficticia necesita responder preguntas sobre sus reglas, su catálogo y fechas de devolución. Una respuesta convincente puede ser incorrecta si confunde un título existente con uno disponible, usa días calendario en lugar de hábiles o inventa un dato que no figura en el reglamento.

Este notebook construye un chatbot local, contrasta cuatro estrategias, analiza errores y ofrece una interfaz Gradio con evidencia visible. Los documentos, títulos y cifras son originales y ficticios. **No representan políticas ni inventario de Icesi ni de otra institución real.**''')
md('''## 1. Problema, propuesta y relación con la guía

Los usuarios son estudiantes, docentes y egresados que necesitan una respuesta verificable antes de acudir al mostrador. Hay tres clases de preguntas: normas en texto, disponibilidad tabular y cálculos que combinan reglas con un calendario. Un RAG documental resuelve solo parte del problema: no basta con recuperar una regla para calcular correctamente una fecha o conocer el inventario.

La [sesión 6](https://github.com/Ohtar10/icesi-nlp/tree/main/Sesion6) introduce herramientas, agentes, servicios separados y una interfaz. Este caso conserva esa progresión: funciones Python → servicios con contratos → adaptador de LangChain → agente y flujo guiado → Gradio. Sustituye los ejemplos de clima y calculadora por **búsqueda de reglamentos, catálogo y vencimientos**. La revisión y los hashes de los notebooks consultados están en `data/guide_sources.json`.

Se usan dos servidores MCP reales, descubiertos e invocados por el adaptador de LangChain. Para la ejecución local se usa stdio y procesos gestionados automáticamente; también está implementada la opción HTTP. Esta decisión evita mantener dos terminales adicionales. El LLM se ejecuta con Ollama.

**Hipótesis:** las herramientas mejorarán el acceso a datos y la aritmética; el flujo guiado reducirá omisiones de herramientas; un modelo mayor podría mejorar la redacción y las citas. Estas hipótesis se evalúan por separado. No se entrena ni se ajusta ningún peso: se indexa el corpus y se comparan configuraciones de inferencia.''')
md('''## 2. Reproducción

Python 3.12, dependencias en `requirements.txt` y entorno completo probado en `requirements-lock-macos-py312.txt`. Antes de ejecutar, instalar dependencias y descargar `qwen2.5:3b` y `qwen2.5:1.5b` en Ollama como indica `README.md`. La descarga inicial necesita internet; las consultas posteriores son locales y no requieren claves.

En este Mac, `Abrir_Notebook.command` abre el entorno preparado. La ejecución completa incluye 60 respuestas comparativas, controles adicionales y pruebas; puede tardar varios minutos. Los resultados se recalculan, no se sustituyen por respuestas precargadas. Temperatura 0 y semilla 42 reducen variación; GPU, librerías o versiones diferentes pueden cambiar texto y latencia. Los hashes de los modelos se conservan en `models.lock.json`.

Los módulos del proyecto contienen implementación reutilizable; las celdas muestran las partes relevantes, ejecutan los experimentos y desarrollan la interpretación.''')
code('''import os, sys, json, inspect, subprocess, platform
from pathlib import Path
ROOT = Path.cwd()
assert (ROOT/'bibliolab').is_dir(), 'Abre el notebook desde la carpeta BiblioLab.'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.runtime/matplotlib'))
import pandas as pd
import numpy as np
from IPython.display import display, Markdown, Image
from bibliolab.core import *
from bibliolab.assistant import Assistant, make_client, SYSTEM, MODEL
from bibliolab.evaluation import eda, run_retrieval, run_generation, run_followups, run_holdout
from bibliolab.runtime import ensure_ollama
model_info = ensure_ollama()
print('Python:', platform.python_version(), '| Modelo de la interfaz:', MODEL)
print('Digest del modelo:', model_info['digest'])
display(pd.DataFrame(read_json(DATA/'guide_sources.json')['files'])[['name','sha256']])''')
md('''## 3. Datos, procedencia y calidad

El corpus contiene 8 documentos y 17 secciones con identificadores estables. El catálogo contiene 32 títulos de cuatro áreas. Los estados de ejemplares son excluyentes: `disponibles = total − prestados − reservados − consulta_sala`. El calendario es una simulación explícita entre octubre y diciembre de 2026; no se presenta como calendario oficial.

Las fuentes fueron escritas para probar reglas, excepciones y datos ausentes; se generan mediante `scripts/build_data.py` y se versionan con hashes. No hay datos personales. El catálogo tiene corte fijo, por lo que decir “disponible ahora” sería incorrecto.

Las preguntas anotadas fueron creadas por el mismo autor del laboratorio: permiten comparar variantes de forma controlada, pero no constituyen una muestra representativa de usuarios reales.''')
code('''sections, books, checks = eda()
display(pd.Series(checks, name='Control de calidad'))
display(books.head(8))
display(sections.drop(columns='text'))
display(Image(filename=str(ROOT/'results/figures/01_documentos.png')))
display(Image(filename=str(ROOT/'results/figures/02_catalogo.png')))''')
code('''display(Markdown(f"""**Lectura del EDA.** Hay {checks['unavailable_titles']} títulos sin ejemplares disponibles, aunque sí existen en el catálogo. Por tanto, la mera coincidencia de un título no prueba disponibilidad. El {checks['availability_rate']:.1%} de los ejemplares está disponible al corte. No se encontraron secciones vacías, duplicados exactos ni valores ausentes.

Las secciones son cortas (mediana: {sections.words.median():.0f} palabras), lo que hace razonable comparar fragmentos de 35 y 90 palabras. Las cuatro áreas tienen igual cantidad de títulos porque el corpus es sintético: ese equilibrio es una decisión de construcción, no un hallazgo sobre bibliotecas reales."""))''')
md('''## 4. Herramientas: separar evidencia, cálculo y lenguaje

`buscar_normas` devuelve fragmentos con IDs; `buscar_catalogo` consulta registros y calcula disponibilidad; `calcular_devolucion` cuenta días hábiles y conserva las fechas incluidas y excluidas. El cálculo exige perfil y fecha explícitos, rechaza días cerrados y no extrapola más allá del calendario. Ninguna herramienta modifica datos.

La trazabilidad importa más que la fluidez: una fecha se puede contrastar con el listado de días contados, y un inventario con las columnas originales. A continuación se muestra la implementación, no una simulación de tool calling.''')
code('''from bibliolab.server import make_server
display(Markdown('```python\\n'+inspect.getsource(make_server)+'\\n```'))
display(Markdown('```python\\n'+inspect.getsource(due_date)+'\\n```'))
display(due_date('estudiante', '2026-10-09'))
display(search_catalog('Visualización con gráficos'))''')
md('''### Comprobación del contrato sin el modelo

Primero se inicializa una sesión, se descubren herramientas y se llama al servicio de circulación. Esta etapa comprueba la conexión y el cálculo sin atribuir al LLM un resultado producido por Python.''')
code('''from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
parameters = StdioServerParameters(command=sys.executable, args=['-m','bibliolab.server','circulacion'], cwd=str(ROOT))
async with stdio_client(parameters) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        available = await session.list_tools()
        calculated = await session.call_tool('calcular_devolucion', {'perfil':'estudiante','fecha_retiro':'2026-10-09'})
        print('Herramientas descubiertas:', [t.name for t in available.tools])
        print(calculated.content[0].text)''')
md('''## 5. Experimentos de recuperación

La primera exploración usó TF-IDF por palabras, BM25 y fusión RRF. Sus archivos originales están en `results/exploratory_baseline`. Se observaron fallos con variantes como “renovar” y “renovación”, lo que motivó añadir TF-IDF por caracteres (`char_wb`, n-gramas 3 a 5). Los caracteres ayudan con variaciones morfológicas, pero no son embeddings semánticos.

La cuadrícula final tiene **16 configuraciones**: 4 métodos × 2 tamaños × 2 valores de k (1 y 3). Se elige por Recall de validación y luego MRR; los desempates prefieren menor k y secciones completas. RRF combina rangos con constante 60, no puntuaciones de escalas distintas.

Las 8 preguntas de validación seleccionan parámetros. Las otras 12 preguntas se conservan como evaluación exploratoria: **ya se observaron durante el desarrollo**, por lo que no se presentan como una prueba final intocada. Más adelante hay seis preguntas adicionales registradas antes de su ejecución, después de congelar esta configuración.

Recall cuenta secciones relevantes recuperadas, no respuestas correctas. Una sección repetida en dos fragmentos solo cuenta una vez. “Evidencia completa” exige recuperar todas las secciones anotadas de la pregunta.''')
code('''display(Markdown('```python\\n'+inspect.getsource(Index.search)+'\\n```'))
detail, summary, config = run_retrieval()
display(summary.drop(columns='seconds'))
print('Selección usando validación:', config)
display(Image(filename=str(ROOT/'results/figures/03_recuperacion.png')))''')
code('''selected = detail[(detail.method==config['method']) & (detail['size']==config['size']) & (detail.k==config['k'])]
display(selected.groupby('split')[['recall','mrr','complete']].mean())
display(selected[selected.complete==0][['id','split','recall','retrieved']])
display(Markdown("**Interpretación.** La mejora por caracteres tiene sentido en un corpus breve con variaciones de género, número y conjugación. No demuestra comprensión semántica. Los fallos multifuente y las paráfrasis que no comparten forma escrita siguen siendo pruebas importantes; los resultados anteriores permiten comprobarlos en lugar de suponer que un método más complejo siempre gana."))''')
md('''## 6. LangChain y las cuatro estrategias

Se mantiene el modelo Qwen2.5 de 3B y el mismo conjunto de doce tareas para comparar:

1. **Solo modelo:** sin acceso a las fuentes; debería reconocer que no conoce los datos ficticios.
2. **RAG fijo:** recupera reglamentos y los pasa a una cadena `prompt | llm | parser`. No recibe inventario ni motor de fechas: es una ablación deliberada de esas capacidades.
3. **Agente autónomo:** `create_agent` permite al modelo elegir y encadenar herramientas descubiertas por el adaptador.
4. **Flujo guiado:** reglas explícitas detectan catálogo, fechas y preguntas de normas; ejecutan herramientas y un LLM redacta la respuesta. No se presenta como selección autónoma del modelo.

Las arquitecturas necesitan prompts diferentes, por lo que se comparan sistemas completos, no un efecto causal aislado. El historial de la interfaz es visible, pero el flujo guiado exige perfil y fecha en el turno actual; no resuelve automáticamente referencias como “¿y para mí?”.''')
code('''from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from bibliolab.assistant import BASE_URL, guided_plan
client = make_client()
tools = await client.get_tools()
llm = ChatOllama(model='qwen2.5:3b', base_url=BASE_URL, temperature=0, seed=42, num_ctx=4096)
agent = create_agent(model=llm, tools=tools, system_prompt=SYSTEM)
print('Herramientas del agente:', [t.name for t in tools])
display(Markdown('```python\\n'+inspect.getsource(guided_plan)+'\\n```'))''')
md('''### Métricas y límites

Se conservan pregunta, respuesta cruda, argumentos de herramientas, salidas, citas y latencia. Las herramientas esperadas miden cobertura de capacidades, no exactitud final. Los chequeos por expresiones regulares buscan datos mínimos: pueden aprobar una respuesta incompleta o equivocada. Una cita válida significa que el ID estuvo en la evidencia; **no demuestra que la frase esté respaldada**. El panel de fuentes se agrega por la aplicación y se distingue de las citas producidas por el LLM.

Las doce preguntas son un benchmark de desarrollo, con normas, catálogo, fechas, composición de herramientas y falta de información. Algunas coinciden con las pruebas iniciales de integración. No son test ciego. La carga del modelo se realiza antes del cronómetro; la latencia incluye invocaciones y arranque de procesos de herramientas. No es un estudio de rendimiento con repeticiones.''')
code('''outputs, metrics, generation_summary = await run_generation()
display(generation_summary)
display(Image(filename=str(ROOT/'results/figures/04_generacion.png')))
for result in outputs:
    display(Markdown(f"**{result['id']} · {result['mode']}** — {result['question']}\\n\\n{result['raw_answer']}"))''')
md('''## 7. Capacidad del generador: 3B frente a 1,5B

En la exploración inicial, 3B omitió citas y se abstuvo aun cuando recibió la respuesta. Presentar evidencia como texto legible en el flujo guiado es una intervención adicional; se conservan las salidas previas en `results/development_char`. El agente autónomo recibe los resultados estructurados. Por tanto, la comparación de estrategias abarca también la presentación del contexto.

Se intentó cargar 7B, pero excedió el tiempo de espera de 120 segundos en este equipo. Ese fallo se conserva en `results/model7b_load_failure.json`; no se atribuyen métricas de calidad a un modelo que no llegó a responder. Para mantener la reproducción local se comparan **1,5B y 3B** con el mismo flujo guiado, evidencia textual, prompt y parámetros de inferencia. Es una comparación de capacidad dentro de la familia Qwen2.5, sin entrenamiento ni ajuste de pesos.

La hipótesis es que el modelo menor reduzca consumo, a costa de posibles errores adicionales. Tener todas las herramientas correctas no basta si el generador ignora sus resultados.''')
code('''small_outputs, small_metrics, small_summary = await run_generation(modes=('guiado',), model='qwen2.5:1.5b', prefix='small_')
comparison = pd.concat([metrics[metrics['mode']=='guiado'], small_metrics])
display(comparison.groupby('model')[['expected_citation_recall','content_checks_pass','seconds']].mean())
for result in small_outputs:
    display(Markdown(f"**{result['id']} · 1,5B guiado** — {result['question']}\\n\\n{result['raw_answer']}"))''')
md('''## 8. Controles adicionales y revisión crítica

Las siguientes consultas comprueban datos ausentes, perfil faltante, fecha de retiro cerrada, cobertura del calendario y una instrucción para fingir una reserva. Los errores de entrada deben producir aclaraciones o límites, no resultados inventados. La resistencia a una instrucción adversarial aislada no constituye una evaluación completa de seguridad.''')
code('''followups = await run_followups()
for result in followups:
    display(Markdown('**'+result['question']+'**\\n\\n'+result['answer']))''')
md('''### Seis preguntas adicionales después de congelar la propuesta

`data/holdout.json` se escribió antes de ejecutar estas consultas y no se usa para cambiar el recuperador, los prompts ni las reglas. Comparten corpus y autor con las anteriores; no sustituyen una evaluación externa. Se muestran tanto recuperación como generación para distinguir sus fallos.''')
code('''holdout = await run_holdout()
display(holdout)
display(holdout[['recall','mrr','complete']].mean())
for _, row in holdout.iterrows():
    display(Markdown(f"**{row['id']}**\\n\\n{row.raw_answer}"))''')
md((ROOT/'results/qualitative_review.md').read_text(encoding='utf-8'))
md('''## 9. Verificación y conclusiones

Las pruebas verifican conservación de inventario, integridad del corpus, cobertura del fragmentado, calendario con cierres, rechazo de entradas inválidas, métricas multifuente y llamadas reales al servicio. Estos controles no prueban que toda respuesta de un modelo sea correcta.''')
code('''check = subprocess.run([sys.executable,'-m','pytest','-q'], capture_output=True, text=True, check=True)
print(check.stdout)
write_json(ROOT/'results/environment.json', {'python':platform.python_version(),'platform':platform.platform(),'model':model_info,'tests':check.stdout})
display(Markdown(f"""**Conclusiones apoyadas en esta ejecución:**

- La configuración documental elegida fue `{config}`. Se seleccionó con validación; las tablas anteriores muestran hasta dónde recupera evidencia fuera de esa selección.
- En 3B, el agente llamó todas las herramientas anotadas en {metrics[metrics['mode']=='agente'].all_expected_tools.mean():.0%} de las tareas; el flujo guiado lo hizo en {metrics[metrics['mode']=='guiado'].all_expected_tools.mean():.0%}. Este indicador no evalúa por sí solo la respuesta.
- Con 1,5B guiado, la cobertura media de citas esperadas fue {small_metrics.expected_citation_recall.mean():.0%}; los chequeos parciales de contenido pasaron en {small_metrics.content_checks_pass.mean():.0%}. Son señales auxiliares, no porcentajes de exactitud factual.
- Los cálculos e inventarios se pueden verificar fuera del LLM. Ese es el aporte principal de las herramientas frente a consultar únicamente texto.
- Una biblioteca ficticia y pequeña favorece control experimental, pero limita la generalización. Harían falta consultas de usuarios, anotadores independientes, fuentes extensas y medición repetida de latencia antes de usarlo en una institución.

**Siguiente mejora:** recuperación semántica para paráfrasis, evaluación humana de fidelidad por afirmación y resolución controlada del historial. El sistema actual ya permite inspeccionar dónde ocurrió un fallo sin ocultar las respuestas originales."""))''')
md('''## 10. Interfaz Gradio

La celda siguiente inicia la interfaz y puede ejecutarse en un kernel nuevo después de preparar el entorno. Prueba consultas sobre la disponibilidad de *Procesamiento de lenguaje natural* o el vencimiento para un estudiante con retiro el 2026-10-09. El panel de evidencia permite contrastar las respuestas con el catálogo, las reglas y el calendario.''')
code('''# BiblioLab · Grupo X-Ray — iniciar la interfaz Gradio
from bibliolab.runtime import ensure_ollama
from app import build_demo
ensure_ollama()
if 'demo' in globals():
    demo.close()
demo = build_demo()
demo.queue().launch(server_name='127.0.0.1', server_port=7862,
                    share=False, inline=False, prevent_thread_lock=True)''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (BiblioLab)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
nbf.write(nb,ROOT/'BiblioLab_LangChain.ipynb')
print('Notebook creado:',len(cells),'celdas;',sum(c.cell_type=='code' for c in cells),'de código')
