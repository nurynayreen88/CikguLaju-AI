import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from flask import Flask

from staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging import audio_link_action
from web.telegram_music_source_audio import SUBJECT_MENU, install
from web.telegram_provisional_arab_music_api import (
    _lesson_rows, _unit_rows, create_provisional_subjects_blueprint,
)


class MusicSourceAudioTest(unittest.TestCase):
    def test_telegram_choice_uses_original_urls_without_rph_generation(self):
        def send(cid, message, buttons):
            return cid, message, buttons

        runtime = SimpleNamespace(
            callback=lambda cid, data: ("previous", cid, data),
            state={1: {"year": "Tahun 4"}, 2: {"year": "Tahun 3"}},
            send=send,
        )
        self.assertTrue(install(runtime))
        self.assertEqual(runtime.callback(2, SUBJECT_MENU), ("previous", 2, SUBJECT_MENU))
        self.assertEqual(runtime.callback(1, "home"), ("previous", 1, "home"))
        _, _, menu = runtime.callback(1, SUBJECT_MENU)
        self.assertEqual([row[0]["callback_data"] for row in menu[:-1]],
                         ["muzik-audio-y4:21", "muzik-audio-y4:24"])
        for lesson, tracks in ((21, [66, 67]), (24, [90, 91, 92])):
            _, message, buttons = runtime.callback(1, f"muzik-audio-y4:{lesson}")
            self.assertIn("sepadan dengan skor", message)
            self.assertEqual([int(row[0]["text"].split()[1]) for row in buttons[:-1]], tracks)
            self.assertTrue(all(row[0]["url"].startswith("https://drive.google.com/file/d/")
                                for row in buttons[:-1]))
        self.assertEqual(runtime.state[1], {"year": "Tahun 4"})

    def test_web_source_uses_exact_lesson_selection(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda *_: None, create_pdf_file=lambda *_: None)
        app.register_blueprint(create_provisional_subjects_blueprint(runtime))
        client = app.test_client()
        path = "/internal/rph/v1/other-drafts/audio-links"
        token = "a" * 40
        with patch.dict(os.environ, {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                     "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            self.assertEqual(client.get(path).status_code, 401)
            for number, tracks in ((21, [66, 67]), (24, [90, 91, 92])):
                lesson = f"{number:03d}"
                unit, = [row["value"] for row in _unit_rows(4, "MUZIK")
                         if lesson in {p["value"] for p in _lesson_rows(4, "MUZIK", row["value"])}]
                result = client.get(path, query_string={
                    "year": 4, "subject": "MUZIK", "unit": unit, "lesson": lesson,
                }, headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(result.status_code, 200, result.json)
                self.assertTrue(result.json["content_verified"])
                self.assertFalse(result.json["download_available"])
                self.assertEqual([item["track"] for item in result.json["links"]], tracks)

    def test_other_pdp_and_changed_file_ids_are_not_verified(self):
        self.assertFalse(audio_link_action(4, 20)["content_verified"])
        with patch("staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging.links_for_pdp",
                   return_value=[{"track": 66, "file_id": "different"}]):
            result = audio_link_action(4, 21)
            self.assertFalse(result["content_verified"])
            self.assertFalse(result["available"])
