"""Contrato editorial y evidencia de apertura, sin publicar ni generar voz/arte.

`validar_empaque` sirve antes del guion. `validar` exige ademas el largo y shorts
autonomos; con evidencia verifica los primeros dos segundos del archivo final.
La coherencia semantica y la aprobacion editorial siguen siendo humanas.
"""

import argparse
from array import array
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageChops, ImageStat

VERSION = 1
VACIOS = {'', 'todo', 'tbd', 'pending', 'pendiente', 'por definir', '...', 'n/a'}
DISPONIBLE = re.compile(r'\b(?:available now|out now|live now|already available|already up|'
                        r'full (?:video|episode)(?: is|\'s) (?:up|out|live|available))\b', re.I)


def _texto(value):
    return isinstance(value, str) and value.strip().lower() not in VACIOS


def _normal(value):
    return ' '.join(re.findall(r'[a-z0-9]+', str(value).lower()))


def _numero(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _packaging():
    return {'promise': {'id': '', 'question': '', 'answer': '', 'source_ids': []},
            'title': {'text': '', 'promise_id': '', 'source_ids': []},
            'thumbnail': {'text': '', 'promise_id': '', 'source_ids': [], 'country_flags': [],
                          'brief': '', 'image_path': ''},
            'hook': {'promise_id': '', 'visual': {'start_s': 0, 'action': '',
                                                 'response_by_s': 1, 'response': ''},
                     'audio': {'start_s': 0, 'text': '', 'kind': 'narration'}, 'source_ids': [],
                     'evidence': {'video_path': '', 'video_sha256': '',
                                  'frames': [{'second': i, 'path': '', 'sha256': ''} for i in range(3)],
                                  'audio': {'path': '', 'sha256': '', 'first_audible_s': None,
                                            'method': ''}}}}


def plantilla(episode_id, tema, formato='largo'):
    """Borrador deliberadamente incompleto: nunca aprueba por traer campos vacios."""
    return {'schema_version': VERSION,
            'episode': {'id': str(episode_id), 'topic': str(tema), 'format': formato, 'language': 'en'},
            'sources': [], 'packaging': _packaging(),
            'long_video': {'script_path': '', 'script_text': '', 'media_path': '',
                           'published': False, 'visibility': 'private', 'public_url': ''},
            'shorts': [],
            'policy': {'manual_schedule': True, 'no_auto_publish': True,
                       'shorts_min': 3, 'shorts_max': 5, 'shorts_override_reason': ''},
            'human_qc': {'status': 'pending', 'reviewer': '', 'reviewed_at': ''},
            'goals': {'views_per_video': 500, 'subscribers': 500,
                      'deadline': '2026-09-30', 'guaranteed': False}}


def _path(base, value):
    if not _texto(value):
        raise ValueError('Falta la ruta del archivo')
    path = Path(value)
    path = path.resolve() if path.is_absolute() else (base / path).resolve()
    if not path.is_relative_to(base):
        raise ValueError('La evidencia debe quedar dentro del directorio de produccion')
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('Archivo inexistente o vacio: %s' % value)
    return path


def _sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def _youtube(url):
    p = urlparse(url if isinstance(url, str) else '')
    host = (p.hostname or '').lower()
    if p.scheme != 'https' or host not in ('youtube.com', 'www.youtube.com', 'youtu.be'):
        return False
    vid = p.path.strip('/') if host == 'youtu.be' else parse_qs(p.query).get('v', [''])[0]
    return bool(re.fullmatch(r'[A-Za-z0-9_-]{11}', vid))


def _inspeccionar_video(path):
    """Decodifica la evidencia desde el export, incluida su pista audible real."""
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
                       capture_output=True, check=True, timeout=30)
    info = json.loads(p.stdout)
    streams = info.get('streams', [])
    visual = next((s for s in streams if s.get('codec_type') == 'video'), None)
    if not visual:
        raise ValueError('El export no tiene video')
    if not any(s.get('codec_type') == 'audio' for s in streams):
        raise ValueError('El export no tiene audio')
    duration = float(info.get('format', {}).get('duration', 0))
    if duration < 2.01:
        raise ValueError('El export no permite verificar los segundos 0, 1 y 2')
    frames = []
    for second in range(3):
        p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(second), '-i', str(path),
                            '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                           capture_output=True, check=True, timeout=30)
        with Image.open(BytesIO(p.stdout)) as im:
            frames.append(im.convert('RGB'))
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-t', '2', '-vn',
                        '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                       capture_output=True, check=True, timeout=30)
    samples = array('h')
    samples.frombytes(p.stdout[:len(p.stdout) // 2 * 2])
    if sys.byteorder != 'little':
        samples.byteswap()
    audible = None
    # Ventanas de 10 ms; el umbral permite voz/SFX discretos y descarta silencio.
    for i in range(0, len(samples), 160):
        block = samples[i:i + 160]
        rms = math.sqrt(sum(s * s for s in block) / max(1, len(block)))
        if rms >= 184:
            audible = i / 16000
            break
    return {'frames': frames, 'first_audible_s': audible, 'duration_s': duration,
            'width': int(visual['width']), 'height': int(visual['height']),
            'method': 'export_pcm16_rms_minus45db_10ms'}


class _Validador:
    def __init__(self, base, evidencia):
        self.base = Path(base or Path.cwd()).resolve()
        self.evidencia = evidencia
        self.errores, self.avisos = [], []
        self.fuentes = {}
        self.exports = {}

    def error(self, code, path, text):
        self.errores.append({'codigo': code, 'ruta': path, 'mensaje': text})

    def aviso(self, code, path, text):
        self.avisos.append({'codigo': code, 'ruta': path, 'mensaje': text})

    def texto(self, value, path):
        if not _texto(value):
            self.error('VACIO', path, 'Falta contenido concreto; no sirve un marcador pendiente')
            return False
        return True

    def obj(self, value, path):
        if not isinstance(value, dict):
            self.error('TIPO', path, 'Se esperaba un objeto JSON')
            return {}
        return value

    def refs(self, value, path):
        if not isinstance(value, list) or not value:
            self.error('SIN_FUENTES', path, 'La afirmacion necesita fuentes identificadas')
            return
        for key in value:
            if not isinstance(key, str) or key not in self.fuentes:
                self.error('FUENTE_DESCONOCIDA', path, 'Referencia no declarada: %r' % key)
            elif self.fuentes[key].get('status') != 'verified':
                self.error('FUENTE_PENDIENTE', path, 'La fuente %s no esta verificada' % key)

    def sources(self, data):
        if not isinstance(data, list) or not data:
            self.error('SIN_FUENTES', 'sources', 'Faltan fuentes del encargo')
            return
        for i, item in enumerate(data):
            p = 'sources[%d]' % i
            s = self.obj(item, p)
            if not self.texto(s.get('id'), p + '.id'):
                continue
            if s['id'] in self.fuentes:
                self.error('FUENTE_DUPLICADA', p, 'ID de fuente repetido')
            self.fuentes[s['id']] = s
            self.texto(s.get('claim'), p + '.claim')
            url = urlparse(s.get('url', '') if isinstance(s.get('url', ''), str) else '')
            if not (url.scheme == 'https' and url.hostname):
                try:
                    _path(self.base, s.get('evidence_path'))
                except ValueError as exc:
                    self.error('FUENTE_SIN_EVIDENCIA', p, str(exc))

    def packaging(self, data, path, media_path=''):
        d = self.obj(data, path)
        prom = self.obj(d.get('promise'), path + '.promise')
        for key in ('id', 'question', 'answer'):
            self.texto(prom.get(key), path + '.promise.' + key)
        self.refs(prom.get('source_ids'), path + '.promise.source_ids')
        title = self.obj(d.get('title'), path + '.title')
        thumb = self.obj(d.get('thumbnail'), path + '.thumbnail')
        hook = self.obj(d.get('hook'), path + '.hook')
        for label, item in (('title', title), ('thumbnail', thumb), ('hook', hook)):
            if not _texto(item.get('promise_id')) or item.get('promise_id') != prom.get('id'):
                self.error('PROMESA_DISTINTA', path + '.' + label, 'Debe desarrollar la misma promesa editorial')
            self.refs(item.get('source_ids'), path + '.' + label + '.source_ids')
        if self.texto(title.get('text'), path + '.title.text'):
            text = title['text']
            tags = re.findall(r'(?<!\w)#[A-Za-z0-9_]+', text)
            if len(tags) != 3 or len(set(tags)) != 3:
                self.error('TITULO_HASHTAGS', path + '.title', 'La regla vigente del canal pide tres hashtags distintos')
            if len(text) > 100:
                self.error('TITULO_LARGO', path + '.title', 'Supera el limite de 100 caracteres')
            elif len(text) > 70:
                self.aviso('TITULO_REVISAR', path + '.title', 'Revisar concision; 70 es orientativo, no un limite obligatorio')
            question, mark, tail = text.partition('?')
            if not mark or not _normal(re.sub(r'#\w+', '', tail)):
                self.error('FORMULA_TITULO', path + '.title', 'Falta pregunta seguida de una frase corta')
            if _texto(prom.get('question')) and _normal(question) != _normal(prom['question']):
                self.error('PREGUNTA_DISTINTA', path + '.title', 'La pregunta del titulo difiere de la promesa')
            if 'description' in d:
                desc = self.obj(d['description'], path + '.description')
                if self.texto(desc.get('text'), path + '.description.text'):
                    description_tags = re.findall(r'(?<!\w)#[A-Za-z0-9_]+', desc['text'])
                    if len(description_tags) != 3 or set(description_tags) != set(tags):
                        self.error('DESCRIPCION_HASHTAGS', path + '.description', 'Usar los mismos tres hashtags que el titulo')
                self.refs(desc.get('source_ids'), path + '.description.source_ids')
        if self.texto(thumb.get('text'), path + '.thumbnail.text'):
            if '?' not in thumb['text']:
                self.error('MINIATURA_SIN_PREGUNTA', path + '.thumbnail', 'La miniatura debe conservar la pregunta')
            if _normal(thumb['text']) != _normal(prom.get('question', '')):
                if (_normal(thumb.get('question_ref', '')) != _normal(prom.get('question', ''))
                        or not _texto(thumb.get('coherence_note'))):
                    self.error('MINIATURA_PROMESA', path + '.thumbnail',
                               'Una pregunta abreviada necesita question_ref y una explicacion de coherencia')
        self.texto(thumb.get('brief'), path + '.thumbnail.brief')
        flags = thumb.get('country_flags')
        if not isinstance(flags, list) or not flags:
            self.error('BANDERA_FALTA', path + '.thumbnail.country_flags',
                       'Declarar las banderas de los paises tratados, o country_flags_no_aplica con motivo')
            if _texto(thumb.get('country_flags_no_aplica')):
                self.errores.pop()
        visual = self.obj(hook.get('visual'), path + '.hook.visual')
        audio = self.obj(hook.get('audio'), path + '.hook.audio')
        for key in ('action', 'response'):
            self.texto(visual.get(key), path + '.hook.visual.' + key)
        for label, piece in (('visual', visual), ('audio', audio)):
            start = piece.get('start_s')
            if not _numero(start) or not 0 <= start < 2:
                self.error('HOOK_TARDIO', path + '.hook.' + label, 'Debe empezar dentro de los primeros dos segundos')
            elif label == 'visual' and start != 0:
                self.error('HOOK_NO_FRAME_CERO', path + '.hook.visual', 'La accion visual debe existir desde el cuadro cero')
        response = visual.get('response_by_s')
        if not _numero(response) or not 0 <= response <= 1:
            self.error('PROMESA_TARDIA', path + '.hook.visual.response_by_s',
                       'El primer segundo debe reconocer visualmente la promesa; no exige revelar toda la respuesta')
        if _numero(response) and _numero(visual.get('start_s')) and response < visual['start_s']:
            self.error('RELOJ_HOOK', path + '.hook.visual', 'La respuesta no puede ocurrir antes de empezar la accion')
        self.texto(audio.get('text'), path + '.hook.audio.text')
        if audio.get('kind') not in ('narration', 'sfx', 'both'):
            self.error('AUDIO_TIPO', path + '.hook.audio.kind', 'Indicar narracion, efecto o ambos')
        if self.evidencia:
            try:
                p = _path(self.base, thumb.get('image_path'))
                with Image.open(p) as im:
                    im.verify()
            except (ValueError, OSError) as exc:
                self.error('MINIATURA_SIN_ARCHIVO', path + '.thumbnail.image_path', str(exc))
            self.evidence(hook.get('evidence'), path + '.hook.evidence', media_path)

    def archivo_hash(self, data, key, path):
        try:
            p = _path(self.base, data.get(key))
            digest = data.get('video_sha256' if key == 'video_path' else 'sha256')
            if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
                raise ValueError('Falta SHA-256 del archivo revisado')
            if _sha(p) != digest:
                raise ValueError('El archivo cambio despues de registrar la evidencia')
            return p
        except ValueError as exc:
            self.error('EVIDENCIA_ARCHIVO', path, str(exc))
            return None

    def evidence(self, data, path, media_path):
        e = self.obj(data, path)
        video = self.archivo_hash(e, 'video_path', path + '.video_path')
        if video:
            try:
                if _path(self.base, media_path) != video:
                    raise ValueError('La evidencia debe salir del mismo master que se entregara')
                if video not in self.exports:
                    self.exports[video] = _inspeccionar_video(video)
            except (ValueError, OSError, subprocess.SubprocessError, KeyError, json.JSONDecodeError) as exc:
                self.error('EXPORT_NO_VERIFICADO', path, str(exc))
                video = None
        frames = e.get('frames')
        if not isinstance(frames, list):
            frames = []
        seconds = [f.get('second') for f in frames if isinstance(f, dict)
                   and _numero(f.get('second'))]
        if len(frames) != 3 or len(seconds) != 3 or set(seconds) != {0, 1, 2}:
            self.error('CUADROS_FALTAN', path + '.frames', 'Se necesitan exactamente cuadros de los segundos 0, 1 y 2')
        for i, raw in enumerate(frames):
            f = self.obj(raw, path + '.frames[%d]' % i)
            p = self.archivo_hash(f, 'path', path + '.frames[%d]' % i)
            if not p:
                continue
            try:
                with Image.open(p) as im:
                    actual = im.convert('RGB')
                if min(actual.size) < 180 or max(actual.size) < 320:
                    raise ValueError('El cuadro es demasiado pequeno para inspeccionar la apertura')
                if max(ImageStat.Stat(actual).stddev) < 4:
                    raise ValueError('El cuadro esta vacio o es casi uniforme')
                sec = f.get('second')
                if video and _numero(sec) and sec in (0, 1, 2):
                    expected = self.exports[video]['frames'][int(sec)].resize(actual.size, Image.Resampling.LANCZOS)
                    diff = sum(ImageStat.Stat(ImageChops.difference(expected, actual)).mean) / 3
                    if diff > 8:
                        raise ValueError('El cuadro no coincide con ese segundo del export')
            except (ValueError, OSError) as exc:
                self.error('CUADRO_INVALIDO', path + '.frames[%d]' % i, str(exc))
        audio = self.obj(e.get('audio'), path + '.audio')
        ap = self.archivo_hash(audio, 'path', path + '.audio.path')
        if ap and video and ap != video:
            self.error('AUDIO_OTRO_ARCHIVO', path + '.audio', 'La prueba audible debe medir la pista del export final')
        first = audio.get('first_audible_s')
        if not _numero(first) or not 0 <= first < 2:
            self.error('HOOK_INAUDIBLE', path + '.audio', 'No hay evidencia de audio audible en los primeros dos segundos')
        self.texto(audio.get('method'), path + '.audio.method')
        if video:
            measured = self.exports[video]['first_audible_s']
            if measured is None or measured >= 2:
                self.error('EXPORT_SILENCIOSO', path + '.audio', 'El archivo final no tiene un comienzo audible')
            elif _numero(first) and abs(measured - first) > 0.1:
                self.error('AUDIO_MEDICION', path + '.audio', 'El comienzo audible declarado no coincide con el export')

    def script(self, data, path):
        if _texto(data.get('script_text')):
            return data['script_text']
        try:
            result = _path(self.base, data.get('script_path')).read_text(encoding='utf-8')
            return result if self.texto(result, path) else ''
        except (ValueError, OSError, UnicodeError) as exc:
            self.error('GUION_FALTA', path, str(exc))
            return ''

    def shorts(self, paquete, largo):
        items = paquete.get('shorts')
        policy = self.obj(paquete.get('policy'), 'policy')
        if not isinstance(items, list):
            self.error('SHORTS_FALTAN', 'shorts', 'Falta la lista de shorts propios')
            return
        lo, hi = policy.get('shorts_min', 3), policy.get('shorts_max', 5)
        if (not isinstance(lo, int) or isinstance(lo, bool) or not isinstance(hi, int)
                or isinstance(hi, bool) or lo < 0 or hi < lo):
            self.error('SHORTS_RANGO', 'policy', 'El rango de shorts no es valido')
            lo, hi = 3, 5
        override = _texto(policy.get('shorts_override_reason'))
        if (lo, hi) != (3, 5) and not override:
            self.error('SHORTS_SIN_MOTIVO', 'policy', 'Documentar por que se ajusta la referencia de 3 a 5 shorts')
        if not lo <= len(items) <= hi:
            self.error('SHORTS_CANTIDAD', 'shorts', 'Cantidad fuera del rango elegido %d..%d' % (lo, hi))
        scripts, ids = set(), set()
        main = self.obj(paquete.get('long_video'), 'long_video')
        episode = self.obj(paquete.get('episode'), 'episode')
        for i, item in enumerate(items):
            p = 'shorts[%d]' % i
            s = self.obj(item, p)
            if not self.texto(s.get('id'), p + '.id'):
                continue
            if s['id'] in ids:
                self.error('SHORT_DUPLICADO', p, 'ID de short repetido')
            ids.add(s['id'])
            if s.get('standalone') is not True or s.get('content_mode') != 'original_script':
                self.error('SHORT_NO_AUTONOMO', p, 'Se necesita historia autonoma con guion propio, no un recorte')
            duration = s.get('duration_estimate_s')
            if not _numero(duration) or duration < 50:
                self.error('SHORT_DURACION', p + '.duration_estimate_s', 'La referencia de formato vigente exige al menos 50 segundos')
            script = self.script(s, p + '.script')
            normal = _normal(script)
            words = normal.split()
            # Detecta un recorte con CTA agregado; no intenta juzgar originalidad semantica.
            overlap = SequenceMatcher(None, words, _normal(largo).split(), autojunk=False).find_longest_match().size
            if normal in scripts or (len(words) > 20 and overlap >= .8 * len(words)):
                self.error('GUION_REPETIDO', p, 'El guion repite otro short o es un recorte literal del largo')
            scripts.add(normal)
            self.refs(s.get('source_ids'), p + '.source_ids')
            giro = self.obj(s.get('twist'), p + '.twist')
            self.texto(giro.get('text'), p + '.twist.text')
            if _texto(giro.get('text')) and _normal(giro['text']) not in normal:
                self.error('GIRO_NO_EN_GUION', p + '.twist', 'El giro debe aparecer en el guion, no solo en las notas')
            if (not _numero(giro.get('at_s')) or giro['at_s'] < 0
                    or (_numero(duration) and giro['at_s'] >= duration)):
                self.error('GIRO_TIEMPO', p + '.twist.at_s', 'Falta el momento previsto del giro')
            self.refs(giro.get('source_ids'), p + '.twist.source_ids')
            engagement = self.obj(s.get('engagement'), p + '.engagement')
            question = engagement.get('comment_question')
            if self.texto(question, p + '.engagement.comment_question'):
                if '?' not in question or _normal(question) not in normal:
                    self.error('COMENTARIO_NO_EN_GUION', p + '.engagement',
                               'La pregunta concreta para comentarios debe aparecer en la voz del guion')
            cta = self.obj(s.get('cta'), p + '.cta')
            self.texto(cta.get('text'), p + '.cta.text')
            if _texto(cta.get('text')) and _normal(cta['text']) not in normal:
                self.error('CTA_NO_EN_GUION', p + '.cta', 'La voz debe decir la llamada al video principal')
            if cta.get('related_episode_id') != episode.get('id'):
                self.error('CTA_OTRO_EPISODIO', p + '.cta', 'La llamada debe remitir al episodio principal de este paquete')
            if re.search(r'\b(?:link in (?:the )?description|click (?:the )?description)\b', script, re.I):
                self.error('CTA_ENLACE_SHORT', p + '.cta', 'No prometer enlaces clicables en la descripcion del Short')
            available = cta.get('availability')
            if available not in ('pending', 'published'):
                self.error('CTA_ESTADO', p + '.cta', 'Indicar si el principal esta publicado o pendiente')
            if available == 'pending' and DISPONIBLE.search(script):
                self.error('CTA_DISPONIBILIDAD_FALSA', p + '.cta', 'El guion dice que el principal ya esta disponible')
            if available == 'published':
                if not (main.get('published') is True or main.get('visibility') == 'unlisted'):
                    self.error('CTA_PRINCIPAL_PRIVADO', p + '.cta', 'El video relacionado necesita ser publico o no listado')
                if not _youtube(cta.get('related_url')) or cta.get('related_url') != main.get('public_url'):
                    self.error('CTA_URL', p + '.cta', 'Falta la URL real del principal disponible')
                if cta.get('advanced_features_enabled') is not True:
                    self.error('CTA_FEATURE', p + '.cta', 'No esta verificada la disponibilidad de video relacionado en YouTube')
            self.packaging(s.get('packaging'), p + '.packaging', s.get('media_path', ''))
            if self.evidencia:
                try:
                    media = _path(self.base, s.get('media_path'))
                    if media in self.exports and self.exports[media]['duration_s'] < 50:
                        self.error('SHORT_EXPORT_CORTO', p + '.media_path', 'El export real dura menos de 50 segundos')
                    if media in self.exports and self.exports[media]['width'] >= self.exports[media]['height']:
                        self.error('SHORT_NO_VERTICAL', p + '.media_path', 'El export del Short debe ser vertical')
                except ValueError:
                    pass  # El chequeo de evidencia ya informa la ruta ausente.


def _validar(paquete, base_dir, exigir_evidencia, guiones):
    v = _Validador(base_dir, exigir_evidencia)
    p = v.obj(paquete, 'paquete')
    if p.get('schema_version') != VERSION:
        v.error('VERSION', 'schema_version', 'Version desconocida o paquete legado sin adaptar; no se aprueba vacio')
    episode = v.obj(p.get('episode'), 'episode')
    v.texto(episode.get('id'), 'episode.id')
    v.texto(episode.get('topic'), 'episode.topic')
    if episode.get('language') != 'en':
        v.error('IDIOMA', 'episode.language', 'El contenido del canal se prepara en ingles')
    if episode.get('format') not in ('largo', 'short'):
        v.error('FORMATO', 'episode.format', 'Formato esperado: largo o short')
    policy = v.obj(p.get('policy'), 'policy')
    if policy.get('manual_schedule') is not True or policy.get('no_auto_publish') is not True:
        v.error('PUBLICACION_HUMANA', 'policy', 'La frecuencia y la publicacion deben quedar en manos de Agustin')
    goals = v.obj(p.get('goals'), 'goals')
    if goals.get('guaranteed') is not False:
        v.error('META_NO_GARANTIA', 'goals.guaranteed', 'Las metas de vistas/suscriptores no son garantias')
    v.sources(p.get('sources'))
    main = v.obj(p.get('long_video'), 'long_video')
    v.packaging(p.get('packaging'), 'packaging', main.get('media_path', ''))
    if guiones:
        script = v.script(main, 'long_video.script')
        if episode.get('format') == 'largo':
            v.shorts(p, script)
    qc = v.obj(p.get('human_qc'), 'human_qc')
    if qc.get('status') not in ('pending', 'approved', 'rejected'):
        v.error('QC_ESTADO', 'human_qc', 'Falta el estado del QC humano')
    if qc.get('status') == 'approved':
        for field in ('reviewer', 'reviewed_at'):
            v.texto(qc.get(field), 'human_qc.' + field)
        if str(qc.get('reviewer', '')).strip().casefold() != 'agustin':
            v.error('QC_REVISOR', 'human_qc.reviewer', 'Solo se registra aprobacion explicita de Agustin')
        try:
            reviewed = datetime.fromisoformat(str(qc.get('reviewed_at', '')).replace('Z', '+00:00'))
            if reviewed.utcoffset() != timedelta(0) or reviewed > datetime.now(timezone.utc) + timedelta(minutes=1):
                raise ValueError('La fecha debe ser UTC aware y no futura')
        except ValueError as exc:
            v.error('QC_FECHA', 'human_qc.reviewed_at', str(exc))
    if not exigir_evidencia:
        v.aviso('BORRADOR', 'packaging.hook.evidence', 'Sin evidencia del export no esta listo para QC humano final')
    v.aviso('SEMANTICA_HUMANA', 'human_qc', 'IDs y evidencias no prueban por si solos que la promesa sea cierta: requiere revision humana')
    qc_status = qc.get('status', 'pending')
    if any(e['codigo'] in ('QC_REVISOR', 'QC_FECHA') for e in v.errores):
        qc_status = 'invalid'
    return {'ok': not v.errores, 'errores': v.errores, 'advertencias': v.avisos,
            'ready_for_human_qc': bool(exigir_evidencia and guiones and not v.errores),
            'human_qc_status': qc_status, 'publish_allowed': False}


def validar_empaque(paquete, base_dir=None):
    """Gate anterior al guion: promesa/titulo/miniatura/apertura y fuentes."""
    return _validar(paquete, base_dir, False, False)


def validar(paquete, base_dir=None, exigir_evidencia=True):
    """Gate del paquete completo; el resultado nunca autoriza una subida."""
    return _validar(paquete, base_dir, exigir_evidencia, True)


def capturar_evidencia(video, base_dir, out_dir):
    """Extrae la apertura del export final y devuelve un bloque evidence auditable."""
    base = Path(base_dir).resolve()
    path = _path(base, str(video))
    out = (base / out_dir).resolve()
    if not out.is_relative_to(base):
        raise ValueError('El destino de evidencia debe quedar en la produccion')
    info = _inspeccionar_video(path)
    out.mkdir(parents=True, exist_ok=True)
    digest = _sha(path)
    result = {'video_path': str(path.relative_to(base)), 'video_sha256': digest, 'frames': [],
              'audio': {'path': str(path.relative_to(base)), 'sha256': digest,
                        'first_audible_s': info['first_audible_s'], 'method': info['method']}}
    for i, frame in enumerate(info['frames']):
        dest = out / ('frame_%02d.png' % i)
        frame.save(dest)
        result['frames'].append({'second': i, 'path': str(dest.relative_to(base)), 'sha256': _sha(dest)})
    return result


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from radar.entorno import cargar
    cargar()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paquete', type=Path)
    parser.add_argument('--base', type=Path, required=True, help='Directorio de la produccion')
    parser.add_argument('--solo-empaque', action='store_true')
    parser.add_argument('--sin-evidencia', action='store_true')
    args = parser.parse_args()
    data = json.loads(args.paquete.read_text(encoding='utf-8'))
    result = (validar_empaque(data, args.base) if args.solo_empaque else
              validar(data, args.base, not args.sin_evidencia))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
