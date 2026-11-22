# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""
Canali FAST Spagna (versione SPERIMENTALE, ispirata a Samsung TV Plus).

Sono canali FAST gratuiti (con pubblicita'), disponibili in Spagna e presenti
anche su Samsung TV Plus. Gli URL sono flussi HLS diretti (CDN amagi.tv /
wurl.tv) verificati come raggiungibili (HTTP 200).

NOTA: questa e' una lista ridotta e sperimentale. La lista completa di Samsung
TV Plus (~194 canali) richiede l'API proprietaria di Samsung con token di
sessione: non e' una playlist pubblica. Qui includiamo solo i canali con
flusso diretto verificato, per avere qualcosa che funzioni davvero.
"""

# id, nome, url (HLS diretto), logo, gruppo
SAMSUNG_CHANNELS = [
    {'name': 'The Pet Collective',  'url': 'https://the-pet-collective-international-es.samsung.wurl.tv/playlist.m3u8',
     'icon': 'https://i.imgur.com/yH7n2dF.png', 'group': 'Famiglia'},
    {'name': 'WaterBear',          'url': 'https://amg01415-waterbearnetwor-waterbear-samsunguk-1h0y8.amagi.tv/playlist/amg01415-waterbearnetwor-waterbear-samsunguk/playlist.m3u8',
     'icon': 'https://framerusercontent.com/images/41VQQ7F0fYlp1MX1N4Ixog5QnPI.png', 'group': 'Documentari'},
    {'name': 'NatureTime',         'url': 'https://bamusa-naturetime-emea-eng-rakuten.amagi.tv/playlist.m3u8',
     'icon': 'https://i.imgur.com/72JmyjM.png', 'group': 'Documentari'},
    {'name': 'MyTime Movie Network','url': 'https://appletree-mytimespain-rakuten.amagi.tv/playlist.m3u8',
     'icon': 'https://i.imgur.com/pw4NZK1.png', 'group': 'Cinema'},
    {'name': 'BBC Drama',          'url': 'https://amg00793-amg00793c40-rakuten-es-5444.playouts.now.amagi.tv/playlist.m3u8',
     'icon': 'https://i.imgur.com/HctHhLL.png', 'group': 'Serie'},
    {'name': 'Mr Bean Animated',   'url': 'https://amg00627-amg00627c30-rakuten-es-3990.playouts.now.amagi.tv/playlist/amg00627-banijayfast-mrbeanescc-rakutenes/playlist.m3u8',
     'icon': 'https://static.wikia.nocookie.net/logopedia/images/2/25/Mr._Bean_Animated_Series_stacked_logo.png', 'group': 'Bambini'},
]


def get_channels():
    return SAMSUNG_CHANNELS


def resolve(url):
    """Gli URL sono gia' HLS diretti: ritornano cosi' come sono."""
    return url