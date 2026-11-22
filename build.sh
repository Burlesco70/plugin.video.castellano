#!/usr/bin/env bash
# Wrapper per build.py (Windows Git Bash / Linux / macOS)
set -e
cd "$(dirname "$0")"
python build.py
# se "python" non e' disponibile prova "python3"
if [ $? -ne 0 ]; then
  python3 build.py
fi