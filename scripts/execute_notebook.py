"""Ejecuta todas las celdas desde un kernel limpio y guarda salidas verdaderas."""
import json
import os
import time
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('JUPYTER_RUNTIME_DIR',str(ROOT/'.jupyter/runtime'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED','False')

def main():
    path=ROOT/'FinGuia_RAG_Inversion.ipynb'
    notebook=nbformat.read(path,as_version=4)
    for cell in notebook.cells:
        if cell.cell_type=='code':
            cell.outputs=[]
            cell.execution_count=None
    started=time.perf_counter()
    def announce(cell,cell_index,**kwargs):
        if cell.cell_type=='code':
            print(f'Ejecutando celda {cell_index+1}/{len(notebook.cells)}: {cell.source.splitlines()[0][:100]}',flush=True)
    client=NotebookClient(notebook,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}},
        allow_errors=False,on_cell_start=announce)
    try:
        client.execute()
    finally:
        nbformat.write(notebook,path)
    errors=[out for cell in notebook.cells if cell.cell_type=='code' for out in cell.outputs if out.output_type=='error']
    executed=sum(cell.cell_type=='code' and cell.execution_count is not None for cell in notebook.cells)
    report=dict(executed_code_cells=executed,total_code_cells=sum(c.cell_type=='code' for c in notebook.cells),
                errors=len(errors),seconds=round(time.perf_counter()-started,2),fresh_kernel=True)
    assert not errors and report['executed_code_cells']==report['total_code_cells']
    (ROOT/'results/notebook_execution.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
