"""Servidor local para la verificación visual; el token solo se guarda en .runtime."""
import os,secrets
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runtime';runtime.mkdir(exist_ok=True)
os.environ['JUPYTER_RUNTIME_DIR']=str(runtime/'jupyter')
os.environ['IPYTHONDIR']=str(runtime/'ipython')
token=secrets.token_hex(24)
token_path=runtime/'jupyter-token';token_path.write_text(token);token_path.chmod(0o600)
config=runtime/'jupyter_demo_config.py'
config.write_text(f"c.IdentityProvider.token = {token!r}\nc.ServerApp.ip = '127.0.0.1'\nc.ServerApp.port = 8892\nc.ServerApp.root_dir = {str(ROOT)!r}\nc.ServerApp.open_browser = False\nc.LabApp.expose_app_in_browser = True\n")
config.chmod(0o600)
os.execv(sys.executable,[sys.executable,'-m','jupyterlab','--config',str(config)])
