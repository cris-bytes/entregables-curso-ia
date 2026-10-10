#!/bin/bash
set -e
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Falta el entorno. Sigue la instalación del README usando Python 3.12.'
  read -r -p 'Pulsa Enter para salir.'
  exit 1
fi
export GRADIO_ANALYTICS_ENABLED=False
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
echo 'Iniciando FinGuía. Mantén esta ventana abierta mientras uses el chatbot.'
exec .venv/bin/python app.py
