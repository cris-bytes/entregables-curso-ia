"""Interfaz compartida por el notebook y el lanzador local."""
import json
import os
import gradio as gr
from bibliolab.assistant import Assistant,evidence_markdown
from bibliolab.core import ROOT,catalog

MODES={'Consulta guiada':'guiado','Agente autónomo':'agente','Solo documentos':'rag','Solo modelo':'solo'}

def build_demo():
    assistant=Assistant()
    async def respond(question,history,mode):
        if not question.strip():return '',history,'Escribe una pregunta.',{}
        result=await assistant.ask(question,history,mode=MODES[mode])
        answer=result['answer']
        if result['allowed_references']:
            answer+='\n\n**Fuentes consultadas** (adjuntas por la aplicación): '+', '.join('['+r+']' for r in result['allowed_references'])
        history=(history or [])+[{'role':'user','content':question},{'role':'assistant','content':answer}]
        return '',history,evidence_markdown(result),{'modo':mode,'segundos':result['seconds'],'herramientas':result['calls'],'error':result['error'],'advertencia_citas':result['citation_warning']}

    with gr.Blocks(title='BiblioLab · X-Ray',theme=gr.themes.Soft(primary_hue='teal'),css='.gradio-container {max-width: 1200px !important;}') as demo:
        gr.Markdown('# BiblioLab\nConsulta las reglas, explora el catálogo y calcula una devolución. **Biblioteca ficticia · Grupo X-Ray**')
        gr.Markdown('Catálogo con corte **16 de octubre de 2026**. Las consultas no crean préstamos ni reservas.')
        with gr.Tab('Asistente'):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot=gr.Chatbot(type='messages',label='Conversación',height=410)
                    question=gr.Textbox(label='Tu pregunta',placeholder='¿Puedo llevar un portátil a casa?',lines=2,max_lines=4)
                    with gr.Row():
                        send=gr.Button('Consultar',variant='primary');clear=gr.Button('Nueva conversación')
                    gr.Examples(examples=[['¿Puedo llevar un portátil a casa?'],['Busca Procesamiento de lenguaje natural y dime cuántos ejemplares hay disponibles.'],['Soy estudiante. Si pido un libro el 2026-10-09, ¿cuál es la fecha de devolución?']],inputs=question)
                with gr.Column(scale=2):
                    evidence=gr.Markdown('Las fuentes de tu última consulta aparecerán aquí.',label='Evidencia',elem_id='evidencia')
            with gr.Accordion('Comparar estrategias y revisar ejecución',open=False):
                mode=gr.Dropdown(list(MODES),value='Consulta guiada',label='Estrategia')
                gr.Markdown('Guiada: reglas explícitas eligen herramientas. Autónomo: el modelo decide. Las citas se comprueban por identificador; esa comprobación no garantiza que toda la respuesta sea fiel.')
                trace=gr.JSON(label='Registro de la última consulta')
            send.click(respond,[question,chatbot,mode],[question,chatbot,evidence,trace],api_name='consultar',concurrency_limit=1)
            question.submit(respond,[question,chatbot,mode],[question,chatbot,evidence,trace],concurrency_limit=1)
            clear.click(lambda:('',[],'Las fuentes de tu última consulta aparecerán aquí.',{}),outputs=[question,chatbot,evidence,trace],queue=False)
        with gr.Tab('Documentos y catálogo'):
            gr.Markdown('Material original del laboratorio, no reglamentos de una universidad real. Descarga las fuentes para contrastar una respuesta.')
            gr.File(value=[str(p) for p in sorted((ROOT/'data/documents').glob('*.md'))]+[str(ROOT/'data/catalogo.csv'),str(ROOT/'data/cierres.csv')],label='Fuentes del caso',interactive=False)
            rows=catalog()
            gr.Dataframe(value=[[r[k] for k in ['id','titulo','area','total','disponibles']] for r in rows],headers=['ID','Título','Área','Total','Disponibles'],interactive=False)
    return demo

if __name__=='__main__':
    from bibliolab.runtime import ensure_ollama
    ensure_ollama()
    build_demo().queue().launch(server_name='127.0.0.1',server_port=int(os.getenv('BIBLIOLAB_PORT','7862')),inbrowser=True,share=False)
