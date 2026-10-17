"""Arranque local: no descarga ni instala servicios implícitamente."""
import atexit
import os
import shutil
import subprocess
import time
import httpx
from bibliolab.core import ROOT,write_json
from bibliolab.assistant import BASE_URL,MODEL

_process=None
_log=None

def ensure_ollama():
    global _process,_log
    try:
        response=httpx.get(BASE_URL+'/api/tags',timeout=3);response.raise_for_status()
    except httpx.HTTPError:
        binary=ROOT/'.runtime/ollama/ollama'
        executable=str(binary) if binary.exists() else shutil.which('ollama')
        if not executable:raise RuntimeError('Instala Ollama, descarga los modelos y sigue README.md.')
        runtime=ROOT/'.runtime';runtime.mkdir(exist_ok=True)
        env={**os.environ,'OLLAMA_HOST':BASE_URL.removeprefix('http://'),'OLLAMA_NO_CLOUD':'1'}
        if binary.exists():env['OLLAMA_MODELS']=str(runtime/'models')
        _log=(runtime/'ollama.log').open('a')
        _process=subprocess.Popen([executable,'serve'],env=env,stdout=_log,stderr=_log)
        atexit.register(stop_owned_ollama)
        for _ in range(30):
            try:
                response=httpx.get(BASE_URL+'/api/tags',timeout=1);response.raise_for_status();break
            except httpx.HTTPError:time.sleep(.5)
        else:raise RuntimeError('Ollama no arrancó. Revisa .runtime/ollama.log.')
    models=response.json().get('models',[])
    match=next((m for m in models if m['name']==MODEL),None)
    if not match:raise RuntimeError(f'Falta {MODEL}. Descárgalo siguiendo README.md antes de ejecutar.')
    return match

def stop_owned_ollama():
    if _process and _process.poll() is None:
        _process.terminate()
        try:_process.wait(timeout=5)
        except subprocess.TimeoutExpired:_process.kill();_process.wait()
    if _log:_log.close()
