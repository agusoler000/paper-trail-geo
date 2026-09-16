"""Pruebas locales del contrato, sin red, voz, render ni publicacion."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from produccion import paquete_editorial as P


def empaque(question='Who Pays the US Debt?', ident='debt'):
    p = P._packaging()
    p['promise'].update(id=ident, question=question, answer='The cost can reach domestic savers.', source_ids=['F1'])
    p['title'].update(text=question + ' Follow the Money. #USDebt #Economy #Inflation', promise_id=ident, source_ids=['F1'])
    p['thumbnail'].update(text=question, promise_id=ident, source_ids=['F1'], country_flags=['US'],
                          brief='A US receipt moves toward a paper saver.', image_path='thumb.png')
    p['hook'].update(promise_id=ident, source_ids=['F1'])
    p['hook']['visual'].update(action='A receipt enters the saver pocket.', response='The US bill reaches a person.')
    p['hook']['audio'].update(text='Which pocket?')
    return p


def paquete():
    p = P.plantilla('09', 'US debt')
    p['sources'] = [{'id': 'F1', 'url': 'https://example.org/primary', 'claim': 'US debt source', 'status': 'verified'}]
    p['packaging'] = empaque()
    p['long_video']['script_text'] = 'A long original narrative about the Treasury, its creditors, and purchasing power.'
    texts = ['A government receipt can travel into a saver account. The twist is purchasing power.',
             'A ranking changes when another creditor moves above China. The twist is who owns the rest.',
             'A balance rises through several administrations. The twist is a pattern across parties.']
    twists = ['The twist is purchasing power.', 'The twist is who owns the rest.', 'The twist is a pattern across parties.']
    for i, (text, twist) in enumerate(zip(texts, twists)):
        p['shorts'].append({'id': 's%d' % i, 'content_mode': 'original_script', 'standalone': True,
                            'script_text': text + ' Which change surprised you? Tell us in the comments. Follow Paper Trail for the full US debt story.',
                            'source_ids': ['F1'], 'duration_estimate_s': 60,
                            'twist': {'text': twist, 'at_s': 20, 'source_ids': ['F1']},
                            'engagement': {'comment_question': 'Which change surprised you?'},
                            'cta': {'text': 'Follow Paper Trail for the full US debt story.',
                                    'related_episode_id': '09', 'availability': 'pending', 'related_url': '',
                                    'advanced_features_enabled': False},
                            'packaging': empaque(), 'media_path': ''})
    return p


class ContratoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.p = paquete()

    def codes(self, p=None, evidence=False):
        return {e['codigo'] for e in P.validar(self.p if p is None else p, self.base, evidence)['errores']}

    def evidencia(self):
        frames = []
        for i in range(3):
            im = Image.new('RGB', (640, 360), 'white')
            ImageDraw.Draw(im).rectangle((40 + i * 50, 30, 300 + i * 30, 280), fill=(30, 110, 70))
            frames.append(im)
        frames[0].save(self.base / 'thumb.png')
        inspect = {'frames': frames, 'first_audible_s': .1, 'duration_s': 60,
                   'width': 720, 'height': 1280, 'method': 'test_rms'}
        for i, obj in enumerate([self.p['long_video']] + self.p['shorts']):
            video = self.base / ('video%d.mp4' % i)
            video.write_bytes(('distinct export %d' % i).encode())
            obj['media_path'] = video.name
            packaging = self.p['packaging'] if i == 0 else obj['packaging']
            with patch.object(P, '_inspeccionar_video', return_value=inspect):
                packaging['hook']['evidence'] = P.capturar_evidencia(video, self.base, 'evidence%d' % i)
        return inspect

    def test_empty_and_legacy_are_blocked(self):
        for p in (P.plantilla('09', 'debt'), {}, {'schema_version': 0}):
            self.assertFalse(P.validar_empaque(p, self.base)['ok'])
            self.assertFalse(P.validar(p, self.base, False)['ok'])

    def test_packaging_can_precede_scripts_but_not_publish(self):
        self.p['long_video']['script_text'] = ''
        self.p['shorts'] = []
        result = P.validar_empaque(self.p, self.base)
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['ready_for_human_qc'])
        self.assertFalse(result['publish_allowed'])
        self.assertIn('GUION_FALTA', self.codes())

    def test_full_draft_and_semantic_warning(self):
        result = P.validar(self.p, self.base, False)
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['ready_for_human_qc'])
        self.assertIn('SEMANTICA_HUMANA', {w['codigo'] for w in result['advertencias']})

    def test_human_approval_requires_owner_and_utc_date(self):
        self.p['human_qc'].update(status='approved', reviewer='Bob', reviewed_at='yesterday')
        self.assertTrue({'QC_REVISOR', 'QC_FECHA'} <= self.codes())
        self.assertEqual(P.validar(self.p, self.base, False)['human_qc_status'], 'invalid')
        self.p['human_qc'].update(reviewer='Agustin', reviewed_at=datetime.now(timezone.utc).isoformat())
        result = P.validar(self.p, self.base, False)
        self.assertTrue(result['ok'], result)
        self.assertFalse(result['publish_allowed'])
        self.p['human_qc']['reviewed_at'] = '2026-01-01T00:00:00'
        self.assertIn('QC_FECHA', self.codes())

    def test_promise_and_title_are_linked(self):
        self.p['packaging']['title']['promise_id'] = 'other'
        self.p['packaging']['title']['text'] = 'Who Owns Oil? Follow the Money.'
        self.assertTrue({'PROMESA_DISTINTA', 'PREGUNTA_DISTINTA'} <= self.codes())

    def test_hook_starts_zero_and_audio_before_two(self):
        self.p['packaging']['hook']['visual']['start_s'] = .1
        self.p['packaging']['hook']['audio']['start_s'] = 2
        self.assertTrue({'HOOK_NO_FRAME_CERO', 'HOOK_TARDIO'} <= self.codes())

    def test_title_limit_is_platform_not_sixty(self):
        prefix = 'Who Pays the US Debt? '
        suffix = ' #USDebt #Economy #Inflation'
        self.p['packaging']['title']['text'] = prefix + 'x' * (100 - len(prefix) - len(suffix)) + suffix
        self.assertNotIn('TITULO_LARGO', self.codes())
        self.p['packaging']['title']['text'] += 'x'
        self.assertIn('TITULO_LARGO', self.codes())

    def test_title_and_description_share_three_hashtags(self):
        self.p['packaging']['title']['text'] = 'Who Pays the US Debt? Follow the Money.'
        self.assertIn('TITULO_HASHTAGS', self.codes())
        self.p['packaging'] = empaque()
        self.p['packaging']['description'] = {'text': 'A receipt. #USDebt #Economy #History', 'source_ids': ['F1']}
        self.assertIn('DESCRIPCION_HASHTAGS', self.codes())

    def test_pending_cta_cannot_claim_live_or_clickable_description(self):
        self.p['shorts'][0]['script_text'] += ' The full video is live. Link in the description.'
        self.assertTrue({'CTA_DISPONIBILIDAD_FALSA', 'CTA_ENLACE_SHORT'} <= self.codes())

    def test_related_video_requires_actual_availability(self):
        cta = self.p['shorts'][0]['cta']
        cta.update(availability='published', related_url='https://www.youtube.com/watch?v=abcdefghijk')
        self.assertTrue({'CTA_PRINCIPAL_PRIVADO', 'CTA_FEATURE', 'CTA_URL'} <= self.codes())
        self.p['long_video'].update(visibility='unlisted', public_url=cta['related_url'])
        cta['advanced_features_enabled'] = True
        self.assertFalse(self.codes())

    def test_count_adjustment_and_minimum_duration(self):
        self.p['shorts'].pop()
        self.assertIn('SHORTS_CANTIDAD', self.codes())
        self.p['policy'].update(shorts_min=2, shorts_max=4)
        self.assertIn('SHORTS_SIN_MOTIVO', self.codes())
        self.p['policy']['shorts_override_reason'] = 'User chose two self-contained shorts for this production.'
        self.assertFalse(self.codes())
        self.p['shorts'][0]['duration_estimate_s'] = 49.9
        self.assertIn('SHORT_DURACION', self.codes())

    def test_twist_and_cta_must_be_in_script(self):
        self.p['shorts'][0]['twist']['text'] = 'An unsupported twist only in the notes.'
        self.p['shorts'][0]['cta']['text'] = 'A missing line.'
        self.assertTrue({'GIRO_NO_EN_GUION', 'CTA_NO_EN_GUION'} <= self.codes())

    def test_comment_question_must_be_spoken(self):
        self.p['shorts'][0]['engagement']['comment_question'] = 'A new question only in notes?'
        self.assertIn('COMENTARIO_NO_EN_GUION', self.codes())

    def test_no_repeated_or_clipped_scripts(self):
        self.p['shorts'][1] = deepcopy(self.p['shorts'][0])
        self.assertIn('GUION_REPETIDO', self.codes())
        self.p = paquete()
        text = ' '.join('word%d' % i for i in range(100))
        self.p['long_video']['script_text'] = text
        self.p['shorts'][0]['script_text'] = text + ' Follow Paper Trail for the full US debt story.'
        self.assertIn('GUION_REPETIDO', self.codes())

    def test_unverified_sources_and_whitespace_script_blocked(self):
        self.p['sources'][0]['status'] = 'pending'
        self.assertIn('FUENTE_PENDIENTE', self.codes())
        (self.base / 'empty.txt').write_text('   \n', encoding='utf-8')
        self.p['long_video'].update(script_text='', script_path='empty.txt')
        self.assertIn('VACIO', self.codes())

    def test_missing_evidence_and_malformed_input_are_errors(self):
        self.assertIn('EVIDENCIA_ARCHIVO', self.codes(evidence=True))
        self.p['policy'] = None
        self.p['episode'] = []
        self.p['packaging']['hook']['evidence']['frames'][0]['second'] = {}
        result = P.validar(self.p, self.base, True)
        self.assertFalse(result['ok'])
        self.assertIn('CUADROS_FALTAN', {e['codigo'] for e in result['errores']})

    def test_export_evidence_ready_only_for_human_qc(self):
        inspect = self.evidencia()
        with patch.object(P, '_inspeccionar_video', return_value=inspect):
            result = P.validar(self.p, self.base, True)
        self.assertTrue(result['ok'], result)
        self.assertTrue(result['ready_for_human_qc'])
        self.assertFalse(result['publish_allowed'])

    def test_changed_hash_wrong_frame_and_silence_blocked(self):
        inspect = self.evidencia()
        e = self.p['packaging']['hook']['evidence']
        e['video_sha256'] = '0' * 64
        with patch.object(P, '_inspeccionar_video', return_value=inspect):
            self.assertIn('EVIDENCIA_ARCHIVO', self.codes(evidence=True))
        e['video_sha256'] = P._sha(self.base / self.p['long_video']['media_path'])
        inspect['first_audible_s'] = None
        inspect['frames'][0] = Image.new('RGB', (640, 360), 'black')
        with patch.object(P, '_inspeccionar_video', return_value=inspect):
            self.assertTrue({'CUADRO_INVALIDO', 'EXPORT_SILENCIOSO'} <= self.codes(evidence=True))

    def test_actual_short_duration_overrides_estimate(self):
        inspect = self.evidencia()
        inspect['duration_s'] = 49
        with patch.object(P, '_inspeccionar_video', return_value=inspect):
            self.assertIn('SHORT_EXPORT_CORTO', self.codes(evidence=True))

    def test_horizontal_export_is_not_a_short(self):
        inspect = self.evidencia()
        inspect.update(width=1280, height=720)
        with patch.object(P, '_inspeccionar_video', return_value=inspect):
            self.assertIn('SHORT_NO_VERTICAL', self.codes(evidence=True))


if __name__ == '__main__':
    from radar.entorno import cargar
    cargar()
    unittest.main()
