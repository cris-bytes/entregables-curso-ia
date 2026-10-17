#!/bin/bash
set -e
cd -- "$(dirname "$0")"
export MPLCONFIGDIR="$PWD/.runtime/matplotlib"
exec .venv/bin/python app.py
