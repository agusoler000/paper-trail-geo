# -*- coding: utf-8 -*-
"""Subida programada a YouTube del video diario. Contrato: radar/CONTRATO.md. Formato: videos/DAILY/DIARIO.md 5.2.

EL TOPE DE 10 MB DEL ASISTENTE NO APLICA ACA. Ese limite es de lo que el asistente puede mover por el chat
(`project-subida-limite-10mb`); este modulo corre en el VPS y habla directo con la API de YouTube, asi que un
episodio de 20 min a 1080p (~400 MB) sube sin problema. Es exactamente lo que hace que el diario no dependa
de que Agustin suba nada a mano.

Tres decisiones hacen que la subida sea desatendida:

1. SUBIDA RESUMIBLE. MediaFileUpload(resumable=True) en trozos de 8 MB. Cada trozo que llega queda del lado
   de Google: si la red se corta al 70 %, next_chunk() retoma desde ahi y no desde cero. Sin esto, 400 MB no
   sobreviven una noche mala. Ante 429 y 500/502/503/504 (y cortes de socket) reintenta con espera creciente
   2, 4, 8, 16, 32, 60 s mas jitter.
2. PROGRAMACION DEL LADO DE YOUTUBE. Se sube con status.privacyStatus='private' y status.publishAt en ISO
   8601 UTC. YouTube lo publica a esa hora SIN QUE CORRA NADA NUESTRO: el video puede terminar a las 08:30 y
   hacerse publico a las 12:00 con el VPS apagado. Por eso el diario no depende de que nadie este despierto.
3. OAUTH UNA SOLA VEZ. `python videos/DAILY/subir.py --autorizar` abre el consentimiento en el navegador y
   deja el refresh token en radar/_yt_token.json. Despues renueva solo y no vuelve a preguntar nada, salvo
   que se revoque el permiso.
   TRAMPA A EVITAR: si la app de Google Cloud queda en estado de publicacion "Testing", Google vence el
   refresh token A LOS 7 DIAS y el diario se corta un miercoles sin aviso. La pantalla de consentimiento
   tiene que estar "In production" (con la app en modo externo alcanza; no hace falta verificacion de
   Google mientras los scopes sean solo los de YouTube y el unico usuario sea el dueno del canal).

Dependencias: googleapiclient, google.auth, google.oauth2, requests (todas ya instaladas). El consentimiento
va con stdlib a proposito: google_auth_oauthlib NO esta instalado en este entorno y no se agrega una
dependencia entera por una pantalla que se usa una sola vez en la vida del canal.

Cuota diaria de la API: 10.000 unidades. videos.insert 1600 + thumbnails.set 50 + playlistItems.insert 50
= 1700 por corrida completa, o sea 5 subidas enteras por dia. Ver cuota_estimada().

  python videos/DAILY/subir.py --autorizar    # una sola vez; necesita radar/_yt_client.json
  python videos/DAILY/subir.py --autotest     # no sube nada ni necesita credenciales
"""
import argparse, http.client, json, os, random, socket, sys, time
import urllib.parse, urllib.request, webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
TOKEN = os.path.join(RAIZ, 'radar', '_yt_token.json')      # refresh token, lo escribe --autorizar
CLIENTE = os.path.join(RAIZ, 'radar', '_yt_client.json')   # cliente OAuth "App de escritorio" de Google Cloud

# youtube.upload sube y pone miniatura; youtube hace falta para playlistItems.insert.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
AUTH_URI, TOKEN_URI = 'https://accounts.google.com/o/oauth2/v2/auth', 'https://oauth2.googleapis.com/token'

CATEGORIA = '25'          # News & Politics
IDIOMA = 'en'             # el canal es en ingles (canal/CANAL.md)
CHUNK = 8 * 1024 * 1024   # 8 MB: pocos viajes de ida y vuelta, y un corte pierde 8 MB, no 400
REINTENTABLES = (429, 500, 502, 503, 504)
MAX_INTENTOS = 6
ESPERA_BASE, ESPERA_TOPE = 2.0, 60.0
MAX_TITULO, MAX_DESCRIPCION, MAX_ETIQUETAS = 100, 5000, 30
# YouTube no limita la CANTIDAD de etiquetas sino el LARGO TOTAL: 500 caracteres contando las comas que
# las separan. 30 etiquetas de tema ("global economy briefing") son 799 caracteres: videos.insert
# devuelve 400 invalidTags y se pierde la subida entera. Por eso el tope que manda es este, no el de 30.
MAX_ETIQUETAS_CHARS = 500
MAX_MINIATURA = 2 * 1024 * 1024                            # limite duro de thumbnails.set
LIMITE_DIARIO = 10000
COSTO_INSERT, COSTO_MINIATURA, COSTO_LISTA = 1600, 50, 50
# httplib2 tira sus propios errores de transporte; si no esta instalado, no pasa nada.
try:
    import httplib2
    _ERR_HTTPLIB2 = (httplib2.HttpLib2Error,)
except Exception:
    _ERR_HTTPLIB2 = ()
ERRORES_RED = (OSError, http.client.HTTPException) + _ERR_HTTPLIB2


class FaltaToken(RuntimeError):
    """No hay credenciales utilizables. Se levanta ANTES de tocar el video, nunca a mitad de la subida."""


def _log(msg):
    print('[subir] %s' % msg, flush=True)


_dormir = time.sleep   # indirecto a proposito: el autotest lo reemplaza y no espera de verdad


# ---------------------------------------------------------------- tiempo
def _iso_utc(dt):
    """datetime aware -> '2026-09-11T12:00:00Z'. Exige tz: un naive interpretado mal publica el video tres
       horas antes o despues, y de eso nadie se entera hasta que el video ya salio."""
    if not isinstance(dt, datetime):
        raise ValueError('publicar_en tiene que ser datetime, llego %s' % type(dt).__name__)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError('publicar_en tiene que ser aware (tzinfo=timezone.utc), llego naive: %s' % dt)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


# ---------------------------------------------------------------- reintentos
def _codigo(e):
    """Codigo HTTP de un error de googleapiclient, sin atarse a una version de la libreria."""
    for v in (getattr(getattr(e, 'resp', None), 'status', None), getattr(e, 'status_code', None)):
        try:
            if v is not None:
                return int(v)
        except (TypeError, ValueError):
            pass
    return None


def _reintentable(e):
    if isinstance(e, HttpError):
        return _codigo(e) in REINTENTABLES
    return isinstance(e, ERRORES_RED)


def _espera(intento):
    """Creciente con jitter: 2, 4, 8, 16, 32, 60 (+0..1). El jitter evita que dos reintentos vuelvan a
       chocar en el mismo segundo."""
    return min(ESPERA_TOPE, ESPERA_BASE * (2 ** intento)) + random.random()


def _motivo(e):
    c = _codigo(e)
    return '%s %s' % (type(e).__name__, c) if c else type(e).__name__


def _detalle(e):
    """Motivo MAS el texto del error, recortado. Un 'HttpError 400' repetido todos los dias no dice si la
       miniatura pesa de mas, si la lista no existe o si se acabo la cuota; con el texto si."""
    try:
        txt = ' '.join(str(e).split())
    except Exception:
        txt = ''
    return '%s: %s' % (_motivo(e), txt[:200]) if txt else _motivo(e)


def _ejecutar(hacer, etiqueta, intentos=MAX_INTENTOS):
    """Corre hacer() reintentando ante 429/5xx y cortes de red. Lo demas (401, 403 de cuota, 400 por un
       publishAt invalido) sube tal cual: reintentar un error de permisos solo pierde tiempo."""
    for i in range(intentos):
        try:
            return hacer()
        except Exception as e:
            if i == intentos - 1 or not _reintentable(e):
                raise
            t = _espera(i)
            _log('%s fallo (%s); reintento %d/%d en %.1f s' % (etiqueta, _motivo(e), i + 1, intentos - 1, t))
            _dormir(t)


def _recortar_etiquetas(etiquetas):
    """Limpia, aplica los DOS topes (30 etiquetas y 500 caracteres en total) y avisa si algo quedo afuera.
       Recortar en silencio es peor que no recortar: la etiqueta que importa se cae y nadie se entera."""
    limpias = [str(e).strip() for e in (etiquetas or []) if str(e).strip()]
    salen, usado = [], 0
    for e in limpias[:MAX_ETIQUETAS]:
        # una etiqueta con coma la cuenta YouTube entre comillas: dos caracteres mas
        costo = len(e) + (2 if ',' in e else 0) + (1 if salen else 0)
        if usado + costo > MAX_ETIQUETAS_CHARS:
            break
        salen.append(e)
        usado += costo
    if len(salen) != len(limpias):
        _log('AVISO: de %d etiquetas entran %d (topes de YouTube: %d etiquetas, %d caracteres en total). '
             'Quedaron afuera: %s' % (len(limpias), len(salen), MAX_ETIQUETAS, MAX_ETIQUETAS_CHARS,
                                      ', '.join(limpias[len(salen):])[:120]))
    return salen


def _subir_resumible(peticion, etiqueta='videos.insert'):
    """Bombea la subida trozo a trozo. Cada next_chunk() se reintenta por separado y la peticion se acuerda
       de cuanto lleva subido, asi que el reintento no repite los megas que ya llegaron."""
    respuesta, visto = None, -1
    while respuesta is None:
        estado, respuesta = _ejecutar(peticion.next_chunk, etiqueta)
        if estado is not None:
            pct = int(estado.progress() * 100)
            if pct >= visto + 10:
                visto = pct
                _log('%s %d%%' % (etiqueta, pct))
    return respuesta


# ---------------------------------------------------------------- credenciales
def cargar_credenciales(path=None):
    """Lee radar/_yt_token.json y renueva el access token si vencio. El autotest la reemplaza."""
    path = path or TOKEN
    if not os.path.isfile(path):
        raise FaltaToken(
            'no hay token de YouTube en %s.\n'
            'Corre UNA sola vez:  python videos/DAILY/subir.py --autorizar\n'
            '(antes hay que dejar el cliente OAuth de tipo "App de escritorio" en %s, o exportar '
            'YT_CLIENT_ID / YT_CLIENT_SECRET).' % (path, CLIENTE))
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    try:
        creds = Credentials.from_authorized_user_file(path, SCOPES)
    except Exception as e:
        raise FaltaToken('el token %s no se pudo leer (%s). Volve a correr --autorizar.' % (path, e))
    if not creds.refresh_token:
        raise FaltaToken('el token %s no trae refresh_token: sin el no se renueva solo. '
                         'Volve a correr --autorizar.' % path)
    if not creds.valid:
        creds.refresh(Request())
        _volcar_token(json.loads(creds.to_json()), path)
        _log('access token renovado')
    return creds


def construir_servicio(creds):
    """Cliente de la API de YouTube. El autotest la reemplaza."""
    from googleapiclient.discovery import build
    return build('youtube', 'v3', credentials=creds, cache_discovery=False)


MEDIA = MediaFileUpload   # indirecto a proposito: el autotest lo reemplaza


def _volcar_token(datos, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=1)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)   # en Windows casi no hace nada, en el VPS si
    except OSError:
        pass


# ---------------------------------------------------------------- la subida
def subir(video, miniatura, titulo, descripcion, etiquetas, publicar_en, lista=None):
    """Sube `video` como privado y programado para `publicar_en` (datetime AWARE). Devuelve video_id.

    Resumible en trozos de 8 MB con reintentos. La miniatura y la lista son accesorias: si fallan se avisa
    y se devuelve igual el video_id, porque el video ya esta arriba y programado y perderlo por un jpg de
    300 KB seria absurdo."""
    if not titulo or not titulo.strip():
        raise ValueError('titulo vacio')
    if not os.path.isfile(video):
        raise FileNotFoundError('no existe el video: %s' % video)
    if os.path.getsize(video) == 0:
        raise ValueError('el video esta vacio: %s' % video)
    if miniatura and not os.path.isfile(miniatura):
        raise FileNotFoundError('no existe la miniatura: %s' % miniatura)
    cuando = _iso_utc(publicar_en)
    if publicar_en.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise ValueError('publicar_en ya paso (%s): YouTube rechaza publishAt en el pasado' % cuando)

    titulo = titulo.strip()
    if len(titulo) > MAX_TITULO:
        _log('AVISO: titulo de %d caracteres, se recorta a %d' % (len(titulo), MAX_TITULO))
        titulo = titulo[:MAX_TITULO]
    descripcion = descripcion or ''
    if len(descripcion) > MAX_DESCRIPCION:
        _log('AVISO: descripcion de %d caracteres, se recorta a %d (se pierde el final)'
             % (len(descripcion), MAX_DESCRIPCION))
        descripcion = descripcion[:MAX_DESCRIPCION]
    etiquetas = _recortar_etiquetas(etiquetas)

    # El token se pide ACA, antes de abrir el archivo de 400 MB: si falta, el error llega en un segundo.
    creds = cargar_credenciales()
    servicio = construir_servicio(creds)

    cuerpo = {
        'snippet': {'title': titulo, 'description': descripcion, 'tags': etiquetas,
                    'categoryId': CATEGORIA, 'defaultLanguage': IDIOMA, 'defaultAudioLanguage': IDIOMA},
        # private + publishAt = YouTube lo publica solo a esa hora, sin nada corriendo de este lado
        'status': {'privacyStatus': 'private', 'publishAt': cuando,
                   'selfDeclaredMadeForKids': False, 'license': 'youtube', 'embeddable': True},
    }
    _log('subiendo %s (%.1f MB), publica %s' % (os.path.basename(video), os.path.getsize(video) / 1e6, cuando))
    media = MEDIA(video, chunksize=CHUNK, resumable=True, mimetype='video/*')
    peticion = servicio.videos().insert(part='snippet,status', body=cuerpo, media_body=media)
    respuesta = _subir_resumible(peticion) or {}
    vid = respuesta.get('id')
    if not vid:
        raise RuntimeError('YouTube no devolvio id de video: %r' % (respuesta,))
    _log('subido %s, programado para %s' % (vid, cuando))
    # Todo el diseno se apoya en que YouTube publique solo. Si la respuesta no devuelve la programacion,
    # el video queda privado para siempre y nadie se entera hasta que alguien mira el canal.
    eco = respuesta.get('status') or {}
    if eco and (eco.get('privacyStatus') != 'private' or not eco.get('publishAt')):
        _log('AVISO: YouTube devolvio privacyStatus=%r publishAt=%r, o sea que NO quedo programado. '
             'Hay que publicarlo a mano en Studio antes de %s.'
             % (eco.get('privacyStatus'), eco.get('publishAt'), cuando))

    if miniatura:
        try:
            if os.path.getsize(miniatura) > MAX_MINIATURA:
                raise ValueError('la miniatura pesa mas de 2 MB y YouTube la rechaza')
            _ejecutar(lambda: servicio.thumbnails().set(
                videoId=vid, media_body=MEDIA(miniatura, mimetype='image/jpeg', resumable=False)).execute(),
                'thumbnails.set')
            _log('miniatura puesta')
        except Exception as e:
            _log('AVISO: la miniatura fallo (%s). El video YA esta subido y programado.' % _detalle(e))

    if lista:
        try:
            _ejecutar(lambda: servicio.playlistItems().insert(part='snippet', body={'snippet': {
                'playlistId': lista, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}}).execute(),
                'playlistItems.insert')
            _log('agregado a la lista %s' % lista)
        except Exception as e:
            _log('AVISO: no se pudo agregar a la lista %s (%s). El video YA esta subido.' % (lista, _detalle(e)))
    return vid


def cuota_estimada(con_miniatura=True, con_lista=True):
    """Unidades de cuota que consume una corrida completa: 1600 el insert, 50 la miniatura, 50 la lista
       = 1700 sobre las 10.000 diarias, o sea 5 corridas enteras por dia (DIARIO.md 5.2)."""
    return COSTO_INSERT + (COSTO_MINIATURA if con_miniatura else 0) + (COSTO_LISTA if con_lista else 0)


# ---------------------------------------------------------------- OAuth, una sola vez
class _Callback(BaseHTTPRequestHandler):
    """Recibe el redirect de Google en 127.0.0.1. Se usa una vez y se apaga."""
    codigo = error = estado = None

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _Callback.codigo = (q.get('code') or [None])[0]
        _Callback.error = (q.get('error') or [None])[0]
        _Callback.estado = (q.get('state') or [None])[0]
        cuerpo = ('<html><body style="font-family:sans-serif;padding:3em">'
                  '<h2>%s</h2><p>Ya podes cerrar esta pestana y volver a la terminal.</p>'
                  '</body></html>' % ('Listo, YouTube autorizado.' if _Callback.codigo
                                      else 'Fallo: %s' % _Callback.error)).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


def _leer_cliente(path=None):
    path = path or CLIENTE
    cid, csec = os.environ.get('YT_CLIENT_ID'), os.environ.get('YT_CLIENT_SECRET')
    if cid and csec:
        return cid, csec
    if not os.path.isfile(path):
        raise FaltaToken('falta el cliente OAuth en %s. En Google Cloud Console: activar YouTube Data API v3, '
                         'credenciales -> ID de cliente OAuth -> tipo "App de escritorio", bajar el JSON y '
                         'dejarlo ahi. O exportar YT_CLIENT_ID / YT_CLIENT_SECRET.' % path)
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    d = d.get('installed') or d.get('web') or d
    if not d.get('client_id') or not d.get('client_secret'):
        raise FaltaToken('%s no tiene client_id/client_secret' % path)
    return d['client_id'], d['client_secret']


def autorizar(token=None, cliente=None, puerto=0):
    """Consentimiento en el navegador, UNA vez. Guarda el refresh token y no vuelve a pedir nada.
       Con stdlib porque google_auth_oauthlib no esta instalado y no vale una dependencia por esto."""
    token, cliente = token or TOKEN, cliente or CLIENTE
    cid, csec = _leer_cliente(cliente)
    estado = '%032x' % random.getrandbits(128)
    srv = HTTPServer(('127.0.0.1', puerto), _Callback)
    redirect = 'http://127.0.0.1:%d/' % srv.server_port
    url = AUTH_URI + '?' + urllib.parse.urlencode({
        'client_id': cid, 'redirect_uri': redirect, 'response_type': 'code',
        'scope': ' '.join(SCOPES), 'access_type': 'offline', 'prompt': 'consent',
        'include_granted_scopes': 'true', 'state': estado})
    print('Abri esto en el navegador (si no se abrio solo):\n\n%s\n' % url)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    srv.timeout = 300
    _Callback.codigo = _Callback.error = _Callback.estado = None
    try:
        srv.handle_request()
    finally:
        srv.server_close()   # si handle_request se corta, el puerto no queda tomado
    if _Callback.error or not _Callback.codigo:
        raise RuntimeError('Google no devolvio codigo: %s' % (_Callback.error or 'sin respuesta'))
    if _Callback.estado != estado:
        raise RuntimeError('el state no coincide: ese redirect no salio de esta corrida')
    datos = urllib.parse.urlencode({'code': _Callback.codigo, 'client_id': cid, 'client_secret': csec,
                                    'redirect_uri': redirect, 'grant_type': 'authorization_code'}).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URI, datos), timeout=60) as r:
        tok = json.load(r)
    if not tok.get('refresh_token'):
        raise RuntimeError('Google no devolvio refresh_token. Sacale el acceso a la app en '
                           'myaccount.google.com/permissions y volve a correr --autorizar.')
    _volcar_token({'token': tok.get('access_token'), 'refresh_token': tok['refresh_token'],
                   'token_uri': TOKEN_URI, 'client_id': cid, 'client_secret': csec,
                   'scopes': SCOPES, 'universe_domain': 'googleapis.com'}, token)
    print('Listo. Refresh token guardado en %s. No hace falta volver a hacer esto.' % token)
    return token


# ---------------------------------------------------------------- dobles para el autotest
def _error_http(codigo):
    class _R(dict):
        def __init__(s):
            dict.__init__(s, status=codigo, reason='prueba')
            s.status, s.reason = codigo, 'prueba'
    return HttpError(_R(), b'{"error": {"message": "prueba"}}')


class _MediaFalsa:
    def __init__(self, path, chunksize=None, resumable=False, mimetype=None):
        self.path, self.chunksize, self.resumable, self.mimetype = path, chunksize, resumable, mimetype


class _EstadoFalso:
    def __init__(self, p):
        self.p = p

    def progress(self):
        return self.p


class _PeticionFalsa:
    """Imita videos().insert(): sirve `fallos` errores 503 y despues entrega el id en `trozos` pasos.
       Devuelve el eco de `status`, como hace la API real cuando part incluye 'status'."""
    def __init__(self, reg, fallos=0, trozos=1, eco=None):
        self.reg, self.fallos, self.trozos, self.n, self.eco = reg, fallos, trozos, 0, eco

    def next_chunk(self):
        if self.fallos > 0:
            self.fallos -= 1
            self.reg['fallos_servidos'] += 1
            raise _error_http(503)
        self.n += 1
        if self.n < self.trozos:
            return (_EstadoFalso(self.n / float(self.trozos)), None)
        return (None, {'id': 'VIDEO_FALSO', 'status': self.eco})


class _SubFalso:
    def __init__(self, reg, clave, fallos=0):
        self.reg, self.clave, self.fallos = reg, clave, fallos

    def set(self, **kw):
        self.reg[self.clave].append(kw)
        return self

    def insert(self, **kw):
        self.reg[self.clave].append(kw)
        return self

    def execute(self):
        if self.fallos > 0:
            self.fallos -= 1
            self.reg['fallos_servidos'] += 1
            raise _error_http(503)
        return {'id': 'OK'}


class _VideosFalso:
    def __init__(self, reg, fallos=0, trozos=1, sin_programar=False):
        self.reg, self.fallos, self.trozos, self.sp = reg, fallos, trozos, sin_programar

    def insert(self, part=None, body=None, media_body=None):
        self.reg['inserts'].append({'part': part, 'body': body, 'media': media_body})
        eco = dict((body or {}).get('status') or {})
        if self.sp:   # YouTube acepto el video pero se comio la programacion
            eco = {'privacyStatus': 'private', 'publishAt': None}
        return _PeticionFalsa(self.reg, self.fallos, self.trozos, eco)


class _ServicioFalso:
    def __init__(self, reg, fallos_insert=0, trozos=1, fallos_miniatura=0, fallos_lista=0,
                 sin_programar=False):
        self.reg, self.fi, self.tr = reg, fallos_insert, trozos
        self.fm, self.fl, self.sp = fallos_miniatura, fallos_lista, sin_programar

    def videos(self):
        return _VideosFalso(self.reg, self.fi, self.tr, self.sp)

    def thumbnails(self):
        return _SubFalso(self.reg, 'miniaturas', self.fm)

    def playlistItems(self):
        return _SubFalso(self.reg, 'listas', self.fl)


def _autotest():
    """No sube nada ni necesita credenciales: reemplaza el cliente de Google por uno falso."""
    global MEDIA, cargar_credenciales, construir_servicio, _dormir, _log
    import tempfile
    cuenta = {'total': 0}
    fallas = []

    def chequear(nombre, cond, detalle=''):
        cuenta['total'] += 1
        if cond:
            print('OK    %s' % nombre)
        else:
            fallas.append(nombre)
            print('FALLA %s%s' % (nombre, (' -- %s' % (detalle,)) if detalle != '' else ''))

    import shutil
    tmp = tempfile.mkdtemp(prefix='subir_')
    vid_path = os.path.join(tmp, 'diario.mp4')
    with open(vid_path, 'wb') as f:
        f.write(b'\x00' * 4096)
    mini_path = os.path.join(tmp, 'mini.jpg')
    with open(mini_path, 'wb') as f:
        f.write(b'\xff\xd8' + b'\x00' * 1024)
    cuando = datetime(2099, 9, 11, 12, 0, 0, tzinfo=timezone.utc)

    reg = {}

    def limpiar():
        reg.clear()
        reg.update({'inserts': [], 'miniaturas': [], 'listas': [], 'esperas': [], 'fallos_servidos': 0,
                    'avisos': []})
    limpiar()

    log_real = _log
    MEDIA = _MediaFalsa
    _dormir = lambda s: reg['esperas'].append(s)
    _log = lambda m: reg['avisos'].append(m)   # capturados: un tope que no avisa es un bug, y se prueba

    def hay_aviso(txt):
        return any(txt in a for a in reg['avisos'])
    servicio = {'obj': None}
    cargar_credenciales = lambda path=None: 'creds-falsas'
    construir_servicio = lambda creds: servicio['obj']

    # ---- 1. cuota
    chequear('cuota_estimada() = 1700', cuota_estimada() == 1700, cuota_estimada())
    chequear('cuota sin miniatura ni lista = 1600', cuota_estimada(False, False) == 1600)
    chequear('1700 entra 5 veces en las 10.000 del dia', LIMITE_DIARIO // cuota_estimada() == 5)

    # ---- 2. el body del insert
    servicio['obj'] = _ServicioFalso(reg, trozos=3)
    vid = subir(vid_path, None, 'Titulo del dia', 'Descripcion', ['geopolitics', 'daily'], cuando)
    cuerpo = reg['inserts'][0]['body'] if reg['inserts'] else {}
    est = cuerpo.get('status', {})
    chequear('devuelve el video_id', vid == 'VIDEO_FALSO', vid)
    chequear("privacyStatus = 'private'", est.get('privacyStatus') == 'private', est.get('privacyStatus'))
    chequear('publishAt en ISO 8601 UTC', est.get('publishAt') == '2099-09-11T12:00:00Z', est.get('publishAt'))
    chequear("part = 'snippet,status'", reg['inserts'][0]['part'] == 'snippet,status')
    chequear('tags y categoria de noticias',
             cuerpo.get('snippet', {}).get('tags') == ['geopolitics', 'daily']
             and cuerpo.get('snippet', {}).get('categoryId') == CATEGORIA)
    med = reg['inserts'][0]['media']
    chequear('media resumible en trozos de 8 MB', med.resumable is True and med.chunksize == CHUNK,
             '%s / %s' % (med.resumable, med.chunksize))
    chequear('sin miniatura no llama a thumbnails.set', reg['miniaturas'] == [])
    chequear('sin lista no llama a playlistItems', reg['listas'] == [])

    chequear('no inventa un AVISO de programacion cuando YouTube la confirmo',
             not hay_aviso('NO quedo programado'), reg['avisos'])

    # ---- 2b. YouTube se comio el publishAt: el video queda privado para siempre, hay que gritarlo
    limpiar()
    servicio['obj'] = _ServicioFalso(reg, sin_programar=True)
    vid = subir(vid_path, None, 'T', 'D', [], cuando)
    chequear('avisa si YouTube NO devolvio el video programado',
             vid == 'VIDEO_FALSO' and hay_aviso('NO quedo programado'), reg['avisos'])

    # ---- 3. publishAt convertido desde otro huso
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    huso = timezone(timedelta(hours=-3))
    subir(vid_path, None, 'T', 'D', [], datetime(2099, 9, 11, 9, 0, 0, tzinfo=huso))
    chequear('convierte -03:00 a UTC',
             reg['inserts'][0]['body']['status']['publishAt'] == '2099-09-11T12:00:00Z',
             reg['inserts'][0]['body']['status']['publishAt'])

    # ---- 4. reintento ante 503
    limpiar()
    servicio['obj'] = _ServicioFalso(reg, fallos_insert=3, trozos=2)
    vid = subir(vid_path, None, 'T', 'D', [], cuando)
    chequear('sobrevive a 3 errores 503', vid == 'VIDEO_FALSO' and reg['fallos_servidos'] == 3,
             '%s / %d' % (vid, reg['fallos_servidos']))
    chequear('espero 3 veces', len(reg['esperas']) == 3, reg['esperas'])
    chequear('la espera es creciente', reg['esperas'] == sorted(reg['esperas']) and reg['esperas'][0] >= 2.0,
             reg['esperas'])
    chequear('un solo insert: la peticion resume, no reempieza', len(reg['inserts']) == 1, len(reg['inserts']))

    # ---- 5. que se reintenta y que no
    limpiar()
    chequear('403 no es reintentable', not _reintentable(_error_http(403)))
    chequear('429 si es reintentable', _reintentable(_error_http(429)))
    chequear('503 si es reintentable', _reintentable(_error_http(503)))
    chequear('corte de socket es reintentable', _reintentable(socket.timeout('timeout')))
    try:
        _ejecutar(lambda: (_ for _ in ()).throw(_error_http(403)), 'prueba')
        chequear('403 sube tal cual, sin esperar', False, 'no levanto')
    except HttpError:
        chequear('403 sube tal cual, sin esperar', len(reg['esperas']) == 0, reg['esperas'])

    # ---- 6. reintentos agotados
    limpiar()
    servicio['obj'] = _ServicioFalso(reg, fallos_insert=MAX_INTENTOS + 2)
    try:
        subir(vid_path, None, 'T', 'D', [], cuando)
        chequear('al agotar reintentos levanta', False, 'no levanto')
    except HttpError:
        chequear('al agotar reintentos levanta', len(reg['esperas']) == MAX_INTENTOS - 1, reg['esperas'])

    # ---- 7. miniatura y lista
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    subir(vid_path, mini_path, 'T', 'D', [], cuando, lista='PL_FALSA')
    chequear('pone la miniatura',
             len(reg['miniaturas']) == 1 and reg['miniaturas'][0]['videoId'] == 'VIDEO_FALSO', reg['miniaturas'])
    chequear('suma a la lista',
             len(reg['listas']) == 1
             and reg['listas'][0]['body']['snippet']['resourceId']['videoId'] == 'VIDEO_FALSO', reg['listas'])

    limpiar()
    servicio['obj'] = _ServicioFalso(reg, fallos_miniatura=99, fallos_lista=99)
    vid = subir(vid_path, mini_path, 'T', 'D', [], cuando, lista='PL_FALSA')
    chequear('si la miniatura falla NO se pierde el video', vid == 'VIDEO_FALSO', vid)

    # ---- 8. falta el token: claro y temprano
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    guardado = cargar_credenciales
    inexistente = os.path.join(tmp, 'no_existe.json')
    cargar_credenciales = lambda path=None: _cargar_credenciales_real(inexistente)
    try:
        subir(vid_path, mini_path, 'T', 'D', [], cuando)
        chequear('sin token levanta FaltaToken', False, 'no levanto')
    except FaltaToken as e:
        m = str(e)
        chequear('sin token levanta FaltaToken', True)
        chequear('el mensaje dice como arreglarlo', '--autorizar' in m and 'no_existe.json' in m, m[:90])
        chequear('falla ANTES de subir nada', reg['inserts'] == [] and reg['miniaturas'] == [])
    except Exception as e:
        chequear('sin token levanta FaltaToken', False, '%s: %s' % (type(e).__name__, e))
    cargar_credenciales = guardado

    # ---- 9. validaciones baratas primero
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    casos = [('video inexistente', (os.path.join(tmp, 'nada.mp4'), None, 'T', 'D', [], cuando), FileNotFoundError),
             ('titulo vacio', (vid_path, None, '  ', 'D', [], cuando), ValueError),
             ('miniatura inexistente', (vid_path, os.path.join(tmp, 'nada.jpg'), 'T', 'D', [], cuando),
              FileNotFoundError),
             ('publicar_en naive', (vid_path, None, 'T', 'D', [], datetime(2099, 9, 11, 12, 0)), ValueError),
             ('publicar_en en el pasado', (vid_path, None, 'T', 'D', [],
                                           datetime(2020, 1, 1, tzinfo=timezone.utc)), ValueError)]
    for nombre, args, esperado in casos:
        try:
            subir(*args)
            chequear(nombre + ' da error', False, 'no levanto')
        except esperado:
            chequear(nombre + ' da error', True)
        except Exception as e:
            chequear(nombre + ' da error', False, '%s: %s' % (type(e).__name__, e))
    chequear('ninguna validacion llego a la API', reg['inserts'] == [])

    # ---- 10. recortes
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    subir(vid_path, None, 'X' * 200, 'D' * 6000, ['t%d' % i for i in range(50)] + ['', '  '], cuando)
    sn = reg['inserts'][0]['body']['snippet']
    chequear('recorta el titulo a 100', len(sn['title']) == MAX_TITULO, len(sn['title']))
    chequear('recorta la descripcion a 5000', len(sn['description']) == MAX_DESCRIPCION, len(sn['description']))
    chequear('recorta a 30 etiquetas y saca las vacias', len(sn['tags']) == MAX_ETIQUETAS, len(sn['tags']))
    chequear('AVISA que recorto el titulo', hay_aviso('AVISO: titulo de 200'), reg['avisos'])
    chequear('AVISA que recorto la descripcion', hay_aviso('AVISO: descripcion de 6000'), reg['avisos'])

    # ---- 10b. el tope que YouTube aplica de verdad: 500 caracteres en total, no 30 etiquetas
    limpiar()
    servicio['obj'] = _ServicioFalso(reg)
    largas = ['global economy briefing %d' % i for i in range(30)]     # 799 caracteres con las comas
    subir(vid_path, None, 'T', 'D', largas, cuando)
    puestas = reg['inserts'][0]['body']['snippet']['tags']
    chequear('respeta los 500 caracteres de etiquetas de YouTube',
             len(','.join(puestas)) <= MAX_ETIQUETAS_CHARS and 0 < len(puestas) < 30,
             '%d etiquetas, %d caracteres' % (len(puestas), len(','.join(puestas))))
    chequear('AVISA que dejo etiquetas afuera', hay_aviso('AVISO: de 30 etiquetas entran'), reg['avisos'])

    # ---- 10c. el AVISO de la miniatura dice POR QUE fallo, no solo el codigo
    limpiar()
    servicio['obj'] = _ServicioFalso(reg, fallos_miniatura=99)
    subir(vid_path, mini_path, 'T', 'D', [], cuando)
    chequear('el AVISO de la miniatura trae el motivo real de Google',
             hay_aviso('la miniatura fallo') and hay_aviso('prueba'),
             [a for a in reg['avisos'] if 'miniatura' in a])

    # ---- 11. lo que no se puede probar sin el VPS
    _log = log_real
    print('SALTEA: subida real a YouTube (necesita radar/_yt_token.json, red y cuota de la API).')
    print('SALTEA: flujo --autorizar (abre el navegador y pide el consentimiento de una persona).')
    print('SALTEA: renovacion del access token (necesita un refresh token valido de Google).')
    if not os.path.isfile(TOKEN):
        print('SALTEA: chequeo del token en %s (todavia no existe; correr --autorizar en el VPS).' % TOKEN)

    shutil.rmtree(tmp, ignore_errors=True)   # el autotest no deja basura en el temporal
    print('\n%d pruebas, %d fallas' % (cuenta['total'], len(fallas)))
    return 1 if fallas else 0


_cargar_credenciales_real = cargar_credenciales   # copia sin monkeypatch, para probar el token faltante


def main(argv=None):
    ap = argparse.ArgumentParser(description='Subida programada del video diario a YouTube.')
    ap.add_argument('--autotest', action='store_true', help='prueba sin red ni credenciales')
    ap.add_argument('--autorizar', action='store_true', help='consentimiento OAuth, una sola vez')
    ap.add_argument('--cuota', action='store_true', help='imprime la cuota estimada por corrida')
    a = ap.parse_args(argv)
    if a.autotest:
        return _autotest()
    if a.autorizar:
        autorizar()
        return 0
    if a.cuota:
        print('%d de %d unidades por corrida (%d corridas por dia)'
              % (cuota_estimada(), LIMITE_DIARIO, LIMITE_DIARIO // cuota_estimada()))
        return 0
    ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
