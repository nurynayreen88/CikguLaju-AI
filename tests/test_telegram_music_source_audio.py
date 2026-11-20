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
            state={year: {"year": f"Tahun {year}"} for year in range(2, 7)},
            send=send,
        )
        self.assertTrue(install(runtime))
        self.assertEqual(runtime.callback(4, "home"), ("previous", 4, "home"))
        for year in range(2, 7):
            _, message, menu = runtime.callback(year, SUBJECT_MENU)
            self.assertIn(f"Tahun {year}", message)
            self.assertEqual(menu[-2][-1]["callback_data"], f"muzik-audio:menu:{year}:1")
        wrong = "muzik-audio:pdp:4:21"
        self.assertEqual(runtime.callback(3, wrong), ("previous", 3, wrong))
        for lesson, tracks in ((21, [66, 67]), (24, [90, 91, 92])):
            _, message, buttons = runtime.callback(4, f"muzik-audio:pdp:4:{lesson}")
            self.assertIn("memuat turun", message)
            self.assertEqual([int(row[0]["text"].split()[2]) for row in buttons[:-1]], tracks)
            self.assertTrue(all(row[0]["url"].startswith("https://drive.usercontent.google.com/download?")
                                for row in buttons[:-1]))
        self.assertEqual(runtime.state[4], {"year": "Tahun 4"})

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
                for item in result.json["links"]:
                    file_id = item["url"].split("/")[5]
                    self.assertEqual(item["download_url"],
                        f"https://drive.usercontent.google.com/download?id={file_id}&export=download")

    def test_download_audit_applies_to_exact_year_and_pdp(self):
        counts = {2:20, 3:23, 4:19, 5:28, 6:27}
        source_files = set()
        for year, expected in counts.items():
            matched = 0
            for number in range(1, 36):
                links = audio_link_action(year, number)["links"]
                verified = [item for item in links if "download_url" in item]
                if verified:
                    self.assertEqual(verified, links)
                    matched += 1
                    source_files.update(item["file_id"] for item in verified)
            self.assertEqual(matched, expected)
        self.assertEqual(len(source_files), 571)

    def test_other_pdp_and_changed_file_ids_are_not_verified(self):
        self.assertFalse(audio_link_action(4, 20)["content_verified"])
        with patch("staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging.links_for_pdp",
                   return_value=[{"track": 66, "file_id": "different"}]):
            result = audio_link_action(4, 21)
            self.assertFalse(result["content_verified"])
            self.assertFalse(result["available"])
