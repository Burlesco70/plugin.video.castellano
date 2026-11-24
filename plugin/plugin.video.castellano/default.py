# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
#
# Castellano - TV spagnola
# Copyright (C) 2026 Burlesco70
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Castellano - TV spagnola
Plugin Kodi personale per imparare lo spagnolo guardando la TV spagnola.

Menu:
  - Lista TDT Channels (stream liberi, m3u8 pubblico)
  - Canali RTVE Play (richiede login email/password)
"""

import os
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_ID = ADDON.getAddonInfo('id')

# Aggiungi resources/lib al path di importazione
_LIB_DIR = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'lib')
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import tdt
import rtve
import rtve_vod
import pluto
import samsung
import plex
import telemadrid
import netutil
BASE_URL = sys.argv[0]
HANDLE = int(sys.argv[1])


def build_url(query):
    """Crea un URL del plugin con i parametri passati."""
    return BASE_URL + '?' + urllib.parse.urlencode(query)


def add_dir_item(title, query, art=None, fanart=None, plot=''):
    """Aggiunge una voce di menu (cartella)."""
    li = xbmcgui.ListItem(label=title)
    if art:
        li.setArt(art)
    if fanart:
        li.setProperty('fanart_image', fanart)
    if plot:
        li.setInfo('video', {'plot': plot})
    xbmcplugin.addDirectoryItem(
        HANDLE, build_url(query), li, isFolder=True
    )


USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

# mime che indicano un manifest HLS/DASH ( InputStream Adaptive )
_MANIFEST_MIMES = (
    'application/vnd.apple.mpegurl',
    'application/x-mpegurl',
    'application/dash+xml',
)


def _has_adaptive():
    """True se InputStream Adaptive e' installato nel Kodi dell'utente."""
    return xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)')


def _headers_string(headers):
    """Normalizza gli header in 'k=v&k2=v2' (valori url-encoded) per
    inputstream.adaptive. Accetta un dict oppure una stringa gia' pronta
    (es. quella restituita da plex/telemadrid.headers_string())."""
    if not headers:
        return ''
    if isinstance(headers, str):
        return headers
    parts = []
    for key, value in headers.items():
        parts.append('%s=%s' % (key, urllib.parse.quote(str(value), safe='')))
    return '&'.join(parts)


def _configure_stream_item(li, mime, headers=None, subtitles=None):
    """Applica a un ListItem i settaggi di riproduzione comuni (mime,
    content lookup, InputStream Adaptive, header, sottotitoli).

    Restituisce True se il flusso e' configurabile, False se e' richiesto
    InputStream Adaptive per un DASH ma non e' installato.
    """
    li.setProperty('IsPlayable', 'true')
    li.setMimeType(mime)
    # per gli stream non serve la ricerca di metadati: la disattiviamo
    li.setContentLookup(False)
    is_manifest = mime in _MANIFEST_MIMES
    adaptive = is_manifest and _has_adaptive()
    if mime == 'application/dash+xml' and not adaptive:
        return False
    if adaptive:
        li.setProperty('inputstream', 'inputstream.adaptive')
        hs = _headers_string(headers)
        if hs:
            li.setProperty('inputstream.adaptive.manifest_headers', hs)
            li.setProperty('inputstream.adaptive.stream_headers', hs)
    if subtitles:
        li.setSubtitles(subtitles)
    return True


def play_resolved(stream_url, title='', mime='application/vnd.apple.mpegurl',
                  headers=None, subtitles=None):
    """Resolve un flusso e lo passa al player con setResolvedUrl.

    Punto di ingresso unico per tutti i canali 'resolver' (Plex, Telemadrid,
    Pluto, RTVE, VOD): gestisce in modo coerente mime, header, content lookup
    e InputStream Adaptive.
    """
    li = xbmcgui.ListItem(label=title, path=stream_url, offscreen=True)
    if not netutil.is_valid_url(stream_url):
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(ADDON_NAME, 'URL dello stream non valido.')
        return
    if not _configure_stream_item(li, mime, headers=headers, subtitles=subtitles):
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Per questo canale (DASH) serve InputStream Adaptive: installalo '
            'dal repository ufficiale di Kodi.',
        )
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def add_video_item(title, url, icon=None, fanart=None, plot='', mode='direct',
                   headers=None, mime=None):
    """Aggiunge una voce video.

    mode='direct'   -> url e' il flusso HLS/DASH diretto: Kodi lo riproduce al
                       click. Gli header (se non specificati) defaultano a un
                       User-Agent browser generico, utile per i CDN che li
                       pretendono.
    mode='resolver' -> url e' un plugin://...: al click Kodi esegue il plugin
                       che chiama setResolvedUrl per ottenere lo stream.
    """
    li = xbmcgui.ListItem(label=title, offscreen=True)
    info = {'title': title, 'mediatype': 'video'}
    if plot:
        info['plot'] = plot
    li.setInfo('video', info)
    if icon:
        li.setArt({'thumb': icon, 'icon': icon})
    if fanart:
        li.setProperty('fanart_image', fanart)
    li.setProperty('IsPlayable', 'true')
    li.setContentLookup(False)
    if mode == 'direct':
        if not netutil.is_valid_url(url):
            return
        if mime is None:
            mime = netutil.guess_mime(url)
        # header di default: un User-Agent browser (i TDT/CDN lo gradiscono)
        hdrs = headers if headers is not None else {'User-Agent': USER_AGENT}
        _configure_stream_item(li, mime, headers=hdrs)
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=False)


def show_main_menu():
    # --- TV in diretta (azzurro) ---
    add_dir_item('[COLOR FF33B5E5]Canali RTVE in diretta[/COLOR]', {'action': 'rtve'})
    add_dir_item('[COLOR FF33B5E5]Canali TDT (per categoria)[/COLOR]', {'action': 'tdt'})
    add_dir_item('[COLOR FF33B5E5]Pluto TV Spagna[/COLOR]', {'action': 'pluto'})
    add_dir_item('[COLOR FF33B5E5]Plex Spagna[/COLOR]', {'action': 'plex'})
    add_dir_item('[COLOR FF33B5E5]FAST Spagna (sperimentale)[/COLOR]', {'action': 'samsung'})
    # --- On-demand (verde) ---
    add_dir_item('[COLOR FF4CAF50]RTVE on-demand (con sottotitoli)[/COLOR]', {'action': 'vod'})
    xbmcplugin.endOfDirectory(HANDLE)


def show_tdt_groups():
    groups = tdt.get_groups()
    for g in groups:
        add_dir_item(
            g,
            {'action': 'tdt_group', 'group': g},
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_tdt_group(group):
    # Telemadrid (canale nazionale) come PRIMA voce della sezione
    # "C. de Madrid": passa dal resolver perche' lo stream si ottiene a
    # runtime dall'API Galgo (token sempre fresco).
    if group == telemadrid.GROUP:
        for ch in telemadrid.CHANNELS:
            add_video_item(
                ch['name'],
                build_url({'action': 'play_telemadrid', 'cid': ch['id']}),
                icon=ch.get('logo') or None,
                plot='Canale Telemadrid in diretta (stream ufficiale via API '
                     'Galgo). Il nazionale puo\' essere geobloccato fuori '
                     'dalla Spagna.',
                mode='resolver',
            )
    channels = tdt.get_channels_by_group(group)
    for ch in channels:
        add_video_item(
            ch['name'],
            build_url({'action': 'play_tdt', 'name': ch['name'], 'group': group}),
            icon=ch.get('icon') or None,
            fanart=ch.get('fanart') or None,
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_tdt_channels():
    channels = tdt.get_channels()
    for ch in channels:
        add_video_item(
            ch['name'],
            build_url({'action': 'play_tdt', 'name': ch['name'],
                       'group': ch.get('group') or ''}),
            icon=ch.get('icon') or None,
            fanart=ch.get('fanart') or None,
            plot=ch.get('group', ''),
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def play_tdt(name, group):
    """Resolver per i canali TDT: ripesca le sorgenti, prova in ordine quella
    che risponde (scartando feed morti o geobloccati es. HTTP 451) e la passa
    al player. Fallback automatico tra piu' sorgenti."""
    ch = tdt.find_channel(name, group or None)
    sources = (ch.get('sources') if ch else None) or ([])
    if not ch and name:
        # canale non piu' presente nella lista (rimossa a monte)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Canale non piu disponibile nella lista TDT "%s".' % name)
        return
    for src in sources:
        if netutil.probe_url(src):
            play_resolved(src, title=name,
                          mime=ch.get('mime') or netutil.guess_mime(src))
            return
    # nessuna sorgente ha risposto
    xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
    xbmcgui.Dialog().ok(
        ADDON_NAME,
        'Nessuna sorgente disponibile per "%s" (canale spento o geobloccato '
        'fuori dalla Spagna).' % name)


def show_rtve_channels():
    rtve_channels = rtve.get_channel_list()
    for ch in rtve_channels:
        # ogni canale RTVE passa dal resolver (puo' richiedere login)
        add_video_item(
            ch['name'],
            build_url({'action': 'play_rtve', 'cid': ch['id']}),
            icon=ch.get('icon') or None,
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_pluto_groups():
    for g in pluto.get_groups():
        add_dir_item(g, {'action': 'pluto_group', 'group': g})
    xbmcplugin.endOfDirectory(HANDLE)


def show_pluto_group(group):
    for ch in pluto.get_channels_by_group(group):
        add_video_item(
            ch['name'],
            build_url({'action': 'play_pluto', 'cid': ch['id']}),
            icon=ch.get('icon') or None,
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_samsung_channels():
    for ch in samsung.get_channels():
        add_video_item(
            ch['name'],
            samsung.resolve(ch['url']),
            icon=ch.get('icon') or None,
            plot=('Canale FAST gratuito (SPERIMENTALE). Disponibilità variabile '
                  'e pubblicità.'),
            mode='direct',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def show_plex_groups():
    for g in plex.get_groups():
        add_dir_item(g, {'action': 'plex_group', 'group': g})
    xbmcplugin.endOfDirectory(HANDLE)


def show_plex_group(group):
    for ch in plex.get_channels_by_group(group):
        add_video_item(
            ch['name'],
            build_url({'action': 'play_plex', 'key': ch['key']}),
            icon=ch.get('icon') or None,
            plot='Canale FAST gratuito (Plex). Pubblicità.',
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def play_plex(key):
    stream_url = plex.resolve(key)
    if not stream_url:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(ADDON_NAME, 'Impossibile ottenere lo stream Plex.')
        return
    play_resolved(stream_url, mime='application/vnd.apple.mpegurl',
                  headers=plex.headers_string())


def play_telemadrid(cid):
    stream_url, err = telemadrid.resolve(cid or telemadrid.TELEMADRID_ID)
    if not stream_url:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(ADDON_NAME, err or 'Impossibile ottenere lo stream '
                            'Telemadrid.')
        return
    play_resolved(stream_url, mime='application/vnd.apple.mpegurl',
                  headers=telemadrid.headers_string())


def play_pluto(channel_id):
    stream_url = pluto.resolve(channel_id)
    if not stream_url:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(ADDON_NAME, 'Impossibile ottenere lo stream Pluto.')
        return
    play_resolved(stream_url, mime='application/vnd.apple.mpegurl')


def show_vod_programs():
    for prog in rtve_vod.get_programs():
        add_dir_item(prog['name'], {'action': 'vod_eps', 'slug': prog['slug']})
    xbmcplugin.endOfDirectory(HANDLE)


def show_vod_episodes(slug):
    eps = rtve_vod.get_episodes(slug)
    if not eps:
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Nessun episodio disponibile per questo programma '
            '(o errore di rete).',
        )
        xbmcplugin.endOfDirectory(HANDLE)
        return
    for ep in eps:
        add_video_item(
            ep['title'],
            build_url({'action': 'play_vod', 'vid': ep['id']}),
            icon=ep.get('thumb') or None,
            mode='resolver',
        )
    xbmcplugin.endOfDirectory(HANDLE)


def play_vod(video_id):
    stream_url = rtve_vod.resolve_url(video_id)
    subs = rtve_vod.get_subtitles(video_id)
    # RTVE applica hotlink: senza Referer/Origin il CDN risponde 403.
    hdrs = {
        'Referer': 'https://www.rtve.es/',
        'Origin': 'https://www.rtve.es',
        'User-Agent': USER_AGENT,
    }
    play_resolved(stream_url, mime='application/vnd.apple.mpegurl',
                  headers=hdrs, subtitles=subs or None)


def rtve_login():
    email = ADDON.getSetting('rtve_email').strip()
    password = ADDON.getSetting('rtve_password').strip()
    email, password = rtve.get_credentials(email, password)
    if not email or not password:
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Inserisci email e password in Impostazioni > Add-on > '
            'Castellano prima di usare i canali RTVE.',
        )
        return
    result = rtve.login(email, password)
    if result:
        xbmcgui.Dialog().notification(
            ADDON_NAME, 'Accesso RTVE effettuato', xbmcgui.NOTIFICATION_INFO
        )
        xbmc.executebuiltin('Container.Refresh')
    else:
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Login RTVE fallito. Verifica email e password nelle impostazioni.',
        )


def play_rtve(channel_id):
    email = ADDON.getSetting('rtve_email').strip()
    password = ADDON.getSetting('rtve_password').strip()
    email, password = rtve.get_credentials(email, password)
    stream_url = rtve.resolve_stream(channel_id, email, password)
    if not stream_url:
        # nessun resolver ha funzionato: chiudi la directory per evitare errore
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            'Impossibile ottenere lo stream RTVE per questo canale. '
            'I canali RTVE in diretta sono spesso geobloccati fuori dalla '
            'Spagna (HTTP 451): l\'account RTVE non bypassa il blocco del CDN.',
        )
        return
    # RTVE applica hotlink/geoblock: senza Referer/Origin il CDN risponde 403.
    hdrs = {
        'Referer': 'https://www.rtve.es/',
        'Origin': 'https://www.rtve.es',
        'User-Agent': (USER_AGENT),
    }
    play_resolved(stream_url, mime='application/vnd.apple.mpegurl', headers=hdrs)


def router():
    params = dict(
        urllib.parse.parse_qsl(sys.argv[2][1:])
    )
    action = params.get('action')

    if action is None:
        show_main_menu()
    elif action == 'tdt':
        show_tdt_groups()
    elif action == 'tdt_group':
        show_tdt_group(params.get('group'))
    elif action == 'play_tdt':
        play_tdt(params.get('name'), params.get('group'))
    elif action == 'rtve':
        show_rtve_channels()
    elif action == 'vod':
        show_vod_programs()
    elif action == 'pluto':
        show_pluto_groups()
    elif action == 'pluto_group':
        show_pluto_group(params.get('group'))
    elif action == 'play_pluto':
        play_pluto(params.get('cid'))
    elif action == 'play_telemadrid':
        play_telemadrid(params.get('cid'))
    elif action == 'samsung':
        show_samsung_channels()
    elif action == 'plex':
        show_plex_groups()
    elif action == 'plex_group':
        show_plex_group(params.get('group'))
    elif action == 'play_plex':
        play_plex(params.get('key'))
    elif action == 'vod_eps':
        show_vod_episodes(params.get('slug'))
    elif action == 'play_vod':
        play_vod(params.get('vid'))
    elif action == 'rtve_login':
        rtve_login()
    elif action == 'play_rtve':
        play_rtve(params.get('cid'))
    else:
        # azione non valida: chiudi senza generare errori di directory
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        xbmcgui.Dialog().ok(
            ADDON_NAME, 'Azione sconosciuta: %s' % action
        )


if __name__ == '__main__':
    router()