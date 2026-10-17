from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
TOP=['README.md','app.py','requirements.txt','requirements-lock-macos-py312.txt','models.lock.json','.gitignore','Abrir_Notebook.command','Iniciar_BiblioLab.command','BiblioLab_LangChain.ipynb','BiblioLab_LangChain.html']
DIRS=['bibliolab','scripts','data','results','tests']
def deliverable_files():
    files=[ROOT/f for f in TOP if (ROOT/f).exists()]
    for folder in DIRS:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'})
    return sorted(files)
def main():
    output=ROOT/'BiblioLab_entregable.zip'
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for p in deliverable_files():z.write(p,'BiblioLab/'+str(p.relative_to(ROOT)))
    print(output,output.stat().st_size,'bytes')
if __name__=='__main__':main()
