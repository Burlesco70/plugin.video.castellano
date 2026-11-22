# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Burlesco70
# Castellano - TV spagnola. GNU GPL v3 - vedi file LICENSE.
"""
Canali Pluto TV (Spagna) in castigliano.

Pluto TV e' gratuito (con pubblicita'). I canali sono risolti tramite lo
"stitcher" ufficiale di Pluto:
  1. boot.pluto.tv/v4/start  -> restituisce i parametri (stitcherParams) e
     l'host dello stitcher.
  2. Per ogni canale (id) il flusso HLS e':
     https://<stitcher>/stitch/hls/channel/<id>/master.m3u8?<stitcherParams>

Verificato: i canali del catalogo Spagna sono riproducibili (master + varianti
+ segmenti) anche da rete non spagnola. Non serve login.
"""

import urllib.parse
import requests

BOOT_URL = 'https://boot.pluto.tv/v4/start'
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

# Canali del catalogo Spagna (id, nome, logo, gruppo).
PLUTO_CHANNELS = [
    {'id': '67517fae5534bb0008187997', 'name': 'Actualidad 360', 'icon': 'https://i.imgur.com/3YeTu0n.png', 'group': 'Informativos'},
    {'id': '5f1acce7f17797000718f9be', 'name': 'Ana y los 7', 'icon': 'https://i.imgur.com/X5g6gXS.png', 'group': 'Serie'},
    {'id': '6850335b5965a2fd49f7e36d', 'name': 'Andromeda', 'icon': 'https://i.imgur.com/6ot2lmd.png', 'group': 'Serie'},
    {'id': '5f984f4a09e92d0007d74647', 'name': 'Archivos Forenses', 'icon': 'https://i.imgur.com/Pxrl9Ug.png', 'group': 'Documentari'},
    {'id': '5f1aca0b4e448e00075e7c5e', 'name': 'Bob Esponja (720p)', 'icon': 'https://images.pluto.tv/channels/5f1aca0b4e448e00075e7c5e/colorLogoPNG.png', 'group': 'Bambini'},
    {'id': '60ed5fb9c4716d0007d180c5', 'name': 'Cazador de Homicidas', 'icon': 'https://i.imgur.com/hy6FJLe.png', 'group': 'Documentari'},
    {'id': '68de3db35fc0afe85de0b843', 'name': 'Comedia a lo bestia de Pluto TV', 'icon': 'https://images.pluto.tv/channels/68de3db35fc0afe85de0b843/colorLogoPNG_1759402494389.png', 'group': 'Commedia'},
    {'id': '64ddcbb14c5ed80008fad416', 'name': 'Crimen & Historia (720p)', 'icon': 'https://images.pluto.tv/channels/64ddcbb14c5ed80008fad416/colorLogoPNG.png', 'group': 'Documentari'},
    {'id': '5f1acd36779de70007a680d1', 'name': 'Curro Jimenez', 'icon': 'https://i.imgur.com/e3biTY5.png', 'group': 'Serie'},
    {'id': '629a066860ef810008267b70', 'name': 'Detective Conan', 'icon': 'https://images.pluto.tv/channels/629a066860ef810008267b70/solidLogoPNG.png?w=512', 'group': 'Animazione'},
    {'id': '60c343007bcabe0007242aa6', 'name': 'El Comisario', 'icon': 'https://i.imgur.com/XYt8utn.png', 'group': 'Serie'},
    {'id': '60e45687313c5f0007bc8e94', 'name': 'El encantador de perros', 'icon': 'https://i.imgur.com/hYqjQ1n.png', 'group': 'Serie'},
    {'id': '690dd10a37b131228d76d5b1', 'name': 'El Mueble (720p)', 'icon': 'https://provider-static.plex.tv/epg/cms/production/d64983e2-55b1-410b-9599-98a28f7b94ba/Logo_ElMueble_1500x1000_AllWhite_-_Belen_Bruno.png', 'group': 'Lifestyle'},
    {'id': '60218baa464ef900073168c1', 'name': 'Empenos a lo bestia', 'icon': 'https://i.imgur.com/EOttSdW.png', 'group': 'Serie'},
    {'id': '61922be835f3910007fc58f6', 'name': 'En el punto de mira', 'icon': 'https://i.imgur.com/E9grXd9.png', 'group': 'Intrattenimento'},
    {'id': '67517f923a61d40008c451f0', 'name': 'Historia Y Vida (720p)', 'icon': 'https://i.imgur.com/56ZtCA1.png', 'group': 'Documentari'},
    {'id': '5f1acbed25948a0007ffbe65', 'name': 'Los archivos del FBI', 'icon': 'https://i.imgur.com/eDCdJO2.png', 'group': 'Serie'},
    {'id': '5f1aca8310a30e00074fab92', 'name': 'Los Asesinatos de Midsomer', 'icon': 'https://i.imgur.com/JIbupT1.png', 'group': 'Serie'},
    {'id': '6578808014fbe400086e21bc', 'name': 'Medium (Germany)', 'icon': 'https://images.pluto.tv/channels/6578808014fbe400086e21bc/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '60e4573c9f963e00077ecf25', 'name': 'Mi Extrana Obsesion', 'icon': 'https://i.imgur.com/VtxO6KI.png', 'group': 'Serie'},
    {'id': '5f98537a5a4341000733aefe', 'name': 'MTV Embarazada a los 16', 'icon': 'https://images.pluto.tv/channels/5f98537a5a4341000733aefe/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '627d3176d7dfa500077042f1', 'name': 'MTV Geordies', 'icon': 'https://images.pluto.tv/channels/627d3176d7dfa500077042f1/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '62ac3d7dc23b400008ae5b5a', 'name': 'MTV Jerseys', 'icon': 'https://images.pluto.tv/channels/62ac3d7dc23b400008ae5b5a/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '5f1aadf373bed3000794d1d7', 'name': 'MTV Originals', 'icon': 'https://images.pluto.tv/channels/5f1aadf373bed3000794d1d7/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '63eb9495a8b227000841bf64', 'name': 'MTV Verguenza ajena (720p)', 'icon': 'https://images.pluto.tv/channels/63eb9495a8b227000841bf64/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '680ba8992472a7200a183eb5', 'name': 'One Piece Spain', 'icon': 'https://i.imgur.com/XsvbAWR.png', 'group': 'Animazione'},
    {'id': '600ae6a78d801e0007117d21', 'name': 'Pluto TV Animales', 'icon': 'https://images.pluto.tv/channels/600ae6a78d801e0007117d21/colorLogoPNG.png', 'group': 'Documentari'},
    {'id': '645a309c5a0cd5000873f609', 'name': 'Pluto TV Catastrofes', 'icon': 'https://images.pluto.tv/channels/645a309c5a0cd5000873f609/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '5f1ac8099c49f600076579b2', 'name': 'Pluto TV Cine Comedia (Germany)', 'icon': 'https://images.pluto.tv/channels/5f1ac8099c49f600076579b2/colorLogoPNG_1769092378955.png', 'group': 'Cinema'},
    {'id': '60cc807324d60a0007708dc8', 'name': 'Pluto TV Cine de autor', 'icon': 'https://images.pluto.tv/channels/60cc807324d60a0007708dc8/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '5f1ac9a2d3611d0007a844bb', 'name': 'Pluto TV Cine Romantico', 'icon': 'https://images.pluto.tv/channels/5f1ac9a2d3611d0007a844bb/colorLogoPNG_1747044085204.png', 'group': 'Cinema'},
    {'id': '5f1acdaa8ba90f0007d5e760', 'name': 'Pluto TV Cocina', 'icon': 'https://images.pluto.tv/channels/5f1acdaa8ba90f0007d5e760/colorLogoPNG.png', 'group': 'Cooking'},
    {'id': '5f1abce155a03d0007718834', 'name': 'Pluto TV Comedia made in Spain', 'icon': 'https://images.pluto.tv/channels/5f1abce155a03d0007718834/colorLogoPNG.png', 'group': 'Commedia'},
    {'id': '655b5d865812e80008843bd1', 'name': 'Pluto TV Comedias Romanticas', 'icon': 'https://images.pluto.tv/channels/655b5d865812e80008843bd1/colorLogoPNG_1747044085522.png', 'group': 'Commedia'},
    {'id': '64db2e0835425100080f2f5a', 'name': 'Pluto TV Diseno', 'icon': 'https://images.pluto.tv/channels/64db2e0835425100080f2f5a/colorLogoPNG.png', 'group': 'Lifestyle'},
    {'id': '65bd0f53dc10a40008e68b96', 'name': 'Pluto TV Gasolina', 'icon': 'https://images.pluto.tv/channels/65bd0f53dc10a40008e68b96/colorLogoPNG_1747382175081.png', 'group': 'Intrattenimento'},
    {'id': '66b0dfa1d512590008bfa7fd', 'name': 'Pluto TV Gore & Slasher', 'icon': 'https://images.pluto.tv/channels/66b0dfa1d512590008bfa7fd/colorLogoPNG.png', 'group': 'Intrattenimento'},
    {'id': '61cd7b49543066000713b620', 'name': 'Pluto TV Historia (Germany) (720p)', 'icon': 'https://images.pluto.tv/channels/61cd7b49543066000713b620/colorLogoPNG.png', 'group': 'Documentari'},
    {'id': '68adc697116b783a33f99e6c', 'name': 'Pluto TV Impacto', 'icon': 'https://images.pluto.tv/channels/68adc697116b783a33f99e6c/colorLogoPNG_1760448745473.png', 'group': 'Intrattenimento'},
    {'id': '654a35ce346f420008d5c36e', 'name': 'Pluto TV Invasion Alien', 'icon': 'https://images.pluto.tv/channels/654a35ce346f420008d5c36e/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '6475bfec536e0c0008858e9f', 'name': 'Pluto TV K-Drama', 'icon': 'https://images.pluto.tv/channels/6475bfec536e0c0008858e9f/colorLogoPNG.png', 'group': 'Serie'},
    {'id': '609e7e423e9173000706a681', 'name': 'Pluto TV Kids Classics (720p)', 'icon': 'https://images.pluto.tv/channels/609e7e423e9173000706a681/colorLogoPNG_1750147033956.png', 'group': 'Bambini'},
    {'id': '64be745340962900080b55e7', 'name': 'Pluto TV Melrose Place', 'icon': 'https://i.imgur.com/hXDj0fV.png', 'group': 'Altri'},
    {'id': '6080345ebb49b90007ce0baf', 'name': 'Pluto TV Motor (Germany)', 'icon': 'https://images.pluto.tv/channels/6080345ebb49b90007ce0baf/colorLogoPNG.png', 'group': 'Auto'},
    {'id': '65ce480a78df2200131c597b', 'name': 'Pluto TV Psycho', 'icon': 'https://images.pluto.tv/channels/65ce480a78df2200131c597b/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '65cf6ab58145cb0008129ca8', 'name': 'Pluto TV Series criminales', 'icon': 'https://images.pluto.tv/channels/65cf6ab58145cb0008129ca8/colorLogoPNG.png', 'group': 'Serie'},
    {'id': '63eb944dc111bc0008fe7021', 'name': 'Pluto TV Teen (720p)', 'icon': 'https://images.pluto.tv/channels/63eb944dc111bc0008fe7021/colorLogoPNG_1761820520562.png', 'group': 'Bambini'},
    {'id': '662a69daa0a74e00087a1c72', 'name': 'Pluto TV Telenovelas Clasicas', 'icon': 'https://images.pluto.tv/channels/662a69daa0a74e00087a1c72/colorLogoPNG.png', 'group': 'Serie'},
    {'id': '6385e82900ab2e000768a058', 'name': 'Pluto TV Western ES', 'icon': 'https://images.pluto.tv/channels/630dd3b2605f140007e002f5/colorLogoPNG_1732030684562.png', 'group': 'Cinema'},
    {'id': '65786888b228b7000843ad9a', 'name': 'Pluto TV Zombies', 'icon': 'https://images.pluto.tv/channels/65786888b228b7000843ad9a/colorLogoPNG.png', 'group': 'Cinema'},
    {'id': '5e7cb84a172a0f0007da69e4', 'name': 'Red Bull TV ES (1080p)', 'icon': 'https://images.pluto.tv/channels/5e7cb84a172a0f0007da69e4/colorLogoPNG.png', 'group': 'Sport'},
    {'id': '676e7b4a4bd636000819c6a7', 'name': 'SensaCine TV x Pluto', 'icon': 'https://images.pluto.tv/channels/676e7b4a4bd636000819c6a7/colorLogoPNG_1748957675934.png', 'group': 'Cinema'},
    {'id': '604bdf4e6d0abc0007ba77ad', 'name': 'Sin tetas no hay paraiso', 'icon': 'https://i.imgur.com/fpwU2IQ.png', 'group': 'Serie'},
    {'id': '63d7a8e5a9957100086bfc23', 'name': 'South Park Version Original', 'icon': 'https://images.pluto.tv/channels/63d7a8e5a9957100086bfc23/colorLogoPNG.png', 'group': 'Animazione'},
    {'id': '61bb2814ac085a00074309a6', 'name': 'Unidad de investigacion', 'icon': 'https://i.imgur.com/tc3zenG.png', 'group': 'Altri'},
    {'id': '5f28009b150b2500077766b8', 'name': 'Vaya semanita', 'icon': 'https://i.imgur.com/0bCLNUG.png', 'group': 'Commedia'},
]

_PARAMS = None


def get_channel_list():
    return PLUTO_CHANNELS


def get_groups():
    seen = set()
    groups = []
    for ch in PLUTO_CHANNELS:
        g = ch.get('group') or 'Altri'
        if g not in seen:
            seen.add(g)
            groups.append(g)
    return groups


def get_channels_by_group(group):
    return [ch for ch in PLUTO_CHANNELS if (ch.get('group') or 'Altri') == group]


def _boot():
    """Chiama boot.pluto.tv e restituisce (stitcher_host, stitcherParams)."""
    global _PARAMS
    if _PARAMS:
        return _PARAMS
    q = {
        'appName': 'web', 'appVersion': '8.0.0', 'deviceVersion': '120',
        'deviceModel': 'web', 'deviceMake': 'chrome', 'deviceType': 'web',
        'clientModelNumber': '1', 'serverSideAds': 'false',
        'clientID': '11111111-1111-1111-1111-111111111111',
    }
    q['sid'] = q['clientID']
    q['sessionID'] = q['clientID']
    try:
        url = BOOT_URL + '?' + urllib.parse.urlencode(q)
        d = requests.get(url, headers={'User-Agent': USER_AGENT},
                         timeout=20).json()
        stitcher = d.get('servers', {}).get(
            'stitcher',
            'cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv')
        params = d.get('stitcherParams', '')
        _PARAMS = (stitcher, params)
    except Exception:
        _PARAMS = ('cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv',
                   urllib.parse.urlencode(q))
    return _PARAMS


def resolve(channel_id):
    """URL master HLS del canale Pluto.

    Usiamo il redirector pubblico jmp2.uk (quello di iptv-org): genera al volo
    un URL firmato (JWT) colla regione corretta (Spagna) e reindirizza al
    master Pl Pluto. In questo modo la riproduzione funziona anche da rete non
    spagnola, senza dover mintare token dipendenti dalla regione del client
    (che altrimenti davano HTTP 403). ISA segue automaticamente il redirect.
    """
    return 'https://jmp2.uk/plu-%s.m3u8' % channel_id
