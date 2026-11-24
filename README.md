# Castellano - TV spagnola (plugin Kodi)

Plugin Kodi personale per imparare lo spagnolo (castellano) guardando la TV
spagnola. Raccoglie in un unico posto canali in diretta gratuiti e contenuti
on-demand con sottotitoli in spagnolo.

## Cosa include

Il menu principale separa **TV in diretta** (azzurro) da **on-demand** (verde):

- **Canali RTVE in diretta** (azzurro) — La 1, La 2, Teledeporte, 24h, Clan.
- **Canali TDT** (azzurro) — oltre 400 canali spagnoli liberi dalla lista
  [TDT Channels](https://www.tdtchannels.com/lists/tv.m3u8), organizzati per
  categoria (Andalucía, Cataluña, Generalistas, Deportivos, ecc.). I feed
  marcati `GEO` (solo Spagna) vengono scartati automaticamente. Nella sezione
  **C. de Madrid** sono aggiunte in cima le dirette ufficiali di **Telemadrid**
  (nazionale), **LaOtra** e **Telemadrid Internacional** (stream live via API
  Galgo). LaOtra e Internacional sono visibili anche dall'estero; il nazionale
  è geobloccato fuori dalla Spagna.
- **Pluto TV Spagna** (azzurro) — ~56 canali gratuiti (con pubblicità),
  divisi per categoria (Cinema, Serie, Documentari, Bambini...).
- **Plex Spagna** (azzurro) — ~267 canali FAST gratuiti, divisi per categoria
  (Sport, Musica, Serie, Documentari, Notiziari...). Consigliato inserire il
  proprio token Plex gratuito nelle impostazioni per evitare il rate-limit del
  token pubblico condiviso.
- **FAST Spagna (sperimentale)** (azzurro) — canali FAST gratuiti (con
  pubblicità), subset verificato ispirato a Samsung TV Plus. Lista ridotta e
  sperimentale, con disponibilità variabile.
- **RTVE on-demand** (verde) — programmi RTVE (Telediario, documentari, serie)
  con sottotitoli spagnoli funzionanti.

## Requisiti

- **Kodi 20 (Nexus) o superiore** — testato su Kodi 21 "Omega" (Windows).
  Funziona anche su Android TV, Fire TV Stick e LibreELEC/CoreELEC (Kodi 20+).
- Due add-on dipendenza (di norma Kodi li scarica in automatico al primo avvio):
  - `inputstream.adaptive` — per la riproduzione dei flussi HLS/DASH.
  - `script.module.requests` — per scaricare le liste.

Se Kodi NON installa da solo le dipendenze (a volte su build "leggere" o offline):
1. `inputstream.adaptive`: Add-on → Cerca / repository ufficiale Kodi → installa.
2. `script.module.requests`: Add-on → Cerca → installa (spesso incluso di default).
3. Riavvia Kodi e riprova ad aprire il plugin.

## Installazione

### Da Release GitHub (consigliato)

1. Vai nella pagina **Releases** del repository e scarica l'ultimo
   `plugin.video.castellano-<versione>.zip`.
2. In Kodi: **Add-on → Installa da file ZIP** e seleziona lo zip.
   (Su alcune skin: **Sistema → Impostazioni → Add-on → Installa da file ZIP**;
   se non vedi la voce, abilita prima "Origini sconosciute" in
   Impostazioni → Add-on.)
3. Attendi la conferma di installazione.
4. (Opzionale) **Add-on → Castellano → Configura** per eventuali credenziali
   RTVE (non necessarie per i canali in diretta, vedi sotto).

### Build locale dello zip

Se preferisci generare lo zip in locale:

```
python build.py
```

Lo zip viene creato in `plugin/plugin.video.castellano-<versione>.zip`
(la versione è letta da `addon.xml`).

## Aggiornamento

- Ripeti la procedura di installazione con lo zip della nuova versione: Kodi
  lo aggiorna mantenendo le tue impostazioni.
- In alternativa: Add-on → Castellano → tasto destro → "Verifica aggiornamenti"
  (se stai usando un repository sorgente configurato).

## Disinstallazione

- **Add-on → Castellano** → tasto destro → **Disinstalla**.
- Eventuali impostazioni restano finché non rimuovi anche i dati utente in
  `userdata/addon_data/plugin.video.castellano/`.

## Risoluzione problemi

- **Un canale non parte**: alcuni contenuti sono geobloccati (solo Spagna) o
  protetti da DRM e non sono riproducibili con Kodi base. Prova un altro canale.
- **Sottotitoli VOD sfasati**: si regolano al volo con "Ritardo sottotitoli" di
  Kodi durante la riproduzione.
- **Lista vuota / errore di rete**: verifica la connessione e che
  `script.module.requests` sia installato.
- **Log per diagnosi**: Impostazioni → Sistema → Logging → attiva "Debug",
  riproduci il problema e controlla `kodi.log`.

## Credenziali RTVE

NON sono necessarie per i canali in diretta: le dirette RTVE sono pubbliche e
funzionano senza login. I campi email/password nelle impostazioni sono lasciati
solo per eventuali contenuti futuri che richiedano l'accesso.

## Token Plex

I canali **Plex Spagna** funzionano anche senza token (usando un token pubblico
condiviso), ma quel token è spesso soggetto a rate-limit (HTTP 429) e alcuni
canali non partono. Per la massima stabilità conviene inserire il proprio token
Plex gratuito:

1. Crea/accedi a un account su [plex.tv](https://plex.tv) (gratis).
2. Ottieni il token: apri `https://plex.tv/users/sign_in` con le tue credenziali
   e copia il valore `<authToken>` (token account, stabile), oppure leggi
   l'header `X-Plex-Token` dalle richieste di rete (F12) su `app.plex.tv`.
3. In Kodi: Add-on → Castellano → Configura → campo "Token Plex".

Il token è salvato solo nelle tue impostazioni Kodi (non nello zip).

## Note tecniche e limiti

- **Geoblock**: alcuni contenuti spagnoli sono visibili solo da rete spagnola.
  I canali live RTVE e Pluto risolvono gli stream con gli header corretti e
  risultano riproducibili anche dall'estero; altri potrebbero non partire.
- **DRM**: i contenuti protetti (FairPlay/Widevine) non sono riproducibili con
  Kodi base.
- **Sottotitoli VOD**: sono file `.vtt` esterni. Se risultano sfasati, si
  regolano al volo con "Ritardo sottotitoli" di Kodi durante la riproduzione
  (nessun offset predefinito: ognuno si regola come preferisce).
- **Endpoint**: i servizi (RTVE, Pluto, TDT Channels) cambiano periodicamente.
  La risoluzione è isolata in `resources/lib/` e commentata per facilitare la
  manutenzione.

## Struttura

```
plugin.video.castellano/
├── addon.xml
├── default.py                 # menu e routing
├── icon.png, fanart.jpg
└── resources/
    ├── settings.xml           # impostazioni (email/password RTVE, URL TDT)
    ├── language/              # stringhe it/en
    └── lib/
        ├── tdt.py             # lista TDT Channels + filtro GEO
        ├── rtve.py            # canali RTVE in diretta
        ├── rtve_vod.py        # RTVE on-demand + sottotitoli
        ├── pluto.py           # canali Pluto TV Spagna
        ├── plex.py            # canali Plex Spagna (token + categorie)
        ├── samsung.py         # canali FAST Spagna (sperimentale)
        └── telemadrid.py      # dirette Telemadrid/LaOtra/Internacional (API Galgo)
```

## Uso personale / Disclaimer

Progetto personale a scopo didattico (apprendimento dello spagnolo).
Gli stream appartengono ai rispettivi titolari (RTVE, Pluto TV, TDT Channels).
Rispetta i termini di servizio e le condizioni d'uso di ciascun fornitore e le
norme sul copyright del tuo paese.

## Licenza

GPL-3.0-only (GNU General Public License v3). Vedi il file `LICENSE`.