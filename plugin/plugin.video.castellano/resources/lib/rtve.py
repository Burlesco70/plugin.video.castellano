# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""
Supporto per i canali in diretta di RTVE Play (rtve.es/play).

Come funziona la risoluzione (verificato sulle API pubbliche di RTVE):
  1. Ogni canale in diretta ha un "player id" numerico (La 1=1, La 2=2,
     Teledeporte=3, 24h=4, Clan=558, ...).
  2. L'endpoint pubblico
        https://api.rtve.es/api/lives/broadcasts/{player_id}.json
     restituisce il campo "idGolumi" (es. "rtvesec/la2/la2_main_").
  3. Lo stream HLS si ottiene come:
        https://rtvelivestream.rtve.es/{idGolumi}dvr.m3u8

Nota importante sul geoblock:
  I flussi rtvelivestream.rtve.es sono soggetti a geolocalizzazione: fuori
  dalla Spagna molti canali rispondono HTTP 451. Alcuni contenuti (sport,
  ecc.) possono richiedere login e/o DRM. Il login RTVE viene gestito qui
  come cookie di sessione opzionale: se il tuo IP puo' vedere i canali sul
  sito, il plugin li riproduce; altrimenti vanno usati da rete spagnola/VPN.
"""

import requests
import xbmcaddon

ADDON = xbmcaddon.Addon()

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': USER_AGENT,
    'Accept': 'application/json, text/plain, */*',
})

STREAM_BASE = 'https://rtvelivestream.rtve.es/'
BROADCASTS_API = 'https://api.rtve.es/api/lives/broadcasts/{0}.json'

# Canali lineari in diretta. "id" = player id usato dalle API broadcasts.
RTVE_CHANNELS = [
    {'id': '1',   'name': 'La 1',         'slug': 'la-1', 'icon': 'https://css.rtve.es/css/rtve.directos/logos_cadenas/tv-la1_nac.png'},
    {'id': '2',   'name': 'La 2',         'slug': 'la-2', 'icon': 'https://css.rtve.es/css/rtve.directos/logos_cadenas/tv-la2_nac.png'},
    {'id': '3',   'name': 'Teledeporte',  'slug': 'tdp',  'icon': 'https://css.rtve.es/css/rtve.directos/logos_cadenas/tv-teledeporte_nac.png'},
    {'id': '4',   'name': '24h',          'slug': '24h',  'icon': 'https://css.rtve.es/css/rtve.directos/logos_cadenas/tv-24-horas_nac.png'},
    {'id': '558', 'name': 'Clan',         'slug': 'clan', 'icon': 'https://css.rtve.es/css/rtve.directos/logos_cadenas/tv-clan_nac.png'},
]

# Endpoint di login (best-effort). Se RTVE cambia endpoint, adeguare qui.
LOGIN_URL = 'https://api.rtve.es/api/login'


def _read_config():
    import os
    import json
    path = os.path.join(ADDON.getAddonInfo('path'), 'config.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_credentials(email='', password=''):
    """Ritorna (email, password): dalle impostazioni, altrimenti da config.json."""
    if not email or not password:
        cfg = _read_config()
        email = email or cfg.get('rtve_email', '')
        password = password or cfg.get('rtve_password', '')
    return email, password


def get_channel_list():
    return RTVE_CHANNELS


def login(email, password):
    """
    Tenta il login su RTVE (best-effort).
    Ritorna True se il server imposta un cookie di sessione.

    Nota: molti canali in diretta sono riproducibili anche senza login se
    l'IP e' autorizzato. Il login serve soprattutto per contenuti on-demand.
    """
    email, password = get_credentials(email, password)
    if not email or not password:
        return False
    try:
        resp = SESSION.post(
            LOGIN_URL,
            json={'email': email, 'password': password},
            timeout=20,
            headers={'Referer': 'https://www.rtve.es/'},
        )
        return bool(resp.cookies)
    except Exception:
        return False


def _get_idgolumi(player_id):
    """Legge idGolumi dal'endpoint broadcasts per il canale."""
    try:
        resp = SESSION.get(
            BROADCASTS_API.format(player_id),
            timeout=20,
            headers={'Referer': 'https://www.rtve.es/'},
        )
        resp.raise_for_status()
        items = resp.json().get('page', {}).get('items', [])
        if items and items[0].get('idGolumi'):
            return items[0]['idGolumi']
    except Exception:
        pass
    return None


def resolve_stream(channel_id, email='', password=''):
    """
    Risolve l'URL HLS (.m3u8) del canale in diretta.
    Ritorna l'URL o None.
    """
    player_id = None
    for ch in RTVE_CHANNELS:
        if ch['id'] == channel_id or ch['slug'] == channel_id:
            player_id = ch['id']
            break
    if player_id is None:
        return None

    idgolumi = _get_idgolumi(player_id)
    if not idgolumi:
        return None

    # variante DVR (con restart/timeshift); se non disponibile si ripiega su live
    return STREAM_BASE + idgolumi + 'dvr.m3u8'