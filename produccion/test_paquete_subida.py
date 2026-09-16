"""Contrato de entrega, sin red, voz, render ni publicacion."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from PIL import Image

from produccion import paquete_subida as P


class SubidaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / "master.mp4").write_bytes(b"master de prueba, no un render")
        self.probe = mock.patch.object(P, "probe_master", return_value={
            "duration_s": 60.0, "width": 1920, "height": 1080, "fps": 24.0, "audio": True})
        self.probe.start()
        for name, color in (("A", "red"), ("B", "green"), ("C", "blue")):
            Image.new("RGB", (1280, 720), color).save(self.base / (name + ".png"))
        self.data = {"schema_version": 1, "format": "largo",
                     "master": {"path": "master.mp4", "sha256": P.sha256(self.base / "master.mp4"),
                                "duration_s": 60.0, "width": 1920, "height": 1080, "fps": 24},
                     "candidates": [{"id": name, "title": title + " #Debt #Money #USA", "thumbnail_path": name + ".png",
                                     "angle": "Specific angle " + name, "why": "Editorial rationale " + name}
                                    for name, title in (("A", "Who Pays the Debt? Follow the money."),
                                                        ("B", "Does Debt Disappear? The receipt remains."),
                                                        ("C", "Who Gets the Bill? Savers feel the cost."))],
                     "recommended": "A", "description": "A complete, evidence-led explanation.\n\n"
                     "00:00 The receipt\n00:20 The mechanism\n00:40 Who pays\n\n"
                     "Sources: https://www.imf.org/\n\n#Debt #Money #USA",
                     "tags": ["national debt", "money", "USA"], "pinned_comment": "Who pays first in your life?",
                     "chapters": [{"time": "00:00", "title": "The receipt"},
                                  {"time": "00:20", "title": "The mechanism"}, {"time": "00:40", "title": "Who pays"}],
                     "settings": {"visibility": "private", "category": "Education", "language": "en",
                                  "made_for_kids": False, "publish_at": None,
                                  "altered_content": {"decision": "review", "reason": "Verify the music provenance before selecting a setting."}},
                     "sources": [{"label": "IMF", "url": "https://www.imf.org/"}],
                     "policy": {"no_auto_publish": True, "manual_schedule": True},
                     "qc": {"status": "pending", "notes": []}}
        self.manifest = self.base / "paquete_subida.json"

    def tearDown(self):
        self.probe.stop()
        self.temp.cleanup()

    def write(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def codes(self, data=None):
        return {error["codigo"] for error in P.validar(self.data if data is None else data, self.base)["errores"]}

    def test_valid_delivery_never_allows_publish(self):
        result = P.validar(self.data, self.base)
        self.assertTrue(result["ok"], result["errores"])
        self.assertTrue(result["ready_for_human_qc"])
        self.assertFalse(result["publish_allowed"])
        self.assertEqual(self.data["qc"]["status"], "pending")
        self.assertEqual(len(result["artifacts"]), 4)

    def test_three_titles_images_and_ids_are_required(self):
        self.data["candidates"].pop()
        self.assertIn("TRES_CANDIDATOS", self.codes())
        self.data["candidates"].append(deepcopy(self.data["candidates"][0]))
        self.assertTrue({"CANDIDATO_ID", "TITULOS_REPETIDOS", "MINIATURAS_REPETIDAS"}.issubset(self.codes()))

    def test_title_formula_hashtags_and_limit(self):
        self.data["candidates"][0]["title"] = "A statement without a question #Debt #Money #USA"
        self.assertIn("TITULO_FORMULA", self.codes())
        self.data["candidates"][0]["title"] = "A question? " + "x" * 100
        self.assertIn("LIMITE_TEXTO", self.codes())
        self.data["candidates"][0]["title"] = "A question? A sentence. #Other #Tags #Here"
        self.assertIn("TITULO_HASHTAGS", self.codes())

    def test_actual_master_hash_metadata_and_audio(self):
        self.data["master"]["sha256"] = "0" * 64
        self.data["master"]["duration_s"] = 90
        self.data["master"]["fps"] = 25
        self.data["master"]["width"] = 1280
        self.assertTrue({"MASTER_HASH", "MASTER_DURACION", "MASTER_FPS", "MASTER_MEDIDA"}.issubset(self.codes()))

    def test_master_requires_real_probe(self):
        with mock.patch.object(P, "probe_master", side_effect=ValueError("video corrupto")):
            self.assertIn("FFPROBE", self.codes())

    def test_same_pixels_under_different_names_do_not_count(self):
        Image.new("RGB", (1280, 720), "red").save(self.base / "B.png", compress_level=1)
        self.assertIn("MINIATURAS_REPETIDAS", self.codes())

    def test_native_4k_thumbnails_are_accepted(self):
        Image.new("RGB", (3840, 2160), "yellow").save(self.base / "A.png")
        self.assertNotIn("MINIATURA_MEDIDA", self.codes())

    def test_small_or_wrong_aspect_thumbnail_rejected(self):
        Image.new("RGB", (640, 360), "red").save(self.base / "A.png")
        self.assertIn("MINIATURA_MEDIDA", self.codes())
        Image.new("RGB", (1280, 800), "red").save(self.base / "A.png")
        self.assertIn("MINIATURA_MEDIDA", self.codes())

    def test_mobile_weight_profile(self):
        with (self.base / "A.png").open("ab") as out:
            out.write(b"x" * P.MAX_THUMB_BYTES)
        self.assertIn("MINIATURA_PESO", self.codes())

    def test_chapters_begin_zero_order_match_description_and_last_ten_seconds(self):
        self.data["chapters"][0]["time"] = "00:01"
        self.data["chapters"][-1]["time"] = "00:55"
        self.assertTrue({"CAPITULOS_CERO", "CAPITULOS_TRAMOS", "CAPITULOS_DESCRIPCION"}.issubset(self.codes()))
        self.data["chapters"][1]["time"] = "00:99"
        self.assertIn("CAPITULO_TIEMPO", self.codes())

    def test_description_and_tags_limits_placeholders(self):
        self.data["description"] = "x" * 5001
        self.data["tags"] = ["x" * 499, "y"]
        self.assertTrue({"LIMITE_TEXTO", "ETIQUETAS_LIMITE"}.issubset(self.codes()))
        self.data["description"] = "[INSERT DESCRIPTION]"
        self.assertIn("TEXTO_INCOMPLETO", self.codes())

    def test_policy_requires_manual_private_and_explicit_ai_reason(self):
        self.data["settings"]["publish_at"] = "2026-09-20T12:00:00Z"
        self.data["settings"]["visibility"] = "public"
        self.data["settings"]["altered_content"]["reason"] = ""
        self.data["policy"]["no_auto_publish"] = False
        self.assertTrue({"SIN_CALENDARIO", "AJUSTE", "PUBLICACION_HUMANA", "TEXTO_INCOMPLETO"}.issubset(self.codes()))

    def test_paths_cannot_escape_or_be_absolute(self):
        self.data["master"]["path"] = str(self.base / "master.mp4")
        self.assertIn("ARCHIVO", self.codes())
        with self.assertRaises(ValueError):
            P.local_path(self.base, "../outside.md", False)

    def test_malformed_data_produces_errors_not_ready(self):
        for bad in (None, [], {}, {"schema_version": 1, "candidates": [None]}):
            with self.subTest(bad=bad):
                result = P.validar(bad, self.base)
                self.assertFalse(result["ok"])
                self.assertFalse(result["publish_allowed"])

    def test_short_vertical_kit_does_not_require_chapters(self):
        self.data["format"] = "short"
        self.data.pop("chapters")
        self.data["master"].update(width=1080, height=1920)
        for name, color in (("A", "red"), ("B", "green"), ("C", "blue")):
            Image.new("RGB", (1080, 1920), color).save(self.base / (name + ".png"))
        with mock.patch.object(P, "probe_master", return_value={"width": 1080, "height": 1920, "fps": 24, "duration_s": 60, "audio": True}):
            self.assertTrue(P.validar(self.data, self.base)["ok"], self.codes())

    def test_markdown_full_copy_extras_and_no_fake_qc(self):
        self.data["subtitles"] = {"language": "en", "status": "needs review"}
        self.data["end_screen"] = "Choose the related long episode manually."
        result = P.markdown(self.data, self.base)
        self.assertIn(self.data["description"], result)
        self.assertIn(str(self.base / "master.mp4"), result)
        self.assertIn("needs review", result)
        self.assertIn("Choose the related", result)
        self.assertIn("Estado declarado: pending", result)

    def test_write_is_idempotent_and_explicit_update_is_versioned(self):
        self.write()
        first = P.renderizar(self.manifest, self.base)
        original = (self.base / "SUBIR.md").read_bytes()
        self.assertTrue(first["changed"])
        self.assertFalse(P.renderizar(self.manifest, self.base)["changed"])
        self.data["recommended"] = "B"
        self.write()
        with self.assertRaisesRegex(ValueError, "--actualizar"):
            P.renderizar(self.manifest, self.base)
        self.assertEqual((self.base / "SUBIR.md").read_bytes(), original)
        update = P.renderizar(self.manifest, self.base, actualizar=True)
        self.assertEqual(Path(update["backup"]).read_bytes(), original)
        self.assertNotEqual((self.base / "SUBIR.md").read_bytes(), original)

    def test_invalid_kit_does_not_create_guide(self):
        self.data["candidates"] = []
        self.write()
        self.assertFalse(P.renderizar(self.manifest, self.base)["ok"])
        self.assertFalse((self.base / "SUBIR.md").exists())


if __name__ == "__main__":
    unittest.main()
