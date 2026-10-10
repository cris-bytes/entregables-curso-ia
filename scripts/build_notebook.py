"""Construye el notebook fuente; las salidas las añade execute_notebook.py."""
from pathlib import Path
from textwrap import dedent
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
cells=[]
def md(s): cells.append(nbf.v4.new_markdown_cell(dedent(s).strip()))
def code(s): cells.append(nbf.v4.new_code_cell(dedent(s).strip()))

md('''
# FinGuía · Un asesor educativo de inversión con RAG
### Evidencia documental, evaluación crítica y simulación de aportes

**Caso propio:** una persona que comienza a invertir necesita comprender riesgo, diversificación, costes e inflación. Una respuesta fluida sin respaldo puede confundir una simulación con una promesa o una comisión antigua con una vigente.

**Propuesta:** un chatbot en español que recupera documentos, genera una explicación local con referencias y permite verificar el fragmento original. Un simulador separado calcula escenarios de aportes con fórmulas auditables.

**Entregables:** notebook ejecutado, corpus versionado, benchmark, métricas CSV/JSON, gráficos, código reutilizable, aplicación Gradio y guion de video. El video lo graba el estudiante y dura menos de dos minutos.

**Autoría y alcance:** desarrollo elaborado con asistencia de IA para este proyecto. Las síntesis educativas se atribuyen a fuentes oficiales; las carteras Horizonte son ficticias. No se dispone todavía de los notebooks guía del curso, por lo que no se afirma haberlos reproducido ni comparado línea por línea. Este notebook desarrolla un caso original y debe contrastarse con esas guías cuando estén disponibles.
''')
md('''
## 1. Problema, usuarios y criterio de éxito

El problema no consiste en adivinar qué activo subirá. Consiste en **responder preguntas educativas con información verificable** y separar lo conocido de lo que los documentos no contienen. El corpus mezcla conceptos generales con fichas propias que el LLM no debería conocer de memoria: así se comprueba si realmente usa la evidencia.

Un buscador léxico puede fallar cuando el usuario dice «volver a los pesos objetivo» y el documento habla de «rebalanceo». Un LLM sin documentos puede inventar porcentajes. RAG combina recuperación con generación, pero cada etapa puede fallar y debe evaluarse por separado.

**Preguntas de investigación:**
1. ¿E5 mejora la recuperación frente a TF-IDF y BM25 en paráfrasis financieras?
2. ¿Combinar BM25 y E5 mediante RRF mejora siempre o puede empatar?
3. ¿Cómo cambian los resultados al variar tamaño de fragmento y cantidad recuperada?
4. ¿Un umbral de similitud distingue preguntas respondibles de preguntas sin evidencia?
5. ¿Qué cambia al generar con Qwen 0.5B y 1.5B, manteniendo la recuperación?
6. ¿Excluir versiones históricas evita contaminación del contexto?

Criterios de evaluación: Recall por sección, MRR, nDCG, recuperación de **toda** la evidencia necesaria, abstenciones y revisión de respuestas. Tener una cita válida no prueba que la afirmación sea correcta. El sistema no ejecuta compras ni presenta asesoría personalizada; carece de cotizaciones en vivo y de datos fiscales individuales.
''')
md('''
## 2. Reproducción desde cero

Usar Python 3.12 y ejecutar desde la carpeta del proyecto. Antes de abrir el notebook:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_models.py
python -m jupyterlab FinGuia_RAG_Inversion.ipynb
```

La primera preparación descarga modelos públicos; no requiere claves ni servicios pagados. Los tres modelos ocupan varios GB. Los embeddings se ejecutan en CPU, con cuatro hilos. El generador usa float16 y el acelerador MPS de Apple si está disponible; en caso contrario usa CPU. Se puede fijar `FINGUIA_DEVICE=cpu`. Se usa semilla fija y decodificación greedy. El generador de 1.5B requiere más memoria que el de 0.5B; se recomienda disponer de 16 GB de RAM, aunque la demo se verifica en un Mac de 8 GB. Después de descargar modelos y dependencias, el análisis y la aplicación funcionan localmente.

`requirements.txt` fija dependencias directas y `requirements-lock-macos-py312.txt` registra el entorno completo probado en este Mac. Las revisiones exactas de los modelos están en `models.lock.json`. Los tiempos dependen del equipo; pequeñas diferencias numéricas entre plataformas no deben interpretarse como cambios de calidad.
''')
code('''
import os, sys, json, random, platform, inspect
from pathlib import Path
import numpy as np
import pandas as pd
from IPython.display import display, Markdown

ROOT = Path.cwd()
if not (ROOT / 'data/manifest.json').exists():
    raise RuntimeError('Abre este notebook desde la carpeta del proyecto.')
os.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
random.seed(42)
np.random.seed(42)
from finguia.core import (load_sections, make_chunks, Retriever, Assistant, read_json,
    get_generator, generate, citations_in, ROOT)
from finguia.evaluation import run_retrieval, run_generation, record_environment
from finguia.analysis import corpus_eda, retrieval_plots, abstention_plot
from finguia.simulator import simulate
import matplotlib.pyplot as plt
import torch
torch.manual_seed(42)
torch.set_num_threads(4)
(ROOT/'results').mkdir(exist_ok=True)
print('Python:', platform.python_version(), '| embeddings CPU | generador:', 'MPS' if torch.backends.mps.is_available() else 'CPU', '| float16 | semilla 42')
''')
code('''
# Solo descarga si falta una revisión fijada. No cambia modelos silenciosamente.
from huggingface_hub import snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError
import subprocess
models = read_json(ROOT/'models.lock.json')
missing = []
for name, spec in models.items():
    try:
        snapshot_download(spec['repo'], revision=spec['revision'], local_files_only=True,
                          cache_dir=str(ROOT/'.cache/huggingface/hub'))
    except LocalEntryNotFoundError:
        missing.append(name)
if missing:
    subprocess.run([sys.executable, 'scripts/download_models.py'], check=True)
display(pd.DataFrame(models).T)
''')
md('''
## 3. Documentos y anotación de preguntas

Se usan siete documentos educativos que sintetizan, en español, páginas de SEC/Investor.gov y FINRA. No se presentan como traducciones oficiales ni como normas colombianas. Otros tres documentos describen dos carteras ficticias, una versión histórica y las convenciones del simulador. Las fechas de consulta externa y las versiones del laboratorio se distinguen en el manifiesto.

Cada sección tiene un identificador estable (`D08-S1`) que permite evaluar independientemente del tamaño de los fragmentos. Cada archivo tiene un SHA-256 para detectar cambios. El documento histórico permanece disponible para el experimento de vigencia, pero se excluye del índice normal.

Las **36 preguntas** se escribieron antes de ejecutar la búsqueda: 12 de validación (8 respondibles y 4 sin respuesta) y 24 de test (18 respondibles y 6 sin respuesta). Las etiquetas incluyen las secciones necesarias; algunas preguntas requieren dos. Las «anclas» textuales detectan presencia de ciertos contenidos, pero no equivalen a una evaluación semántica ni a una revisión humana independiente.

La configuración de recuperación y el umbral se seleccionan únicamente con validación. El análisis comparativo de generadores es exploratorio: los errores iniciales motivaron probar un modelo mayor, por lo que ese subconjunto no debe anunciarse como prueba ciega de selección del LLM.
''')
code('''
manifest = pd.DataFrame(read_json(ROOT/'data/manifest.json'))
questions = pd.DataFrame(read_json(ROOT/'data/questions.json'))
questions['answerable'] = questions.gold_sections.map(bool)
display(manifest[['doc_id','title','source','current','provenance']])
display(pd.crosstab(questions['split'], questions.answerable).rename(columns={False:'Sin respuesta',True:'Con respuesta'}))
display(questions[['id','split','kind','question','gold_sections']].head(8))
''')
md('''
## 4. EDA: primero entender el corpus

El objeto del EDA es el **corpus documental**, no una serie bursátil. Inventar precios para presentar un backtest como real no resolvería el problema planteado. Se revisan cobertura temática, longitud, duplicados, valores ausentes, vocabulario y similitud entre documentos.

Los enlaces ausentes en documentos del laboratorio son intencionales: se trata de datos propios. Una sección vacía, un identificador repetido o un hash diferente sí sería un problema. La similitud entre D08 y D09 merece especial atención porque sus cifras entran en conflicto.
''')
code('''
sections, corpus_fig, similarity_fig = corpus_eda()
quality = pd.Series({
    'documentos': sections.doc_id.nunique(),
    'secciones': len(sections),
    'secciones vigentes': int(sections.current.sum()),
    'textos vacíos': int(sections.text.str.strip().eq('').sum()),
    'textos duplicados exactos': int(sections.duplicate_text.sum()),
    'IDs de sección repetidos': int(sections.section_id.duplicated().sum()),
    'palabras totales': int(sections.words.sum()),
    'mediana de palabras por sección': float(sections.words.median()),
})
display(quality.to_frame('valor'))
display(sections.groupby(['topic','current']).agg(secciones=('section_id','count'),palabras=('words','sum')))
display(corpus_fig)
display(similarity_fig)
plt.close('all')
''')
code('''
display(Markdown(f"""
**Lectura del EDA.** El corpus contiene {int(quality['documentos'])} documentos y {int(quality['secciones'])} secciones,
con una mediana de {quality['mediana de palabras por sección']:.0f} palabras por sección.
Es un corpus corto y curado: una configuración de 128 palabras tiende a conservar secciones completas,
mientras que 32 palabras puede separar un hecho de su excepción.
Hay {int(quality['textos duplicados exactos'])} duplicados exactos; eso no elimina el problema de versiones parecidas con valores distintos.
Los tópicos comparten vocabulario financiero, de modo que las preguntas fuera de cobertura pero dentro del dominio son especialmente difíciles.
Estos datos permiten un laboratorio controlado; no demuestran desempeño en miles de documentos ni en consultas reales de clientes.
"""))
''')
md('''
## 5. Indexación y arquitectura RAG

```text
Pregunta → límites de alcance → recuperación de fragmentos vigentes
         → umbral calibrado → contexto con IDs → Qwen local
         → comprobación de IDs citados → respuesta + documentos

Simulador → fórmulas Python → gráfico y cifras (sin intervención del LLM)
```

No se entrenan los pesos de E5 ni de Qwen. Se construye un índice y se ajustan hiperparámetros de recuperación. TF-IDF aprende vocabulario e IDF del corpus; BM25 usa estadísticas de términos; E5 codifica preguntas y fragmentos en vectores normalizados. No se debe llamar «entrenamiento del chatbot» a una descarga de modelos o a la construcción del índice.

**Tratamiento del texto:** se mantienen acentos y puntuación para embeddings y generación; solo la rama léxica normaliza acentos y elimina palabras funcionales. La partición usa ventanas de palabras con solapamiento de 12, sin cruzar límites de sección. El tamaño se expresa en palabras, no en tokens del modelo. E5 usa los prefijos `query:` y `passage:` recomendados por su ficha incluso en español.
''')
code('''
chunk_counts = []
for size in [32,64,128]:
    chunks = make_chunks(load_sections(), size=size, overlap=12)
    chunk_counts.append({'palabras máximas':size, 'solapamiento':12, 'fragmentos':len(chunks)})
display(pd.DataFrame(chunk_counts))
example = make_chunks([s for s in load_sections() if s['section_id']=='D08-S1'],size=32,overlap=12)
display(pd.DataFrame([{'id':c.chunk_id,'inicio':c.start_word,'fin':c.end_word,'texto':c.text} for c in example]))
''')
md('''
## 6. Comparación de recuperadores

Se comparan **TF-IDF**, **BM25**, **E5 denso** e **híbrido BM25 + E5**. RRF combina posiciones mediante `sum(1 / (60 + rango))`; no suma directamente un coseno y una puntuación BM25, que tienen escalas diferentes.

La cuadrícula tiene 36 configuraciones: 4 métodos × 3 tamaños (32, 64, 128 palabras) × 3 valores de k (1, 3, 5). La elección maximiza Recall de validación y luego MRR. En empate se prefiere menor k y sección más completa; el orden alfabético del método resuelve el último empate de forma reproducible. No se impone que «híbrido» gane.

- **Recall@k:** proporción de secciones necesarias presentes en los k fragmentos.
- **MRR@k:** inverso del rango de la primera sección relevante.
- **nDCG@k:** recompensa evidencia relevante en posiciones altas, sin contar dos veces una sección.
- **Toda la evidencia:** vale 1 solo si aparecen todas las secciones requeridas.

Una coincidencia parcial con una sección cuenta en recuperación. Por ello un fragmento incompleto puede puntuar bien aunque no contenga la cifra buscada. La generación necesita una evaluación adicional. El tiempo de búsqueda registrado excluye la codificación de la pregunta, porque se precalcula; no es la latencia total del chatbot.
''')
code('''
# La implementación del ranking se muestra para que la decisión sea auditable.
display(Markdown('```python\\n' + inspect.getsource(Retriever.scores) + '\\n```'))
''')
code('''
# Ejecuta de nuevo las 36 configuraciones y selecciona sin usar test.
detail, summary, config = run_retrieval()
display(summary[(summary.split=='val') & (summary['size']==config['size'])].sort_values(['recall','mrr'],ascending=False))
print('Configuración elegida:', config)
display(retrieval_plots(summary, config))
plt.close('all')
''')
code('''
report = read_json(ROOT/'results/retrieval_report.json')
selected_test = detail[(detail.split=='test') & (detail['size']==config['size']) & (detail.method==config['method']) & (detail.k==config['k'])]
display(selected_test.groupby('kind')[['recall','mrr','all_evidence']].mean())
failures = selected_test[selected_test.all_evidence < 1].merge(questions[['id','question','gold_sections']],on='id')
display(failures[['id','question','gold_sections','sections','recall']])
low, high = report['test_recall_bootstrap95']
display(Markdown(f"""
**Resultado de recuperación.** La configuración seleccionada es **{config['method']}**, {config['size']} palabras y k={config['k']}.
En {report['test_answerable_n']} preguntas respondibles de test, el Recall medio es **{report['test_recall']:.1%}**,
y la recuperación de toda la evidencia es **{report['test_all_evidence']:.1%}**. El intervalo bootstrap descriptivo del Recall
es [{low:.1%}, {high:.1%}], con 2000 remuestreos y semilla 42.
El conjunto es pequeño y sus preguntas proceden del mismo diseño documental; el intervalo no corrige ese sesgo.
MRR y Recall responden preguntas distintas: encontrar rápidamente una fuente pertinente no garantiza recuperar la segunda fuente de una consulta compuesta.
"""))
''')
md('''
**Interpretación del caso.** En esta ejecución, E5 e híbrido empatan en Recall de test; E5 obtiene mejor MRR. El híbrido no aporta una mejora automática. BM25 y TF-IDF siguen siendo baselines importantes, porque una ficha con un nombre o porcentaje exacto puede recuperarse bien sin un encoder neuronal.

Los fragmentos de 128 palabras preservan mejor las secciones breves de este corpus. No es una regla para libros extensos o PDFs con tablas. Aumentar k permite recuperar más fuentes, pero también añade distractores y puede confundir al generador. El caso multifuente que no recuperó toda la evidencia se mantiene visible en la tabla anterior.
''')
md('''
## 7. Abstención y documentos antiguos

La similitud E5 no es una probabilidad de corrección. Se calibra un umbral usando solo las 12 preguntas de validación, maximizando balanced accuracy; en empate se reducen falsas aceptaciones. Se evalúan dos capas por separado: umbral y umbral más reglas de alcance para cotizaciones actuales, predicciones exactas, credenciales y cálculo fiscal personal.

Estas reglas responden al alcance del producto y se encuentran explícitas en el código. No son un modelo aprendido de incertidumbre. Un rechazo correcto evita inventar; uno incorrecto impide responder algo que sí estaba documentado. Es necesario contar ambos.
''')
code('''
confidence = pd.read_csv(ROOT/'results/abstention.csv')
display(pd.read_csv(ROOT/'results/threshold_calibration.csv').head())
display(abstention_plot(confidence, config['threshold']))
plt.close('all')
from sklearn.metrics import confusion_matrix
for column in ['accepted_threshold','accepted_with_scope']:
    subset=confidence[confidence.split=='test']
    matrix=confusion_matrix(subset.answerable,subset[column],labels=[False,True])
    print(column)
    display(pd.DataFrame(matrix,index=['Real: sin respuesta','Real: respondible'],columns=['Rechaza','Acepta']))
errors=confidence[(confidence.split=='test') & (confidence.accepted_with_scope != confidence.answerable)]
display(errors.merge(questions[['id','question']],on='id')[['id','question','answerable','confidence','accepted_with_scope']])
''')
md('''
**Hallazgo:** una pregunta sobre la comisión de retiro de Horizonte A puede tener similitud alta con una ficha que solo especifica la comisión anual. La búsqueda acierta el tema, pero la respuesta solicitada falta. Este es un ejemplo concreto de por qué el umbral no basta: hay que revisar qué afirma realmente el texto y permitir que el generador se abstenga. Elevar el umbral hasta ocultar ese caso después de ver test contaminaría la evaluación; no se hace aquí.
''')
code('''
versions = pd.read_csv(ROOT/'results/version_ablation.csv')
display(versions)
display(Markdown(f"""
**Vigencia documental.** Sin filtro se recuperaron {int(versions[versions['index']=='sin_filtro'].obsolete_retrieved.sum())}
fragmentos históricos entre las consultas evaluadas. El filtro elimina ese contexto obsoleto por construcción.
En la consulta de validación sobre la comisión, la ficha antigua puede adelantarse a la vigente.
Esta ablación mide contaminación de recuperación; no demuestra por sí sola que el LLM haya respondido con el valor antiguo.
El filtro usa metadatos curados; si esos metadatos están mal, la protección puede fallar.
"""))
''')
md('''
## 8. Generación real: dos tamaños de Qwen y un baseline extractivo

Se utilizan modelos locales Qwen2.5-Instruct de 0.5B y 1.5B con el mismo prompt, documentos y decodificación greedy. La arquitectura de familia se mantiene; cambia la capacidad. Se comparan con una salida extractiva que muestra los fragmentos tal cual: **ese baseline no se presenta como un LLM**.

El prompt limita la respuesta a las fuentes, solicita citas y habilita abstención. Incluye dos demostraciones artificiales de formato (few-shot): una respuesta citada y una abstención ante un atributo ausente. Ninguna usa cifras de las carteras evaluadas. Un validador verifica que los IDs citados existan en el contexto. Cuando faltan citas o son inválidas, la interfaz anuncia expresamente la sustitución por fragmentos. No se ocultan las salidas originales: quedan en `raw_generation`.

**Límite del validador:** una cita válida puede respaldar una afirmación incorrecta o una cifra intercambiada. Para analizarlo se conservan la generación cruda, las anclas y las evidencias. Las anclas tampoco detectan de forma fiable una negación incorrecta o el intercambio entre dos carteras.
''')
code('''
# Muestra el prompt y la llamada neuronal exactos.
display(Markdown('```python\\n' + inspect.getsource(generate) + '\\n```'))
''')
code('''
# Puede tardar varios minutos en CPU; no sustituye la ejecución por resultados inventados.
small_outputs = run_generation(model_key='generator_small', prefix='small_')
large_outputs = run_generation(model_key='generator')
''')
code('''
comparisons=[]
for label,prefix in [('Qwen 0.5B','small_'),('Qwen 1.5B','')]:
    metrics=pd.read_csv(ROOT/f'results/{prefix}generation_metrics.csv')
    for mode,part in metrics.groupby('mode'):
        answerable=part[~part.expected_abstention]
        absent=part[part.expected_abstention]
        comparisons.append({'modelo':label,'modo':mode,
            'respondibles':len(answerable),'cobertura de anclas (salida final)':answerable.anchor_coverage.mean(),
            'rechazos indebidos':int(answerable.abstained.sum()),
            'sustituciones por fragmentos':int(answerable.fallback.sum()),
            'citas válidas en generación cruda':int(answerable.citation_ids_valid.sum()),
            'recall de fuentes citadas (crudo)':answerable.cited_gold_recall.mean(),
            'rechazos correctos sin evidencia':int(absent.abstained.sum()),
            'preguntas sin evidencia':len(absent),'mediana segundos':part.seconds.median()})
comparison=pd.DataFrame(comparisons)
comparison.to_csv(ROOT/'results/model_comparison.csv',index=False)
display(comparison)
# Se muestra exactamente lo generado, no solo el texto final tras el fallback.
for qid in ['Q16','Q26','Q28','Q36']:
    print('\\n' + '='*75)
    for label,outputs in [('0.5B',small_outputs),('1.5B',large_outputs)]:
        result=next(o for o in outputs if o['id']==qid and o['mode']=='generative')
        print(label, result['question'])
        print('GENERACIÓN CRUDA:',result['raw_generation'])
        print('Abstención:',result['abstained'],'| Sustitución:',result['fallback'])
''')
md('''
**Lectura crítica de la generación.** La primera ejecución de 0.5B omitió referencias y llegó a intercambiar los porcentajes de Horizonte A y B. Esto motivó ensayar 1.5B. El prompt inicial también produjo errores con 1.5B: omitió citas y llegó a interpretar una comisión de retiro no documentada como inexistente. Se añadió few-shot y se aclaró que un dato ausente no equivale a cero. Las ejecuciones iniciales se conservan en los archivos `initial_*`, pero no se comparan como si solo hubiera cambiado la arquitectura: también cambió el prompt y la precisión numérica. La tabla anterior vuelve a ejecutar ambos tamaños bajo el mismo prompt final y float16.

No se anuncia la cobertura de anclas del fallback como precisión del LLM: copiar todo el contexto facilita encontrar las anclas, aunque también añade información irrelevante. Tampoco se anuncia un porcentaje de «fidelidad» basado solo en IDs válidos. Las latencias incluyen la primera carga del generador y cachés de preguntas ya calculadas; no son un benchmark de concurrencia.

**Errores que permanecen con el prompt final:** en Q36, 1.5B puede responder con la comisión anual aunque se preguntó por la comisión de retiro, que no está documentada. La cita existe, pero la respuesta no resuelve la pregunta. En Q28 puede describir correctamente ambas carteras y citar solo la ficha de B. El recall de fuentes citadas muestra esa referencia incompleta. El panel de la aplicación conserva todo el contexto recuperado para facilitar la revisión, sin presentar eso como una reparación de la generación.

Esta comparación usa nueve preguntas de test seleccionadas por tipo, no todo test ni una muestra representativa de usuarios. La decisión de probar un modelo mayor y ajustar el prompt fue posterior a observar errores, por lo que sus resultados son exploratorios. Una evaluación final externa debería incorporar nuevas preguntas anotadas por otra persona, revisión de cada afirmación y más ejemplos de abstención financiera difícil.
''')
md('''
### Comprobación adicional después de fijar el prompt

Se escribieron ocho preguntas adicionales antes de observar sus respuestas con el prompt final. No se utilizan para cambiar el ranking, el umbral ni el prompt. Esta comprobación reduce la dependencia de las preguntas usadas durante el desarrollo, pero sigue siendo pequeña, del mismo corpus y sin anotador externo. Se muestran las respuestas completas, incluidos los fallos.
''')
code('''
from finguia.evaluation import run_final_checks
final_checks=run_final_checks()
display(pd.DataFrame([{'id':o['id'],'pregunta':o['question'],'abstención':o['abstained'],
    'citas válidas':o['citation_ids_valid'],'fallback':o['fallback'],'respuesta':o['answer']} for o in final_checks]))
''')
md('''
**Hallazgos de las ocho preguntas adicionales.** Cuatro de las seis consultas respondibles produjeron respuestas directas con la fuente correspondiente. H01 y H06 activaron la sustitución por fragmentos al omitir las citas: H06 tenía el contenido correcto, mientras H01 explicó ventas y compras aunque se preguntó por nuevas aportaciones.

Las dos preguntas sin respuesta no produjeron una abstención correcta. H07 confundió un saldo mínimo, inexistente en los documentos, con los porcentajes de composición de Horizonte B; además adjuntó un ID válido. H08 no identificó al gestor solicitado y terminó mostrando evidencia extractiva. El hecho de que no inventara un nombre no equivale a resolver bien la consulta.

Este resultado es más exigente que la prueba exploratoria y demuestra que la abstención sigue siendo insuficiente. No se modificaron el prompt ni el umbral después de observar estas ocho respuestas. El prototipo sirve para estudiar educación financiera con evidencia y fallos visibles; no está validado para recomendar inversiones reales. Una siguiente versión necesitaría verificar la correspondencia entre el atributo preguntado y la afirmación, además de la existencia de la cita.
''')
md('''
## 9. Innovación útil: separar lenguaje y cálculo

Un asesor educativo también debe mostrar cuánto cambian los escenarios al variar aportes, costes y pérdida de poder adquisitivo. Se añade un simulador determinista, conectado a la interfaz, que evita delegar aritmética al LLM.

Para un rendimiento anual efectivo bruto `r` y una comisión anual `c`, el factor mensual del laboratorio es:

`f = ((1 + r) × (1 - c)) ** (1/12)`

`saldo_mes = saldo_anterior × f + aporte_mensual`

`saldo_real = saldo_nominal / (1 + inflación) ** (mes / 12)`

Los aportes se realizan al final del mes. La comisión se modela multiplicativamente; es una convención simplificada y no la forma contractual de cobro de todos los fondos. El resultado real se expresa en poder adquisitivo inicial. Las tasas son supuestas y constantes; no hay volatilidad, impuestos, riesgo de divisa ni predicción del mercado.
''')
code('''
# Casos conocidos verifican la fórmula antes de interpretar curvas.
zero = simulate(1000,100,1,0,0,0).iloc[-1]
compound = simulate(1000,0,2,5,0,0).iloc[-1]
assert zero.nominal == zero.real == 2200
assert np.isclose(compound.nominal,1102.5)
print('Tasa cero:',zero.nominal,'| Capitalización 5 % por dos años:',round(compound.nominal,2))

rows=[]
fig,ax=plt.subplots(figsize=(10,4.5))
for fee in [0,.3,1.2,2]:
    frame=simulate(1000000,100000,20,6,fee,3)
    last=frame.iloc[-1]
    rows.append({'comisión anual (%)':fee,'aportado nominal':last.contributed,
                 'saldo nominal':last.nominal,'saldo real':last.real,
                 'diferencia frente a cero comisión':last.without_fees-last.nominal})
    ax.plot(frame.year,frame.nominal,label=f'Comisión {fee:.1f} %')
ax.set(title='Sensibilidad al coste: mismo aporte y rendimiento bruto supuesto',xlabel='Años',ylabel='Unidades monetarias nominales')
ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
fig.savefig(ROOT/'results/figures/08_fee_sensitivity.png')
display(fig); plt.close(fig)
sensitivity=pd.DataFrame(rows)
sensitivity.to_csv(ROOT/'results/fee_sensitivity.csv',index=False)
display(sensitivity.round(2))
''')
code('''
low_fee=sensitivity[sensitivity['comisión anual (%)']==.3].iloc[0]
high_fee=sensitivity[sensitivity['comisión anual (%)']==1.2].iloc[0]
display(Markdown(f"""
**Interpretación del escenario.** Al cambiar únicamente la comisión de 0,30 % a 1,20 %, la diferencia de saldo nominal
al año 20 es de **{low_fee['saldo nominal']-high_fee['saldo nominal']:,.0f} unidades monetarias**.
No es una comparación del rendimiento esperado de Horizonte A frente a B: esas carteras también difieren en composición.
Aquí se mantiene una tasa bruta hipotética del 6 % para aislar el efecto matemático del coste.
La curva en dinero de hoy descuenta una inflación hipotética del 3 %; ninguna de las tasas se presenta como previsión.
Un escenario negativo también debe ser posible: la aplicación admite rendimientos anuales negativos.
"""))
''')
md('''
## 10. Verificación y conclusiones

Se comprueban integridad del corpus, cobertura del chunking, métricas sin doble conteo, detección de abstenciones y casos matemáticos conocidos. La prueba de la aplicación abre Gradio en un navegador, realiza una consulta, comprueba la referencia y el archivo asociado, y revisa simulador, biblioteca y disposición móvil. El notebook guarda sus salidas reales para poder revisar los resultados sin volver a descargar modelos.
''')
code('''
check=subprocess.run([sys.executable,'-m','pytest','-q'],capture_output=True,text=True,check=True)
print(check.stdout)
environment=record_environment()
display(pd.Series(environment['packages'],name='Versión probada').to_frame())
if (ROOT/'results/app_smoke.json').exists():
    display(pd.Series(read_json(ROOT/'results/app_smoke.json'),name='Prueba de interfaz guardada').to_frame())
''')
md('''
**Conclusiones del caso:**

1. E5 mejora el orden de recuperación respecto a los baselines léxicos en este corpus pequeño. La fusión RRF es una comparación valiosa, pero no supera automáticamente al recuperador denso.
2. La granularidad debe elegirse según los documentos: conservar secciones cortas evita perder excepciones y cifras. Recuperar más fragmentos también introduce distractores.
3. Una pregunta puede tener alta similitud sin disponer de respuesta. La comisión de retiro no documentada muestra esta limitación de forma concreta. El control de alcance y la abstención del generador complementan el umbral, sin garantizar exactitud universal.
4. Mantener metadatos de versión resulta tan importante como cambiar el modelo. El experimento sin filtro recupera una comisión antigua y evidencia el riesgo de mezclar valores.
5. La evaluación del generador debe mirar el texto crudo. Referencias válidas, cobertura de palabras y recuperación correcta no son sinónimos de fidelidad de cada afirmación.
6. El simulador añade una herramienta útil al problema educativo y mantiene los cálculos fuera del LLM. Sus curvas explican supuestos; no recomiendan una cartera ni prometen rentabilidad.

**Limitaciones:** corpus breve de síntesis, preguntas elaboradas por el mismo proceso que los documentos, pocas preguntas negativas, sin evaluación humana externa, contexto de una sola pregunta por turno, sin PDFs largos ni tablas complejas, sin cotizaciones actuales. Los documentos estadounidenses aportan conceptos; no se trasladan reglas fiscales a Colombia. Las decisiones de inversión personal requieren contexto y evaluación profesional.

**Siguiente iteración razonable:** incorporar documentos oficiales más extensos con metadatos de fecha y jurisdicción; crear preguntas independientes antes de nuevos ajustes; evaluar cada afirmación y su cita; explorar reranking con cross-encoder y analizar calidad frente a latencia. No se afirma haber implementado esos pasos futuros.
''')
md('''
## 11. Fuentes y reproducibilidad documental

Las URLs y hashes completos están en `data/manifest.json`. Los documentos locales permiten repetir el experimento aunque una web cambie. Son síntesis propias, no snapshots íntegros de los sitios.

- [SEC: asignación de activos](https://www.investor.gov/introduction-investing/getting-started/asset-allocation).
- [SEC: diversificación y rebalanceo](https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset).
- [SEC: impacto de comisiones](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated).
- [FINRA: bonos y diligencia](https://syndication.finra.org/content/bond-investing-and-due-diligence).
- [SEC: fondos ETF](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24).
- [SEC: señales de fraude](https://www.investor.gov/protect-your-investments/fraud/how-avoid-fraud/red-flags-investment-fraud-checklist).
- [SEC: poder adquisitivo](https://www.investor.gov/introduction-investing/investing-basics/glossary/purchasing-power).
- [Ficha E5 multilingüe](https://huggingface.co/intfloat/multilingual-e5-small) y [reporte técnico](https://arxiv.org/abs/2402.05672).
- [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) y [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct).
- [Cormack et al.: Reciprocal Rank Fusion](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf).
- [Gradio Blocks](https://www.gradio.app/docs/gradio/blocks).
''')
md('''
## 12. Celda para grabar el video (menos de 2 minutos)

Antes de grabar, ejecutar las celdas anteriores para cargar los modelos. Durante la grabación **mostrar y ejecutar la celda siguiente**, abrir la interfaz y realizar dos preguntas. Por ejemplo:

1. «¿Cuál es la comisión anual vigente de Horizonte A?» — verificar 0,30 % y `D08-S1`.
2. «¿Diversificar garantiza que no perderé dinero si cae el mercado?» — verificar la explicación y `D02-S1`.

Mostrar el panel de evidencia y abrir al menos un documento. El guion detallado está en `docs/VIDEO.md`. Una página ya abierta sin ejecutar la celda de Gradio no cumple por sí sola el requisito del video. La aplicación es local: no se publica un enlace externo.
''')
code('''
from app import build_demo
assistant = Assistant(config)
get_generator()  # Precarga; no consume claves ni realiza llamadas a una API de pago.
if 'demo' in globals():
    demo.close()
demo = build_demo(assistant)
demo.queue().launch(
    server_name='127.0.0.1',
    share=False,
    inline=True,
    prevent_thread_lock=True,
    allowed_paths=[str(ROOT/'data/documents')],
)
''')
md('''
**Video:** pendiente de grabación y subida por el estudiante. Añadir el enlace en `docs/ENTREGA.md` o adjuntar el archivo en Intu. **GitHub:** [entregables-curso-ia](https://github.com/cris-bytes/entregables-curso-ia) (privado; compartir acceso con el docente).
''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (ipykernel)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.14'}})
nbf.write(nb,ROOT/'FinGuia_RAG_Inversion.ipynb')
print(f'Notebook fuente: {len(cells)} celdas, {sum(c.cell_type=="code" for c in cells)} de código.')
