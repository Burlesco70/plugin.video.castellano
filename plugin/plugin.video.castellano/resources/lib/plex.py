# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""
Canali Plex (FAST) Spagna — live gratuiti (con pubblicita').

Plex offre canali FAST gratuiti. A differenza di Samsung, i flussi live di Plex
sono risolvibili in modo pulito:
  1.  Lista canali + token + header regione da (mirror pubblico mjh.nz):
        https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/Plex/.channels.json.gz
  2.  Per ogni canale (key) il master HLS:
        https://epg.provider.plex.tv/library/parts/{key}?X-Plex-Token={token}
     va richiesto con gli header:
        X-Plex-Token: <token>
        X-Forwarded-For: <IP Spagna>   (per il geocontenuto)
        User-Agent: <browser>
     Restituisce un master m3u8 con variante relativa; ISA segue tutto.

Verificato end-to-end (master + variante + segmento .ts) con riproduzione OK.
La lista e il token sono letti dinamicamente dal mirror mjh.nz, cosi' restano
aggiornati; e' un servizio di terzi (buona volonta' / best-effort).
"""

import gzip
import io
import json

import requests

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
)
CHANNELS_JSON_URL = (
    'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/Plex/'
    '.channels.json.gz'
)
PARTS_URL = 'https://epg.provider.plex.tv/library/parts/%s?X-Plex-Token=%s'

REGION = 'es'

_CACHE = None  # dict: token, xff, channels[]


def _load():
    """Scarica e parsa il JSON dei canali Plex (con cache in memoria)."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    try:
        resp = requests.get(CHANNELS_JSON_URL, timeout=25,
                            headers={'User-Agent': USER_AGENT})
        raw = gzip.decompress(resp.content).decode('utf-8')
        data = json.loads(raw)
    except Exception:
        _CACHE = {'token': '', 'xff': '', 'channels': []}
        return _CACHE

    token = data.get('headers', {}).get('X-Plex-Token', '')
    xff = data.get('regions', {}).get(REGION, {}).get('headers', {}).get(
        'X-Forwarded-For', '')

    channels = []
    for key, ch in data.get('channels', {}).items():
        regions = ch.get('regions', '')
        # regions puo' essere lista o stringa tipo "['us', 'es']"
        if isinstance(regions, list):
            has_region = REGION in regions
        else:
            has_region = ("'%s'" % REGION) in regions or ('"%s"' % REGION) in regions
        if not has_region:
            continue
        channels.append({
            'key': key,
            'name': ch.get('name', 'Canale'),
            'icon': ch.get('logo', ''),
        })

    _CACHE = {'token': token, 'xff': xff, 'channels': channels}
    return _CACHE


def get_channels():
    return _load()['channels']


def get_headers():
    """Header HTTP necessari a Plex (token + geo)."""
    d = _load()
    h = {'User-Agent': USER_AGENT, 'X-Plex-Token': d['token']}
    if d['xff']:
        h['X-Forwarded-For'] = d['xff']
    return h


def headers_string():
    """Header in formato 'k=v&k2=v2' per inputstream.adaptive."""
    d = _load()
    parts = ['User-Agent=' + USER_AGENT, 'X-Plex-Token=' + d['token']]
    if d['xff']:
        parts.append('X-Forwarded-For=' + d['xff'])
    return '&'.join(parts)


def resolve(key):
    """URL master HLS del canale Plex (da riprodurre con gli header Plex)."""
    token = _load()['token']
    return PARTS_URL % (key, token)