# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""Canali live ufficiali di Telemadrid.

Lo stream si ottiene a runtime dall'API pubblica di Galgo (usata dal sito
www.tlmad.es): restituisce un URL HLS con token sempre fresco, cosi' non
ci sono problemi di scadenza.

Nota: il canale nazionale Telemadrid e' spesso geobloccato fuori dalla
Comunidad de Madrid / Spagna. In tal caso l'API risponde HTTP 403 e viene
mostrato un messaggio esplicito.
"""

import requests

# Endpoint pubblico che restituisce gli URI dello stream per un videoId.
GALGO_URI = 'https://galgo-telemadrid.galgo.tv/video/%s/uri?language=es'

LOGO_BASE = ('https://storage.googleapis.com/galgo-telemadrid.appspot.com/'
             'media/images/')

_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:160.0) '
                   'Gecko/20100101 Firefox/160.0'),
    'Referer': 'https://www.tlmad.es/',
    'Origin': 'https://www.tlmad.es',
    'Accept': 'application/json',
}

# videoId del canale nazionale Telemadrid (Brightcove/Galgo).
TELEMADRID_ID = '6389770581112'

# Canali live ufficiali Telemadrid.
# - Telemadrid (nazionale): geobloccato fuori dalla Spagna (HTTP 403).
# - LaOtra e Internacional: visibili anche dall'estero.
CHANNELS = [
    {
        'id': TELEMADRID_ID,
        'name': 'Telemadrid',
        'logo': LOGO_BASE + 'EPG-LOGO-TELEMADRID.png',
    },
    {
        'id': '6389770474112',
        'name': 'LaOtra',
        'logo': LOGO_BASE + 'EPG-LOGO-LAOTRA.png',
    },
    {
        'id': '6389768804112',
        'name': 'Telemadrid Internacional',
        'logo': LOGO_BASE + 'EPG-LOGO-TELEMADRID-INT.png',
    },
]

# Gruppo TDT in cui inserire Telemadrid come prima voce.
GROUP = 'C. de Madrid'


def _pick_url(uris):
    """Sceglie l'URL HLS piu' stabile tra quelli restituiti dall'API.

    L'API a volte ritorna URL con timestamp '-now' (finestra temporale che
    scade e da' HTTP 400): preferiamo la variante statica 'playlist-hls.m3u8'
    costruita a partire dalla radice dell'URL.
    """
    hls = (uris.get('hls') or {}).get('uri')
    master = uris.get('master')
    dash = (uris.get('dash') or {}).get('uri')
    base = hls or master or dash
    if not base:
        return ''
    root = base.rsplit('/', 1)[0]
    return root + '/playlist-hls.m3u8'


def resolve(video_id):
    """Restituisce (url, errore). Uno dei due e' sempre None."""
    try:
        resp = requests.get(GALGO_URI % video_id, headers=_HEADERS, timeout=20)
    except Exception as e:
        return None, 'Errore di rete Telemadrid: %s' % e

    if resp.status_code == 403:
        return None, ('Telemadrid e\' geobloccato fuori dalla Spagna '
                      '(HTTP 403). Serve una connessione spagnola o una VPN.')
    if resp.status_code != 200:
        return None, 'Telemadrid: risposta HTTP %s' % resp.status_code

    try:
        data = resp.json()
    except Exception:
        return None, 'Telemadrid: risposta non valida.'

    stream = _pick_url(data.get('uris') or {})
    if not stream:
        return None, 'Telemadrid: nessuno stream disponibile.'
    return stream, None


def headers_string():
    """Header in formato 'k=v&k2=v2' per inputstream.adaptive."""
    return '&'.join('%s=%s' % (k, v) for k, v in _HEADERS.items())