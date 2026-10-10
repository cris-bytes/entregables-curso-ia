"""Empaqueta únicamente archivos de entrega, nunca cachés ni credenciales."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
TOP=['README.md','RAG.py','app.py','requirements.txt','requirements-lock-macos-py312.txt',
     'models.lock.json','.gitignore','Iniciar_FinGuia.command','Abrir_Notebook.command',
     'FinGuia_RAG_Inversion.ipynb','FinGuia_RAG_Inversion.html']
DIRECTORIES=['data','docs','finguia','scripts','tests','results']

def main():
    files=[ROOT/name for name in TOP if (ROOT/name).is_file()]
    for directory in DIRECTORIES:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and
                     '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log'})
    destination=ROOT/'FinGuia_entregable.zip'
    with ZipFile(destination,'w',compression=ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path,Path('FinGuia')/path.relative_to(ROOT))
    print(f'{destination.name}: {len(files)} archivos; {destination.stat().st_size/1e6:.2f} MB')

if __name__=='__main__':
    main()
