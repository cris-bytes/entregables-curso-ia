#!/bin/bash
set -e
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Falta el entorno. Sigue la instalación del README usando Python 3.12.'
  read -r -p 'Pulsa Enter para salir.'
  exit 1
fi
export JUPYTER_RUNTIME_DIR="$PWD/.jupyter/runtime"
export JUPYTER_CONFIG_DIR="$PWD/.jupyter/config"
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
mkdir -p "$JUPYTER_RUNTIME_DIR"
exec .venv/bin/python -m jupyterlab FinGuia_RAG_Inversion.ipynb
