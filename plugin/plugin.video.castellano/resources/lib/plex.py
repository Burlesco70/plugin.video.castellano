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
import xbmcaddon

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


def _user_token():
    """Token Plex personale dalle impostazioni (se presente)."""
    try:
        return xbmcaddon.Addon().getSetting('plex_token').strip()
    except Exception:
        return ''


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

    # token: preferisci quello personale dalle impostazioni, altrimenti pubblico
    token = _user_token() or data.get('headers', {}).get('X-Plex-Token', '')
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
            'group': _classify(ch.get('name', '')),
        })

    # ordina per nome dentro ogni gruppo (menu piu' leggibile)
    channels.sort(key=lambda c: c['name'].lower())
    _CACHE = {'token': token, 'xff': xff, 'channels': channels}
    return _CACHE


# Parole chiave (spagnolo/inglese) -> categoria, in ordine di priorita'.
# Matching case-insensitive e senza accenti (es. "accion" trova "Acción").
_CATEGORIES = [
    ('Bambini', ['infantil', 'kids', 'nin', 'anime', 'cartoon', 'dibujos',
                 'junior', 'baby einstein', 'beyblade', 'brat', 'lewed',
                 'h2o', 'masha', 'pitufo', 'skwad', 'sonic', 'toon',
                 'watch it kid', 'wiggles', 'yu-gi-oh', 'the wiggles']),
    ('Musica', ['musica', 'music', 'stingray', 'trace', 'karaoke',
                'conciertos', 'concert', 'radio', 'rock', 'pop', 'billboard',
                'hit list', 'hits', 'hip-hop', 'hip hop', 'jazz', '90s', '80s',
                '70s', 'y2k', 'flashback', 'revry', 'euro hits', 'greatest',
                'smooth jazz']),
    ('Sport', ['deporte', 'sport', 'futbol', 'golf', 'tenis', 'tennis', 'poker',
               'motor', 'ciclismo', 'baloncesto', 'ufc', 'mma', 'wrestling',
               'kickbox', 'boxing', 'nfl', 'fifa', 'dfb', 'football', 'soccer',
               'cricket', 'billiard', 'billar', 'bowling', 'cornhole', 'pickle',
               'strongman', 'surfer', 'surf league', 'bassmaster', 'racing',
               'racer', 'racing america', 'powernation', 'pursuitup',
               'fuel tv', 'speedvision', 'glory', 'nhra', 'unbeaten',
               'pac-12', 'man city', 'inter 24', 'swac', 'xfc', 'tna',
               'monster jam', 'hard knocks']),
    ('Notiziari', ['euronews', 'news', 'noticias', '24h', 'bloomberg',
                   'informa', 'reuters', 'usa today', 'yahoo finance', 'france 24',
                   'tv5monde info', 'milenio', 'growthday', 'actualidad',
                   'cnn', 'comercio']),
    ('Crime', ['crimen', 'crime', 'forense', 'nosey', 'investigaci', 'detective',
               'polic', 'cops', 'jail', 'cheaters', 'repo', 'misterios',
               'sangre fria', 'sucesos', 'alerta']),
    ('Documentari', ['documental', 'doc ', 'doc+', 'docs', 'historia', 'history',
                     'naturaleza', 'salvaje', 'wild', 'nature', 'discovery',
                     'viajes', 'travel', 'cosmic', 'qwest', 'mythical',
                     'life down under', 'ice pilots', 'wired2fish', 'prof g']),
    ('Commedia', ['comedia', 'comedy', 'humor', 'romantica', 'just for laughs',
                  'carol burnett', 'ed sullivan', 'johnny carson', 'standup',
                  'stand up', 'gags']),
    ('Serie', ['series', 'serie ', 'sitcom', 'drama', 'thriller', 'western',
               'telenovela', 'novela', 'andromeda', 'farscape', 'mutant',
               'hunter', 'merli', 'curro jimenez', 'dick van dyke', 'bold',
               '21 jump', 'legacy', 'lonestar', 'bizaar', 'addict', 'z nation',
               'dos vidas', 'rcm']),
    ('Cinema', ['cine', 'cinema', 'movie', 'movies', 'film', 'pelicula',
                'pelimex', 'moviesphere', 'trailers', 'galxy', 'classics',
                'clasicos', 'free tv clasico', 'peli']),
    ('Lifestyle', ['cocina', 'hogar', 'lifestyle', 'salud', 'moda', 'craft',
                   'ideas en 5', 'mueble', 'gustotv', 'gusto', 'mi casa',
                   'design', 'em eril', 'em eril', 'emeril', 'martha', 'spa',
                   'homeful', 'platos', 'tastemade', 'chefs', 'voyage',
                   'journy', 'buen viaje', 'fashion', '5-minute', 'comercio',
                   'the spa', 'wedo', 'amor', 'corazon']),
    ('Intrattenimento', ['failarmy', 'fail army', 'people are awesome', 'shark',
                         'dr. phil', 'dr phil', 'dog whisperer', 'cesar',
                         'bondi', 'hot ones', 'hollywood', 'made in', 'more u',
                         'alternative', 'bizaar', '123go', 'wineman', 'real']),
]


def _norm(text):
    """Minuscolo e senza accenti, per il match delle parole chiave."""
    import unicodedata
    text = text.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')


def _classify(name):
    low = _norm(name)
    for cat, kws in _CATEGORIES:
        for kw in kws:
            if kw in low:
                return cat
    return 'Altri'


def get_groups():
    """Categorie presenti, ordinate per numero di canali (discendente)."""
    from collections import Counter
    cnt = Counter(ch['group'] for ch in _load()['channels'])
    return [g for g, _ in sorted(cnt.items(), key=lambda x: (-x[1], x[0]))]


def get_channels_by_group(group):
    return [ch for ch in _load()['channels'] if ch['group'] == group]


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
    token = _user_token() or d['token']
    parts = ['User-Agent=' + USER_AGENT, 'X-Plex-Token=' + token]
    if d['xff']:
        parts.append('X-Forwarded-For=' + d['xff'])
    return '&'.join(parts)


def resolve(key):
    """URL master HLS del canale Plex (da riprodurre con gli header Plex)."""
    token = _user_token() or _load()['token']
    return PARTS_URL % (key, token)