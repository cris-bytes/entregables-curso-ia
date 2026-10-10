"""Exporta el informe sin iniciar Jupyter ni escribir configuración global."""
from pathlib import Path
import nbformat
from nbconvert import HTMLExporter

ROOT=Path(__file__).resolve().parents[1]

def main():
    notebook=nbformat.read(ROOT/'FinGuia_RAG_Inversion.ipynb',as_version=4)
    # Una interfaz local no sigue viva dentro de un HTML estático.
    # El notebook original conserva íntegra la salida real de launch().
    for cell in notebook.cells:
        for output in cell.get('outputs',[]):
            data=output.get('data',{})
            if '<iframe' in data.get('text/html',''):
                data['text/html']=('<p>Captura de la aplicación probada. Para interactuar, ejecuta '
                    '<code>Iniciar_FinGuia.command</code> o la celda de Gradio del notebook.</p>'
                    '<img src="results/figures/05_demo_chat.png" alt="FinGuía: respuesta con referencia documental" '
                    'style="max-width:100%;height:auto">')
    body,_=HTMLExporter(template_name='lab').from_notebook_node(notebook)
    path=ROOT/'FinGuia_RAG_Inversion.html'
    path.write_text(body,encoding='utf-8')
    print(f'{path.name}: {path.stat().st_size/1e6:.2f} MB')

if __name__=='__main__':
    main()
