"""Interfaz local Gradio: chat con evidencias y simulador de inversión."""
from __future__ import annotations
import html
from pathlib import Path
from urllib.parse import quote

from finguia.core import ROOT, Assistant, get_generator, load_sections, read_json
from finguia.simulator import simulate
import gradio as gr
import matplotlib.pyplot as plt

CSS = """
.gradio-container {max-width:1220px!important; margin:auto!important; background:#f6f7f9;}
.hero {background:#101f35; padding:30px 34px; border-radius:18px; color:#fff; margin-bottom:16px;}
.hero .eyebrow {font-size:12px; letter-spacing:2px; color:#b8e0ba; text-transform:uppercase; font-weight:600;}
.hero h1 {font-size:38px; font-weight:650; margin:7px 0; letter-spacing:-1.5px; color:white;}
.hero p {max-width:720px; color:#d4ddea; font-size:16px; line-height:1.5; margin:0;}
.hero .badge {display:inline-block; margin-top:18px; font-size:12px; padding:5px 12px;
 border:1px solid #42604f; border-radius:30px; color:#c2e8c5;}
.evidence-card {background:white; border:1px solid #dce3e9; border-left:3px solid #2e7460;
 padding:15px; margin:10px 0; border-radius:10px; font-size:13px; line-height:1.6; color:#25354a;}
.evidence-card strong {color:#1b614a;} .evidence-card a {color:#286993;}
.evidence-card .source {font-size:12px; margin-top:10px;} .evidence-empty {padding:24px 10px;color:#68788b;line-height:1.7;}
footer {display:none!important;} #ask-button {background:#286650; color:white;}
.fineprint {font-size:12px;color:#718095;}
"""

def evidence_html(hits):
    if not hits:
        return '<div class="evidence-empty">Las referencias aparecerán aquí después de tu consulta.<br>Podrás leer el fragmento y abrir el documento.</div>'
    cards = []
    seen = set()
    for h in hits:
        if h['chunk_id'] in seen:
            continue
        seen.add(h['chunk_id'])
        local = '/gradio_api/file=' + quote(str(ROOT/h['path']),safe='/')
        source = f'<a href="{local}" target="_blank" rel="noopener">Documento del corpus ↗</a>'
        if h['source_url']:
            source += f' · <a href="{html.escape(h["source_url"],quote=True)}" target="_blank" rel="noopener">Fuente oficial ↗</a>'
        else:
            source += ' · Ficha ficticia del laboratorio'
        card = (f'<div class="evidence-card"><strong>[{h["section_id"]}] {html.escape(h["heading"])}</strong>'
            f'<p>{html.escape(h["text"])}</p><div class="source">{source}</div></div>')
        if not h.get('cited',True):
            card = f'<details><summary>Contexto adicional · {h["section_id"]}</summary>{card}</details>'
        cards.append(card)
    return ''.join(cards)

def simulator_view(initial,monthly,years,annual_return,annual_fee,inflation):
    frame = simulate(initial,monthly,years,annual_return,annual_fee,inflation)
    last = frame.iloc[-1]
    fig,ax = plt.subplots(figsize=(9,4.4))
    fig.patch.set_facecolor('#f6f7f9'); ax.set_facecolor('#f6f7f9')
    ax.plot(frame.year,frame.nominal,color='#267258',linewidth=2.5,label='Saldo nominal')
    ax.plot(frame.year,frame.real,color='#336da3',linewidth=2,label='Saldo en dinero de hoy')
    ax.plot(frame.year,frame.contributed,color='#8290a0',linestyle='--',label='Aportes nominales acumulados')
    ax.set(xlabel='Años',ylabel='Unidades monetarias',title='Escenario hipotético con tasas constantes')
    ax.ticklabel_format(axis='y',style='plain'); ax.grid(alpha=.16); ax.legend(frameon=False,fontsize=9)
    ax.spines[['top','right']].set_visible(False); fig.tight_layout()
    summary = (f"**Saldo nominal: {last.nominal:,.0f}** · Saldo en dinero de hoy: **{last.real:,.0f}**\n\n"
        f"Aportado: {last.contributed:,.0f} · Diferencia frente al escenario sin comisión: "
        f"{last.without_fees-last.nominal:,.0f}\n\n"
        'Aportes al final de cada mes. Todas las cantidades usan la misma moneda. '
        'Se excluyen impuestos, divisas y fluctuaciones del mercado. [Supuestos: D10-S1 y D10-S2.]')
    return summary,fig

def build_demo(assistant=None):
    assistant = assistant or Assistant()
    documents = read_json(ROOT/'data/manifest.json')
    theme = gr.themes.Soft(primary_hue='emerald',neutral_hue='slate',font=['Arial','sans-serif'])
    with gr.Blocks(title='FinGuía · Invertir con contexto',theme=theme,css=CSS) as demo:
        gr.HTML('<div class="hero"><div class="eyebrow">Laboratorio de inversión</div>'
                '<h1>FinGuía<span style="color:#a6d5a9">.</span></h1>'
                '<p>Entiende tus opciones. Explora escenarios. Encuentra la fuente detrás de cada respuesta.</p>'
                '<span class="badge">Educación financiera · Referencias verificables</span></div>')
        with gr.Tab('Conversar'):
            with gr.Row():
                with gr.Column(scale=7):
                    chat = gr.Chatbot(type='messages',height=410,label='Tu conversación',show_copy_button=True,
                        placeholder='<strong>Una buena decisión empieza con una buena pregunta.</strong><br>Consulta sobre riesgo, diversificación, costes o interés compuesto.')
                    question = gr.Textbox(label='¿Qué quieres entender?',placeholder='¿Diversificar garantiza que no perderé dinero?',lines=2,max_lines=4)
                    with gr.Row():
                        mode = gr.Radio(['Respuesta explicada','Leer fragmentos'],value='Respuesta explicada',label='Cómo responder',scale=3)
                        submit = gr.Button('Consultar ↗',variant='primary',elem_id='ask-button',scale=1)
                    gr.Examples(examples=[
                        ['¿Cuál es la comisión anual vigente de Horizonte A?'],
                        ['¿Diversificar garantiza que no perderé dinero si cae el mercado?'],
                        ['Con rendimiento nominal del 8 % e inflación del 5 %, ¿cuál es la rentabilidad real?'],
                        ['¿Qué es un ETF y cómo se diferencia de un fondo tradicional?'],
                        ['¿Qué pasa con el precio de un bono cuando suben las tasas de interés?'],
                        ['¿Qué señales de fraude financiero debo reconocer?'],
                        ['¿Qué porcentaje de acciones y bonos tiene Horizonte B?'],
                        ['¿Por qué afectan tanto las comisiones pequeñas a largo plazo?'],
                        ['¿Cuánto acumulo con 1000 iniciales y 100 mensuales durante 12 meses a tasa cero?'],
                    ],inputs=question,label='Para empezar',examples_per_page=9)
                    status = gr.Markdown('**Temas disponibles:** horizonte temporal, tolerancia al riesgo, diversificación, '
                        'costes y comisiones, bonos, ETFs, señales de fraude, inflación, interés compuesto, '
                        'Horizonte A/B (ficticios) y el simulador de aportes. Formula cada pregunta completa.')
                    clear = gr.Button('Nueva conversación',size='sm')
                with gr.Column(scale=4):
                    gr.Markdown('### La evidencia\nComprueba de dónde sale la respuesta.')
                    evidence = gr.HTML(evidence_html([]))
            def respond(message,history,chosen_mode):
                if not message.strip():
                    raise gr.Error('Escribe una pregunta para continuar.')
                try:
                    result = assistant.answer(message,'generative' if chosen_mode=='Respuesta explicada' else 'extractive')
                except ValueError as exc:
                    raise gr.Error(str(exc)) from exc
                history = list(history or []) + [{'role':'user','content':message},{'role':'assistant','content':result['answer']}]
                label = 'Fuera de las fuentes disponibles' if result['abstained'] else ('Fragmentos recuperados' if result['fallback'] or chosen_mode=='Leer fragmentos' else 'Respuesta generada con fuentes')
                return '',history,evidence_html(result['evidence']),f'{label} · {result["seconds"]:.1f} s'
            submit.click(respond,[question,chat,mode],[question,chat,evidence,status],api_name='chat',concurrency_limit=1)
            question.submit(respond,[question,chat,mode],[question,chat,evidence,status],api_name=False,concurrency_limit=1)
            clear.click(lambda:('',[],evidence_html([]),'Nueva conversación.'),outputs=[question,chat,evidence,status],api_name=False)
        with gr.Tab('Simular aportes'):
            gr.Markdown('### Dale perspectiva a tu plan\nCambia tus supuestos y observa su efecto. Las curvas son escenarios, no predicciones.')
            with gr.Row():
                with gr.Column(scale=3):
                    initial = gr.Number(value=1000000,label='Capital inicial',minimum=0)
                    monthly = gr.Number(value=100000,label='Aporte mensual',minimum=0)
                    years = gr.Slider(1,40,value=10,step=1,label='Plazo en años')
                    annual_return = gr.Slider(-20,25,value=6,step=.5,label='Rendimiento anual supuesto (%)')
                    annual_fee = gr.Slider(0,5,value=.3,step=.1,label='Comisión anual supuesta (%)')
                    inflation = gr.Slider(0,20,value=3,step=.5,label='Inflación anual supuesta (%)')
                    calculate = gr.Button('Calcular escenario',variant='primary')
                with gr.Column(scale=7):
                    summary,initial_plot = simulator_view(1000000,100000,10,6,.3,3)
                    chart = gr.Plot(initial_plot,label='Evolución del saldo')
                    plt.close(initial_plot)
                    numbers = gr.Markdown(summary)
            calculate.click(simulator_view,[initial,monthly,years,annual_return,annual_fee,inflation],[numbers,chart],api_name='simulate')
        with gr.Tab('Biblioteca'):
            gr.Markdown('### Documentos a la vista\nSíntesis educativas de SEC/Investor.gov y FINRA, más fichas propias del laboratorio. Consulta documental: 10 de octubre de 2026.')
            selector = gr.Dropdown(choices=[(f"{d['doc_id']} · {d['title']}",d['doc_id']) for d in documents],value='D01',label='Documento')
            reader = gr.Markdown((ROOT/documents[0]['path']).read_text(encoding='utf-8'))
            def read_doc(doc_id):
                doc = next(d for d in documents if d['doc_id']==doc_id)
                return (ROOT/doc['path']).read_text(encoding='utf-8')
            selector.change(read_doc,selector,reader,api_name=False)
        gr.Markdown('Educación financiera general; no sustituye una evaluación profesional de tu situación. '
                    'Sin precios en tiempo real ni órdenes de inversión.',elem_classes=['fineprint'])
    return demo

if __name__ == '__main__':
    print('Cargando modelos locales; la primera apertura puede tardar unos segundos.',flush=True)
    assistant = Assistant()
    get_generator()  # precarga modelo; usa generator_small por defecto
    build_demo(assistant).queue().launch(server_name='127.0.0.1',server_port=7860,share=False,
        inbrowser=True,allowed_paths=[str(ROOT/'data/documents')])
