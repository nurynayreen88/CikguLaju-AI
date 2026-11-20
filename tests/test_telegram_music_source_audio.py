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
        counts = {2:31, 3:31, 4:34, 5:33, 6:34}
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
        self.assertEqual(len(source_files), 615)

    def test_additional_tracks_follow_the_specific_textbook_activity(self):
        expected = {
            (2, 19): [48], (2, 22): list(range(60, 67)), (2, 33): [84, 85, 86],
            (2, 25): [67, 68, 69], (2, 32): [80, 81, 82], (2, 34): [70, 71, 72],
            (2, 35): [84, 85, 86], (3, 34): [60, 63],
            (3, 2): [8], (3, 3): [5, 8],
            (4, 7): [17, 18], (4, 14): [44, 45, 46, 47], (4, 15): [48],
            (4, 12): [14, 16, 24, 26], (4, 13): [14, 16, 24, 26],
            (4, 34): [117], (4, 35): [49, 68, 85],
            (4, 16): [48], (4, 17): list(range(49, 58)), (4, 18): [58, 59, 60],
            (4, 31): list(range(110, 117)), (4, 32): [117], (4, 33): [117],
            (5, 5): [22], (5, 15): list(range(49, 55)), (5, 16): list(range(49, 55)),
            (5, 34): [137, 138, 139, 150, 151, 158, 159, 160, 161],
            (5, 35): [137, 138, 139, 150, 151, 158, 159, 160, 161], (6, 18): [96],
            (6, 12): [74, 76, 86], (6, 13): [74, 76, 86],
            (6, 26): [89, 91, 139, 141, 162], (6, 27): [89, 91, 139, 141, 162],
            (6, 34): [94, 95], (6, 35): [71, 72, 73],
        }
        for (year, number), tracks in expected.items():
            with self.subTest(year=year, pdp=number):
                items = audio_link_action(year, number)["links"]
                self.assertEqual([item["track"] for item in items], tracks)
                self.assertTrue(all("download_url" in item for item in items))

    def test_year_four_project_audio_uses_its_name_only_for_penggal_dua(self):
        for number in (12, 13):
            self.assertTrue(all(item["track"] for item in audio_link_action(4, number)["links"]))
        for number in (25, 26, 27):
            item, = audio_link_action(4, number)["links"]
            self.assertIsNone(item["track"])
            self.assertEqual(item["title"], "Audio Projek Kesenian Penggal Dua")
            self.assertIn("id=1zouWfTYxs4ziN0KARob6Aln2m7K7qIEM&", item["download_url"])

    def test_project_audio_variants_keep_their_verified_titles(self):
        for pdp, song in ((12, "Serangga"), (24, "Kau Sahabatku")):
            links = audio_link_action(3, pdp)["links"]
            self.assertEqual([item["title"] for item in links],
                             [f"{version} {song}" for version in ("Vokal", "Instrumental", "Minus One")])
            self.assertTrue(all(item["track"] is None and item.get("download_url") for item in links))

    def test_year_two_project_downloads_the_large_original_directly(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda *_: None, create_pdf_file=lambda *_: None,
                                  callback=lambda *_: None, state={2: {"year": "Tahun 2"}},
                                  send=lambda _chat, message, buttons: (message, buttons))
        app.register_blueprint(create_provisional_subjects_blueprint(runtime))
        self.assertTrue(install(runtime))
        token = "a" * 40
        file_id = "10FcxBIgawrIMalOIj7-CqVMJ8iVd-f1a"
        viewer = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
        download = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        with patch.dict(os.environ, {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                     "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            for number in (26, 27):
                lesson = f"{number:03d}"
                unit, = [row["value"] for row in _unit_rows(2, "MUZIK")
                         if lesson in {p["value"] for p in _lesson_rows(2, "MUZIK", row["value"])}]
                result = app.test_client().get("/internal/rph/v1/other-drafts/audio-links",
                    query_string={"year": 2, "subject": "MUZIK", "unit": unit, "lesson": lesson},
                    headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(result.status_code, 200, result.json)
                self.assertEqual(result.json["links"], [{"title": "Audio Projek Penggal Dua — Permainya Negaraku",
                    "url": viewer, "track": None, "download_url": download}])
                message, buttons = runtime.callback(2, f"muzik-audio:pdp:2:{number}")
                self.assertIn("memuat turun", message)
                self.assertEqual(buttons[0][0]["url"], download)
        with patch("staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging.links_for_pdp",
                   return_value=[{"track": None, "file_id": "different"}]):
            self.assertFalse(audio_link_action(2, 26)["available"])

    def test_other_pdp_and_changed_file_ids_are_not_verified(self):
        self.assertFalse(audio_link_action(4, 20)["content_verified"])
        with patch("staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging.links_for_pdp",
                   return_value=[{"track": 66, "file_id": "different"}]):
            result = audio_link_action(4, 21)
            self.assertFalse(result["content_verified"])
            self.assertFalse(result["available"])
