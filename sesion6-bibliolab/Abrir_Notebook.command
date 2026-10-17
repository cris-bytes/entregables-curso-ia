#!/bin/bash
set -e
cd -- "$(dirname "$0")"
export JUPYTER_RUNTIME_DIR="$PWD/.runtime/jupyter"
export IPYTHONDIR="$PWD/.runtime/ipython"
export MPLCONFIGDIR="$PWD/.runtime/matplotlib"
exec .venv/bin/python -m jupyterlab BiblioLab_LangChain.ipynb
