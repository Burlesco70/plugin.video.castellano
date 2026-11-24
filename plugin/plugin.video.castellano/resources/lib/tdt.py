# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""Utility per la lista TDT Channels (stream liberi in formato m3u8)."""

import xbmcaddon

import netutil

ADDON = xbmcaddon.Addon()

DEFAULT_TDT_URL = 'https://www.tdtchannels.com/lists/tv.m3u8'

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    ),
    'Accept': '*/*',
}


def _parse_m3u8(text, base_url=''):
    """Converte il testo di una playlist m3u8 in una lista di dict canale."""
    channels = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    pending = None
    for line in lines:
        if line.startswith('#EXTINF'):
            # estrai tvg-logo, group-title, ecc. dalla riga precedente #EXTINF
            continue
        if line.startswith('#'):
            # metadati (es. #EXTVLCOPT)
            if not pending:
                pending = line
            continue
        # riga con URL dello stream
        name = pending if pending else line
        if pending and pending.startswith('#'):
            name = pending
        pending = None
        channels.append({
            'name': _clean_name(name),
            'url': line,
            'group': '',
            'icon': '',
            'fanart': '',
        })
    return channels


def _clean_name(name):
    name = name.strip()
    if name.startswith('#'):
        name = name[1:].strip()
    return name


def get_channels(tdt_url=None):
    """Scarica e parsa la playlist TDT Channels."""
    url = tdt_url or ADDON.getSetting('tdt_url') or DEFAULT_TDT_URL
    try:
        text = netutil.get_text(url, timeout=20, retries=2)
    except Exception as e:
        return [{'name': 'Errore download TDT: %s' % e, 'url': '',
                 'sources': [], 'mime': '', 'group': '', 'icon': ''}]

    channels = []
    lines = [l.rstrip() for l in text.splitlines()]
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            extinf = line
            # la riga successiva non commentata è l'URL
            j = i + 1
            stream_url = ''
            while j < len(lines):
                cand = lines[j].strip()
                if cand and not cand.startswith('#'):
                    stream_url = cand
                    i = j
                    break
                j += 1
            name = _name_from_extinf(extinf)
            icon = _attr_from_extinf(extinf, 'tvg-logo')
            group = _attr_from_extinf(extinf, 'group-title')
            # Salta i canali marcati come geobloccati nel nome (es. "... GEO").
            if _is_geo(name):
                i += 1
                continue
            if stream_url:
                channels.append({
                    'name': name,
                    'url': stream_url,
                    'icon': icon,
                    'group': group,
                    'fanart': '',
                    'sources': [stream_url],
                    'mime': netutil.guess_mime(stream_url),
                })
        i += 1

    # raggruppa per nome (un canale puo' avere piu' sorgenti) e ordina le
    # sorgenti per affidabilita': penalizza gli URL con token firmati (segmenti
    # es. esadecimali molto lunghi) che scadono e causano problemi di
    # riproduzione. Conserviamo TUTTE le sorgenti ordinate (non solo la prima)
    # cosi' il player puo' ripiegare su un'alternativa se la prima e' morta o
    # geobloccata.
    order = []
    by_name = {}
    for ch in channels:
        nm = ch['name']
        if nm not in by_name:
            by_name[nm] = []
            order.append(nm)
        by_name[nm].append(ch)

    unique = []
    for nm in order:
        ranked = sorted(by_name[nm], key=lambda c: _url_score(c['url']))
        best = dict(ranked[0])
        best['sources'] = [c['url'] for c in ranked]
        best['mime'] = netutil.guess_mime(best['url'])
        unique.append(best)
    return unique


def find_channel(name, group=None):
    """Ritorna il canale (con tutte le sue sorgenti) per nome ed eventuale
    gruppo. Usato dal resolver per ripescare le sorgenti al momento del click."""
    for ch in get_channels():
        if ch['name'] != name:
            continue
        if group is not None and (ch.get('group') or 'Altri') != group:
            continue
        return ch
    return None


def _url_score(url):
    """Punteggio di affidabilita' (più basso = meglio).

    Gli URL con token firmati contengono lunghe sequenze esadecimali e spesso
    scadono: penalizziamoli preferendo sorgenti 'pulite'. Un token reale e'
    lungo (>= 12 caratteri); NON vanno scambiati per token i numeri di
    risoluzione (720/576/1080/2160) ne' le brevi sequenze, altrimenti si
    finisce per scartare la sorgente giusta (es. il feed internazionale
    '..._1080.m3u8') a favore di quella geobloccata.
    """
    longest = 0
    run = 0
    for ch in url:
        if ch in '0123456789abcdefABCDEF':
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # conta come 'token' solo le sequenze davvero lunghe
    return longest if longest >= 12 else 0


def get_groups():
    """Restituisce i gruppi (categorie) presenti, in ordine di apparizione."""
    seen = set()
    groups = []
    for ch in get_channels():
        g = ch.get('group') or 'Altri'
        if g not in seen:
            seen.add(g)
            groups.append(g)
    return groups


def get_channels_by_group(group):
    return [ch for ch in get_channels() if (ch.get('group') or 'Altri') == group]


def _attr_from_extinf(extinf, attr):
    token = '%s="' % attr
    start = extinf.find(token)
    if start == -1:
        return ''
    start += len(token)
    end = extinf.find('"', start)
    if end == -1:
        return ''
    return extinf[start:end]


def _name_from_extinf(extinf):
    # nome = testo dopo l'ultima virgola
    comma = extinf.rfind(',')
    if comma != -1:
        return extinf[comma + 1:].strip()
    # fallback: tvg-name o tvg-id
    return _attr_from_extinf(extinf, 'tvg-name') or _attr_from_extinf(extinf, 'tvg-id') or 'Canale'


def _is_geo(name):
    """True se il nome del canale indica un feed geobloccato (contiene GEO)."""
    tokens = name.upper().replace('-', ' ').replace('_', ' ').split()
    return 'GEO' in tokens