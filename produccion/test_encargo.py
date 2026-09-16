"""Pruebas offline del encargo: transiciones, evidencia y proteccion de originales."""

from datetime import timedelta
import importlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from produccion import encargo as E


def package(episode_id, topic, formato="largo"):
    return {"schema_version": 1, "episode": {"id": episode_id, "topic": topic}, "sources": [],
            "packaging": {"promise": {"question": "A question?"}, "title": {"text": "A question? A sentence."},
                          "thumbnail": {"text": "A QUESTION?", "image_path": ""},
                          "hook": {"visual": {"action": "receipt moves"}, "evidence": {}}},
            "long_video": {"script_text": "", "media_path": ""}, "shorts": []}


class EncargoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "videos").mkdir()
        self.base = self.root / "videos" / "10_test"
        self.patch_root = mock.patch.object(E, "RAIZ", self.root)
        self.patch_root.start()
        self.patch_editorial = mock.patch.object(E, "editorial", return_value=SimpleNamespace(
            plantilla=package, validar_empaque=lambda *a, **kw: {"ok": True, "errores": []},
            validar=lambda *a, **kw: {"ok": True, "errores": []}))
        self.patch_editorial.start()
        self.patch_upload = mock.patch.object(E, "upload_files_for_qc", return_value=[])
        self.patch_upload.start()
        E.new(self.base, topic="national debt")
        self.evidence("guion.md", "A: This is the actual narration draft.")
        draft = E.read_json(self.base / E.PACKAGE)
        draft["long_video"]["script_path"] = "guion.md"
        E.write_json(self.base / E.PACKAGE, draft)

    def tearDown(self):
        self.patch_upload.stop()
        self.patch_editorial.stop()
        self.patch_root.stop()
        self.temp.cleanup()

    def evidence(self, name, content="evidencia verificada"):
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return name

    def seed_complete(self, through):
        data = E.load(self.base)
        self.evidence(".encargo/demanda.json", json.dumps({"fetched_at": E.utc(), "topic_analysis": {"verdict": "LUZ VERDE - EVERGREEN"}}))
        for stage in E.STAGES[:E.STAGES.index(through) + 1]:
            path = ".encargo/demanda.json" if stage == "demanda" else self.evidence("evidence/" + stage + ".txt")
            data["stages"][stage] = {"status": "complete", "artifacts": [E.artifact(self.base, path)]}
        E.save(self.base, data)
        return data

    def report(self, stage):
        evidence = self.evidence("evidence/" + stage + ".txt")
        path = ".encargo/informes/" + stage + ".json"
        E.write_json(self.base / path, {"schema_version": 1, "stage": stage, "artifacts": [evidence],
                                     "checks": [{"id": name, "status": "pass", "evidence": [evidence]}
                                                for name in E.CHECKS[stage]]})
        return path

    def test_new_is_idempotent_and_preserves_script(self):
        guion = self.evidence("guion.md", "GUION APROBADO")
        before = (self.base / E.MANIFEST).read_bytes()
        E.new(self.base, topic="national debt")
        self.assertEqual(before, (self.base / E.MANIFEST).read_bytes())
        self.assertEqual((self.base / guion).read_text(), "GUION APROBADO")
        self.assertFalse(E.status(self.base)["publish_allowed"])
        self.assertEqual(E.status(self.base)["next"], "demanda")

    def test_new_rejects_existing_different_assignment(self):
        with self.assertRaises(ValueError):
            E.new(self.base, topic="different topic")

    def test_reject_daily_external_and_ambiguous_origin(self):
        for path in [self.root / "radar" / "x", self.root / "videos" / "DAILY", self.root / "videos" / "10_x" / "shorts"]:
            with self.assertRaises(ValueError):
                E.production_path(path)
        with self.assertRaises(ValueError):
            E.new(self.root / "videos" / "11_x", topic="x", trends=True)

    def test_report_cannot_escape_production(self):
        self.seed_complete("brief")
        report = self.report("fuentes")
        data = E.read_json(self.base / report)
        data["artifacts"] = ["../../outside.txt"]
        with self.assertRaises(ValueError):
            E.inside(self.base, data["artifacts"][0])

    def test_report_pending_check_does_not_complete(self):
        self.seed_complete("brief")
        with self.assertRaisesRegex(ValueError, "entregables"):
            E.register(self.base, "fuentes", ".encargo/informes/fuentes.json")

    def test_register_idempotent_and_invalidates_changed_evidence(self):
        self.seed_complete("brief")
        report = self.report("fuentes")
        E.register(self.base, "fuentes", report)
        before = (self.base / E.MANIFEST).read_bytes()
        E.register(self.base, "fuentes", report)
        self.assertEqual(before, (self.base / E.MANIFEST).read_bytes())
        self.assertEqual(E.status(self.base)["stages"]["fuentes"], "complete")
        self.evidence("evidence/fuentes.txt", "cambio")
        self.assertEqual(E.status(self.base)["stages"]["fuentes"], "stale")

    def test_skipping_stages_blocked(self):
        with self.assertRaisesRegex(ValueError, "Etapas pendientes"):
            E.register(self.base, "video", self.report("video"))

    def test_seed_brief_is_not_marked_finished(self):
        self.seed_complete("demanda")
        result = E.prepare_brief(self.base)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(E.status(self.base)["next"], "brief")
        self.evidence(".encargo/brief.md", "BRIEF EDITADO")
        E.prepare_brief(self.base)
        self.assertEqual((self.base / ".encargo/brief.md").read_text(), "BRIEF EDITADO")

    def test_negative_demand_blocks_editorial_production(self):
        self.seed_complete("demanda")
        demand = {"fetched_at": E.utc(), "topic_analysis": {"verdict": "NO - ES DE LOS MEDIOS"}}
        E.write_json(self.base / ".encargo/demanda.json", demand)
        data = E.load(self.base)
        data["stages"]["demanda"]["artifacts"] = [E.artifact(self.base, ".encargo/demanda.json")]
        E.save(self.base, data)
        with self.assertRaisesRegex(ValueError, "descarta"):
            E.register(self.base, "brief", self.report("brief"))

    def test_script_needs_human_approval_then_detects_edit(self):
        self.seed_complete("guion")
        self.assertEqual(E.status(self.base)["stages"]["backup"], "blocked_approval")
        proof = self.evidence("aprobacion_guion.txt", "Agustin aprobo este guion en la conversacion.")
        E.approve(self.base, "guion", "Agustin", proof)
        self.assertTrue(E.approval_valid(self.base, E.load(self.base), "guion"))
        self.evidence("evidence/guion.txt", "otro guion")
        self.assertFalse(E.approval_valid(self.base, E.load(self.base), "guion"))
        with self.assertRaises(ValueError):
            E.register(self.base, "backup", self.report("backup"))

    def test_script_approval_tracks_real_script_omitted_from_report(self):
        self.seed_complete("guion")
        E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion.txt"))
        data = E.load(self.base)
        self.assertTrue(E.approval_valid(self.base, data, "guion"))
        self.evidence("guion.md", "A: A different narration, not the approved one.")
        self.assertFalse(E.approval_valid(self.base, data, "guion"))

    def test_script_approval_not_invalidated_by_adding_future_media(self):
        self.seed_complete("guion")
        E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion.txt"))
        draft = E.read_json(self.base / E.PACKAGE)
        draft["long_video"]["media_path"] = self.evidence("salida/master.mp4")
        draft["packaging"]["thumbnail"]["image_path"] = self.evidence("thumb.png")
        draft["packaging"]["hook"]["evidence"] = {"frames": [{"path": self.evidence("frame0.png")}]}
        E.write_json(self.base / E.PACKAGE, draft)
        self.assertTrue(E.approval_valid(self.base, E.load(self.base), "guion"))

    def test_script_approval_requires_a_real_script_file(self):
        self.seed_complete("guion")
        (self.base / "guion.md").unlink()
        with self.assertRaisesRegex(ValueError, "Falta evidencia"):
            E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion.txt"))

    def test_no_human_qc_without_all_deliverables(self):
        self.seed_complete("guion")
        proof = self.evidence("aprobacion.txt")
        with self.assertRaises(ValueError):
            E.approve(self.base, "qc_humano", "Agustin", proof)
        with self.assertRaises(ValueError):
            E.approve(self.base, "guion", "modelo", proof)

    def test_full_state_machine_ends_at_human_qc_not_publish(self):
        self.seed_complete("guion")
        proof = self.evidence("aprobacion_guion.txt", "Decision humana de prueba")
        E.approve(self.base, "guion", "Agustin", proof)
        for stage in E.STAGES[E.STAGES.index("backup"):E.STAGES.index("qc_humano")]:
            E.register(self.base, stage, self.report(stage))
        self.assertEqual(E.status(self.base)["next"], "qc_humano")
        final = self.evidence("aprobacion_final.txt", "Decision humana de prueba")
        E.approve(self.base, "qc_humano", "Agustin", final)
        result = E.status(self.base)
        self.assertIsNone(result["next"])
        self.assertTrue(result["human_approval_valid"])
        self.assertFalse(result["publish_allowed"])
        self.evidence("evidence/video.txt", "La entrega cambio despues de aprobada")
        self.assertFalse(E.status(self.base)["human_approval_valid"])

    def test_qc_closes_all_package_files_even_when_report_omits_them(self):
        draft = E.read_json(self.base / E.PACKAGE)
        paths = ["salida/master.mp4", "thumb.png", "frame0.png", "audio.wav", "fuentes/proof.json",
                 "shorts/one/video.mp4", "shorts/one/thumb.png", "shorts/one/guion.md"]
        for path in paths:
            self.evidence(path, "original " + path)
        draft["long_video"]["media_path"] = paths[0]
        draft["packaging"]["thumbnail"]["image_path"] = paths[1]
        draft["packaging"]["hook"]["evidence"] = {
            "video_path": paths[0], "frames": [{"path": paths[2]}], "audio": {"path": paths[3]}}
        draft["sources"] = [{"id": "F1", "evidence_path": paths[4]}]
        draft["shorts"] = [{"media_path": paths[5], "script_path": paths[7],
                            "packaging": {"thumbnail": {"image_path": paths[6]}}}]
        E.write_json(self.base / E.PACKAGE, draft)
        self.seed_complete("guion")
        E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion_guion.txt"))
        for stage in E.STAGES[E.STAGES.index("backup"):E.STAGES.index("qc_humano")]:
            E.register(self.base, stage, self.report(stage))
        records = E.load(self.base)["stages"]["qc_tecnico"]["artifacts"]
        for path in paths + ["guion.md"]:
            self.assertIn(path, [item["path"] for item in records])
        self.assertEqual(len([item for item in records if item["path"] == paths[0]]), 1)
        E.approve(self.base, "qc_humano", "Agustin", self.evidence("aprobacion_final.txt"))
        self.assertTrue(E.status(self.base)["human_approval_valid"])
        for path in paths + ["guion.md"]:
            with self.subTest(path=path):
                original = (self.base / path).read_bytes()
                self.evidence(path, "sustituido sin cambiar el JSON")
                result = E.status(self.base)
                self.assertFalse(result["human_approval_valid"])
                self.assertNotEqual(result["stages"]["qc_tecnico"], "complete")
                (self.base / path).write_bytes(original)
        self.assertTrue(E.status(self.base)["human_approval_valid"])

    def test_qc_package_closure_rejects_path_escape(self):
        outside = self.root / "outside.mp4"
        outside.write_bytes(b"media fuera de la produccion")
        with self.assertRaisesRegex(ValueError, "fuera de la produccion"):
            E.package_files(self.base, {"long_video": {"media_path": str(outside)}})

    def test_qc_requires_upload_kit_not_only_editorial_package(self):
        self.patch_upload.stop()
        try:
            self.seed_complete("guion")
            E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion.txt"))
            for stage in E.STAGES[E.STAGES.index("backup"):E.STAGES.index("qc_tecnico")]:
                E.register(self.base, stage, self.report(stage))
            with self.assertRaisesRegex(ValueError, "Falta upload_kit_path"):
                E.register(self.base, "qc_tecnico", self.report("qc_tecnico"))
        finally:
            self.patch_upload.start()

    def test_upload_kit_nested_files_are_in_qc_closure(self):
        self.evidence("kit.json", json.dumps({"master": {"path": "master.mp4"},
                                             "candidates": [{"thumbnail_path": "mini.png"}]}))
        self.evidence("master.mp4")
        self.evidence("mini.png")
        self.evidence("SUBIR.md")
        paths = E.package_files(self.base, {"upload_kit_path": "kit.json", "upload_guide_path": "SUBIR.md"})
        self.assertEqual(set(paths), {"kit.json", "SUBIR.md", "master.mp4", "mini.png"})

    def test_upload_gate_checks_each_short_master_and_guide(self):
        from produccion import paquete_subida as P
        self.patch_upload.stop()
        try:
            for path in ("master.mp4", "short.mp4", "mini.png", "short.png"):
                self.evidence(path)
            self.evidence("SUBIR.md", "GUIDE")
            self.evidence("short/SUBIR.md", "GUIDE")
            self.evidence("kit.json", json.dumps({"format": "largo", "master": {"path": "master.mp4"},
                                                 "candidates": [{"thumbnail_path": "mini.png"}]}))
            self.evidence("short/kit.json", json.dumps({"format": "short", "master": {"path": "short.mp4"},
                                                       "candidates": [{"thumbnail_path": "short.png"}]}))
            package_data = {"episode": {"format": "largo"}, "long_video": {"media_path": "master.mp4"},
                            "upload_kit_path": "kit.json", "shorts": [{"media_path": "short.mp4",
                            "upload_kit_path": "short/kit.json", "upload_guide_path": "short/SUBIR.md"}]}
            checker = SimpleNamespace(validar=lambda *a, **kw: {"ok": True}, local_path=P.local_path,
                                      markdown=lambda *a: "GUIDE", artifact_paths=P.artifact_paths)
            with mock.patch.object(E.importlib, "import_module", return_value=checker):
                paths = E.upload_files_for_qc(self.base, package_data)
                self.assertIn("short.mp4", paths)
                self.assertIn("short.png", paths)
                self.evidence("short/SUBIR.md", "STALE")
                with self.assertRaisesRegex(ValueError, "no corresponde al manifiesto"):
                    E.upload_files_for_qc(self.base, package_data)
                self.evidence("short/SUBIR.md", "GUIDE")
                package_data["shorts"][0]["media_path"] = "master.mp4"
                with self.assertRaisesRegex(ValueError, "otro master"):
                    E.upload_files_for_qc(self.base, package_data)
                package_data["shorts"][0].pop("upload_kit_path")
                with self.assertRaisesRegex(ValueError, "pieza 1"):
                    E.upload_files_for_qc(self.base, package_data)
        finally:
            self.patch_upload.start()

    def test_legacy_qc_approval_without_media_closure_is_not_valid(self):
        draft = E.read_json(self.base / E.PACKAGE)
        draft["long_video"]["media_path"] = self.evidence("salida/master.mp4")
        E.write_json(self.base / E.PACKAGE, draft)
        data = E.load(self.base)
        data["approvals"]["qc_humano"] = {"artifacts": [E.artifact(self.base, E.PACKAGE)]}
        self.assertFalse(E.approval_valid(self.base, data, "qc_humano"))

    def test_packaging_hash_ignores_later_media_but_not_promise(self):
        record = E.artifact(self.base, E.PACKAGE, scope="design")
        data = E.read_json(self.base / E.PACKAGE)
        data["long_video"]["media_path"] = "salida/largo.mp4"
        data["packaging"]["thumbnail"]["image_path"] = "miniatura.png"
        data["packaging"]["hook"]["evidence"] = {"frames": ["00.png"]}
        E.write_json(self.base / E.PACKAGE, data)
        self.assertTrue(E.unchanged(self.base, record))
        self.assertEqual(record, E.artifact(self.base, E.PACKAGE, scope="design"))
        data["packaging"]["promise"]["question"] = "A different promise?"
        E.write_json(self.base / E.PACKAGE, data)
        self.assertFalse(E.unchanged(self.base, record))

    def test_freshness_requires_aware_recent_not_future(self):
        self.assertTrue(E.fresh(E.utc()))
        self.assertFalse(E.fresh((E.now() - timedelta(hours=25)).isoformat()))
        self.assertFalse(E.fresh((E.now() + timedelta(minutes=2)).isoformat()))
        self.assertFalse(E.fresh("2026-09-16T12:00:00"))

    def test_escalera_broken_anchor_and_unresolved_are_not_ranked(self):
        module = SimpleNamespace(escalera=lambda *a: ({"a": 30, "b": 20}, {"a": 0, "b": 0},
                                                    [(["a"], {"a": 30}), (["a", "b"], {"a": 0, "b": 20})]))
        with mock.patch.object(E.importlib, "import_module", return_value=module):
            result = E.compare_terms(["a", "b", "c"], "US", "now 7-d")
        self.assertFalse(result["comparable"])
        self.assertIn("c", result["unresolved"])

    def test_trends_failure_is_persisted_not_faked(self):
        dm = SimpleNamespace(buscar_youtube=lambda *a: [])
        with mock.patch.object(E.importlib, "import_module", return_value=dm), \
                mock.patch.object(E, "compare_terms", side_effect=RuntimeError("429")):
            result = E.measure(self.base)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["comparison"])
        self.assertIsNone(result["topic_analysis"])
        self.assertEqual(E.status(self.base)["stages"]["demanda"], "blocked")
        self.assertIn("429", result["errors"][0])

    def test_slow_measure_cannot_overwrite_new_script_approval(self):
        self.seed_complete("guion")
        old = (self.base / ".encargo/demanda.json").read_bytes()

        def approve_during_query(*args):
            E.approve(self.base, "guion", "Agustin", self.evidence("aprobacion.txt"))
            return {"comparable": False, "unresolved": [], "errors": []}

        dm = SimpleNamespace(buscar_youtube=lambda *a: [])
        with mock.patch.object(E.importlib, "import_module", return_value=dm), \
                mock.patch.object(E, "compare_terms", side_effect=approve_during_query):
            with self.assertRaisesRegex(ValueError, "durante la consulta"):
                E.measure(self.base)
        self.assertEqual((self.base / ".encargo/demanda.json").read_bytes(), old)
        self.assertTrue(E.approval_valid(self.base, E.load(self.base), "guion"))

    def test_slow_measure_cannot_overwrite_new_topic(self):
        def change_during_query(*args):
            data = E.load(self.base)
            data["production"]["topic"] = "new topic"
            E.save(self.base, data)
            return {"comparable": False, "unresolved": [], "errors": []}

        dm = SimpleNamespace(buscar_youtube=lambda *a: [])
        with mock.patch.object(E.importlib, "import_module", return_value=dm), \
                mock.patch.object(E, "compare_terms", side_effect=change_during_query):
            with self.assertRaisesRegex(ValueError, "durante la consulta"):
                E.measure(self.base)
        self.assertFalse((self.base / ".encargo/demanda.json").exists())
        self.assertEqual(E.load(self.base)["production"]["topic"], "new topic")

    def test_stale_evidence_blocks_topic_selection(self):
        E.write_json(self.base / ".encargo/demanda.json", {
            "fetched_at": (E.now() - timedelta(days=2)).isoformat(),
            "comparison": {"comparable": True, "scale": {"a": 30}, "unresolved": []}})
        with self.assertRaisesRegex(ValueError, "caduco"):
            E.select_topic(self.base, "a")

    def test_writer_lock_does_not_allow_second_writer(self):
        with E.mutation_lock(self.base):
            with self.assertRaisesRegex(ValueError, "Otro proceso"):
                with E.mutation_lock(self.base):
                    self.fail("No debe entrar")

    def test_next_task_is_actionable_without_publish_or_schedule(self):
        task = E.next_task(self.base)
        self.assertIn("Mide terminos", task["task"])
        self.assertTrue(task["constraints"]["no_upload"])
        self.assertTrue(task["constraints"]["no_paid_calls"])
        self.assertTrue(Path(task["input_files"][0]).is_absolute())
        self.assertEqual(E.load(self.base)["measurement"]["baseline"], None)

    def test_real_package_contract_integration(self):
        self.patch_editorial.stop()
        try:
            target = self.root / "videos" / "11_integracion"
            E.new(target, topic="national debt")
            draft = E.read_json(target / E.PACKAGE)
            result = E.editorial().validar_empaque(draft, base_dir=target)
            self.assertFalse(result["ok"])
            self.assertFalse(result["publish_allowed"])
            self.assertFalse(result["ready_for_human_qc"])
            self.assertEqual(draft["episode"]["language"], "en")
        finally:
            self.patch_editorial.start()


if __name__ == "__main__":
    unittest.main()
