#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build dello zip installabile dell'add-on Castellano.

- Legge la versione da plugin/spanish_tv/addon.xml
- Esclude file di sviluppo (config.json, __pycache__, *.pyc, .git, ecc.)
- Crea plugin/plugin.video.castellano-<versione>.zip con la cartella
  plugin.video.castellano/ come radice (struttura richiesta da Kodi).

Uso:
    python build.py
"""

import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'plugin', 'plugin.video.castellano')
ADDON_ID = 'plugin.video.castellano'
OUT_DIR = os.path.join(ROOT, 'plugin')

# File/cartelle da escludere dallo zip (mai pubblicare dati personali/build)
EXCLUDE_DIRS = {'__pycache__', '.git', '.idea', '.vscode'}
EXCLUDE_FILES = {
    'config.json',      # credenziali personali
    '.gitignore',
    'Thumbs.db',
    '.DS_Store',
}


def read_version(addon_xml_path):
    with open(addon_xml_path, 'r', encoding='utf-8') as f:
        data = f.read()
    # cerca la versione nel tag <addon ...> (non nella dichiarazione XML)
    m = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', data)
    if not m:
        sys.exit('Versione non trovata in addon.xml')
    return m.group(1)


def iter_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            if name in EXCLUDE_FILES or name.endswith(('.pyc', '.pyo', '.zip')):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, base)
            yield full, rel


def main():
    addon_xml = os.path.join(SRC, 'addon.xml')
    version = read_version(addon_xml)
    out_zip = os.path.join(OUT_DIR, '%s-%s.zip' % (ADDON_ID, version))

    # rimuovi eventuale zip esistente
    if os.path.exists(out_zip):
        os.remove(out_zip)

    count = 0
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for full, rel in iter_files(SRC):
            arcname = os.path.join(ADDON_ID, rel).replace('\\', '/')
            z.write(full, arcname)
            count += 1

    size = os.path.getsize(out_zip)
    print('Creato: %s' % os.path.relpath(out_zip, ROOT))
    print('Versione: %s | File: %d | Dimensione: %d byte' % (version, count, size))


if __name__ == '__main__':
    main()