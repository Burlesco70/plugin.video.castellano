# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""Utilita' di rete condivise: validazione URL, redirect sicuri, retry e
verifica disponibilita' di uno stream.

Da Vaquexflix (fltv_protocol/http_client.py) ho ripreso l'idea di:
  - validate_url: accetta solo http/https, senza credenziali nell'URL ne'
    caratteri di controllo o il separatore '|' usato da Kodi;
  - redirect sicuri: blocca il downgrade https->http e rimuove gli header
    sensibili (Cookie/Authorization) quando si cambia dominio;
  - retry con backoff sui download che falliscono.
In piu' probe_url() per scegliere, tra piu' sorgenti, la prima che risponde.
"""

import time
from urllib.parse import urljoin, urlsplit

import requests

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

# header da non inoltrare a un dominio diverso dopo un redirect
_SENSITIVE = ('authorization', 'cookie', 'content-auth', 'content-license')
_REDIRECT_CODES = (301, 302, 303, 307, 308)


def validate_url(url):
    """Solleva ValueError se l'URL non e' un HTTP(S) valido e sicuro."""
    if not isinstance(url, str) or any(ord(c) < 32 for c in url) or '|' in url:
        raise ValueError('URL non valido')
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname \
            or p.username or p.password:
        raise ValueError('URL non valido: solo HTTP(S) senza credenziali')
    return url


def is_valid_url(url):
    try:
        validate_url(url)
        return True
    except Exception:
        return False


def guess_mime(url):
    """Deduce il mime di un flusso dall'URL (DASH se .mpd, altrimenti HLS)."""
    u = (url or '').lower()
    if '.mpd' in u:
        return 'application/dash+xml'
    return 'application/vnd.apple.mpegurl'


def _strip_sensitive(headers):
    return {k: v for k, v in headers.items()
            if k.lower() not in _SENSITIVE}


def request(method, url, headers=None, timeout=15, retries=2,
            max_redirects=5, stream=False):
    """Esegue una richiesta HTTP con redirect sicuri e retry.

    - valida ogni hop (validate_url);
    - blocca i redirect https -> http;
    - rimuove Cookie/Authorization quando il redirect cambia dominio;
    - riprova fino a `retries` volte con backoff in caso di errore.
    """
    base_headers = dict(headers or {})
    last_exc = None
    for attempt in range(retries + 1):
        current = url
        current_headers = dict(base_headers)
        try:
            resp = None
            for _ in range(max_redirects + 1):
                validate_url(current)
                resp = requests.request(
                    method, current, headers=current_headers,
                    timeout=timeout, allow_redirects=False, stream=stream,
                )
                if resp.status_code in _REDIRECT_CODES:
                    loc = resp.headers.get('Location')
                    if not loc:
                        return resp
                    nxt = urljoin(current, loc)
                    if urlsplit(current).scheme == 'https' \
                            and urlsplit(nxt).scheme != 'https':
                        raise ValueError('Redirect non sicuro (https->http)')
                    if urlsplit(nxt).netloc != urlsplit(current).netloc:
                        current_headers = _strip_sensitive(current_headers)
                    current = nxt
                    resp.close()
                    continue
                return resp
            return resp
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise
    if last_exc:
        raise last_exc


def get_text(url, timeout=15, retries=2, headers=None):
    """Scarica una risorsa di testo (es. playlist m3u8) con retry."""
    hdrs = {'User-Agent': USER_AGENT, 'Accept': '*/*'}
    if headers:
        hdrs.update(headers)
    resp = request('GET', url, headers=hdrs, timeout=timeout, retries=retries)
    resp.raise_for_status()
    return resp.text


def probe_url(url, timeout=5):
    """True se l'URL risponde 200/206 (HEAD, con fallback GET parziale).

    Usato per scegliere tra piu' sorgenti la prima realmente disponibile:
    un feed geobloccato (HTTP 451) o morto viene scartato a favore di quello
    che funziona.
    """
    if not is_valid_url(url):
        return False
    # 1) HEAD (rapido)
    try:
        resp = request('HEAD', url, headers={'User-Agent': USER_AGENT},
                       timeout=timeout, retries=0, stream=True)
        code = resp.status_code
        resp.close()
        if code in (200, 206):
            return True
        if code not in (405, 501):
            # errori "definitivi" (es. 451 geo, 403, 404): prova comunque GET
            pass
    except Exception:
        pass
    # 2) GET parziale (server che non supportano HEAD)
    try:
        resp = request('GET', url, headers={'User-Agent': USER_AGENT,
                       'Range': 'bytes=0-0'}, timeout=timeout, retries=0,
                       stream=True)
        code = resp.status_code
        resp.close()
        return code in (200, 206)
    except Exception:
        return False