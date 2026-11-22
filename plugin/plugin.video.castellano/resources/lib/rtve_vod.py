# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""
RTVE Play - contenuti on-demand (VOD) con sottotitoli.

Risoluzione (verificata sulle API pubbliche di RTVE):
  - Ogni programma ha una pagina /play/videos/<slug>/ che contiene
    l'id del programma (api/programas/<pid>).
  - Gli episodi si elencano da api/programas/<pid>/videos.
  - Il flusso di un video (id) si ottiene da:
        https://ztnr.rtve.es/ztnr/<id>.m3u8
    che reindirizza (302) al master HLS reale (spesso senza DRM).
  - I sottotitoli (file .vtt esterni, che Kodi gestisce bene) da:
        https://www.rtve.es/api/videos/<id>/subtitulos.json

Nota: alcuni contenuti sono protetti da DRM (FairPlay/Widevine) e NON sono
riproducibili con Kodi base. Qui privilegiamo programmi solitamente senza DRM
(documentari, serie storiche, ecc.). I sottotitoli esterni caricati da file
funzionano senza il blocco dei sottotitoli "live".
"""

import re

import requests

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)
BASE = 'https://www.rtve.es'
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': USER_AGENT,
    'Accept': 'application/json, text/html, */*',
    'Referer': BASE + '/',
})

# Programmi on-demand selezionati (slug pagina + nome mostrato).
# Documentari e telegiornali verificati senza DRM e con sottotitoli.
PROGRAMS = [
    # --- Telegiornali ---
    {'slug': 'telediario-1',            'name': 'Telediario 1 (La 1)'},
    {'slug': 'telediario-2',            'name': 'Telediario 2 (La 2)'},
    # --- Documentari ---
    {'slug': 'el-documental',           'name': 'El Documental'},
    {'slug': 'documaster',              'name': 'Documaster'},
    {'slug': 'documentartve',           'name': 'Documenta TVE'},
    {'slug': 'arqueomania',             'name': 'Arqueomanía'},
    {'slug': 'espanoles-en-el-mundo',   'name': 'Españoles en el mundo'},
    {'slug': 'aqui-la-tierra',          'name': 'Aquí la Tierra'},
    {'slug': 'cronicas-de-un-pueblo',   'name': 'Crónicas de un pueblo'},
    {'slug': 'repor.documental',        'name': 'Repor'},
    # --- Serie (extra) ---
    {'slug': 'cuentame-como-paso',      'name': 'Cuéntame cómo pasó'},
    {'slug': 'aguila-roja',             'name': 'Águila Roja'},
]

# Cache id programma per slug
_PID_CACHE = {}


def get_programs():
    return PROGRAMS


def get_program_id(slug):
    """Legge l'id programma dalla pagina /play/videos/<slug>/."""
    if slug in _PID_CACHE:
        return _PID_CACHE[slug]
    try:
        html = SESSION.get('%s/play/videos/%s/' % (BASE, slug), timeout=20).text
        m = re.search(r'api/programas/(\d+)', html)
        if m:
            _PID_CACHE[slug] = m.group(1)
            return _PID_CACHE[slug]
    except Exception:
        pass
    return None


def get_episodes(slug, limit=40):
    """Elenca gli episodi di un programma (id, titolo, thumb)."""
    pid = get_program_id(slug)
    if not pid:
        return []
    try:
        resp = SESSION.get(
            '%s/api/programas/%s/videos' % (BASE, pid), timeout=20)
        resp.raise_for_status()
        items = resp.json().get('page', {}).get('items', [])
    except Exception:
        return []
    out = []
    for it in items[:limit]:
        vid = it.get('id')
        if not vid:
            continue
        out.append({
            'id': str(vid),
            'title': (it.get('title') or it.get('longTitle') or 'Video').strip(),
            'thumb': it.get('thumbnail') or '',
        })
    return out


def get_subtitles(video_id, langs=('es',)):
    """Ritorna la lista di URL .vtt dei sottotitoli richiesti."""
    try:
        resp = SESSION.get(
            '%s/api/videos/%s/subtitulos.json' % (BASE, video_id),
            timeout=20)
        resp.raise_for_status()
        items = resp.json().get('page', {}).get('items', [])
    except Exception:
        return []
    urls = []
    for it in items:
        lang = (it.get('lang') or '').lower()
        src = it.get('src')
        if src and lang in langs:
            urls.append(src)
    return urls


def resolve_url(video_id):
    """URL del master HLS del video (ISA segue il redirect 302)."""
    return 'https://ztnr.rtve.es/ztnr/%s.m3u8' % video_id