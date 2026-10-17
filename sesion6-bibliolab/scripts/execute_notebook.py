import os,time,json
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
os.environ.setdefault('IPYTHONDIR',str(ROOT/'.runtime/ipython'))
os.environ.setdefault('JUPYTER_RUNTIME_DIR',str(ROOT/'.runtime/jupyter'))
def main():
    p=ROOT/'BiblioLab_LangChain.ipynb'
    nb=nbformat.read(p,as_version=4);start=time.perf_counter()
    client=NotebookClient(nb,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
    try:client.execute()
    finally:nbformat.write(nb,p)
    codes=[c for c in nb.cells if c.cell_type=='code']
    errors=[o for c in codes for o in c.get('outputs',[]) if o.output_type=='error']
    report={'code_cells':len(codes),'executed':sum(c.execution_count is not None for c in codes),'errors':len(errors),'seconds':round(time.perf_counter()-start,2),'fresh_kernel':True}
    (ROOT/'results/notebook_execution.json').write_text(json.dumps(report,indent=2))
    html,_=HTMLExporter(template_name='lab').from_notebook_node(nb)
    (ROOT/'BiblioLab_LangChain.html').write_text(html,encoding='utf-8')
    print(report,flush=True)
if __name__=='__main__':main()
