"""Contratos de medicion local: nulos honestos, UTC, formatos y capturas validas."""

from pathlib import Path
import tempfile
import unittest

from produccion import metricas_produccion as M


def sample(**updates):
    data=dict(video_id='episodio-prueba',format='largo',published_at='2026-09-16T12:00:00Z',
              observed_at='2026-09-17T12:00:00Z',window='24h',metrics={})
    data.update(updates)
    return data


class MetricasTest(unittest.TestCase):
    def test_no_observado_no_se_convierte_en_cero(self):
        record=M.validate_capture(sample())
        self.assertTrue(all(value is None for value in record['metrics'].values()))
        self.assertIsNone(record['channel_subscribers'])
        report=M.report(M.empty_store())
        self.assertIsNone(report['objective']['latest_channel_subscribers'])
        self.assertIsNone(report['objective']['remaining_channel_subscribers'])

    def test_cero_medido_se_conserva(self):
        record=M.validate_capture(sample(metrics={'views':0,'ctr_pct':0},channel_subscribers=0))
        self.assertEqual(record['metrics']['views'],0)
        self.assertEqual(record['channel_subscribers'],0)

    def test_porcentajes_negativos_nan_booleanos_y_conteos_fraccionarios(self):
        bad=[{'views':-1},{'views':1.2},{'views':True},{'ctr_pct':101},
             {'retention_30s_pct':-2},{'average_view_duration_seconds':float('nan')},
             {'subscribers_gained':-2}]
        for metrics in bad:
            with self.subTest(metrics=metrics),self.assertRaises(ValueError):
                M.validate_capture(sample(metrics=metrics))

    def test_fechas_siempre_aware_y_ordenadas(self):
        for stamp in ('2026-09-17T12:00:00','2026-09-16T11:59:59Z'):
            with self.assertRaises(ValueError):
                M.validate_capture(sample(observed_at=stamp))
        record=M.validate_capture(sample(observed_at='2026-09-17T14:00:00+02:00'))
        self.assertEqual(record['observed_at'],'2026-09-17T12:00:00Z')
        self.assertEqual(record['observed_age_hours'],24)

    def test_captura_tardia_conserva_edad_real(self):
        record=M.validate_capture(sample(observed_at='2026-09-17T15:00:00Z'))
        self.assertEqual(record['observed_age_hours'],27)
        self.assertEqual(record['window_offset_hours'],3)

    def test_short_corto_no_inventa_retencion_30(self):
        with self.assertRaises(ValueError):
            M.validate_capture(sample(format='short',video_duration_seconds=21,
                                      metrics={'retention_30s_pct':25}))
        self.assertIsNone(M.validate_capture(sample(format='short',video_duration_seconds=21))
                          ['metrics']['retention_30s_pct'])

    def test_repeticiones_no_truncan_retencion_observada(self):
        record=M.validate_capture(sample(metrics={'retention_30s_pct':115.5}))
        self.assertEqual(record['metrics']['retention_30s_pct'],115.5)

    def test_repeticion_idempotente_y_separacion_de_formatos(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Path(folder)/'metrics.json'
            capture=sample(metrics={'views':0})
            self.assertEqual(M.capture(store,capture)['status'],'recorded')
            self.assertEqual(M.capture(store,capture)['status'],'already_exists')
            with self.assertRaises(ValueError):
                M.capture(store,sample(format='short'))
            M.capture(store,sample(video_id='short-prueba',format='short',metrics={'views':900}))
            report=M.report(M.load(store))
            self.assertEqual(report['snapshot_count'],2)
            self.assertEqual(len(report['by_format']['largo']),1)
            self.assertEqual(len(report['by_format']['short']),1)
            self.assertFalse(report['by_format']['largo'][0]['long_views_goal_met_at_latest_observation'])
            self.assertIsNone(report['by_format']['short'][0]['long_views_goal_met_at_latest_observation'])

    def test_baseline_es_observacion_y_meta_no_es_garantia(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Path(folder)/'metrics.json'
            M.baseline(store,123,'2026-09-16T12:00:00Z')
            report=M.report(M.load(store))
            self.assertEqual(report['objective']['latest_channel_subscribers'],123)
            self.assertEqual(report['objective']['remaining_channel_subscribers'],377)
            self.assertEqual(report['objective']['kind'],'objective_not_guarantee')
            self.assertIn('no demuestra causalidad',report['interpretation'])


if __name__=='__main__':
    unittest.main()
