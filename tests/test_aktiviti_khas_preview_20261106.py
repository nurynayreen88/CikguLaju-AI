"""Read-only preview and subject-first selection for special RPH catalogue."""
import os
import unittest
from unittest.mock import patch

from flask import Flask

from rph_standalone.aktiviti_khas.engine import (
    SELEPAS, TRANSISI, _catalog, list_subjects, preview, select,
)
from web.telegram_special_activity_api import create_special_rph_blueprint


TOKEN = "T" * 40


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.digest = _catalog()

    def test_subject_list_covers_all_thirteen_for_all_years(self):
        for year in range(1, 7):
            with self.subTest(year=year):
                items, digest = list_subjects(SELEPAS, year)
                self.assertEqual(len(items), 13)
                self.assertEqual(len({x["value"] for x in items}), 13)
                self.assertEqual(digest, self.digest)
                self.assertNotIn("Semua subjek", [x["label"] for x in items])

    def test_full_preview_matches_original_record(self):
        for row in self.source["activities"]:
            with self.subTest(activity=row["id"]):
                year = row["years"][0]
                chosen_subject = (
                    row["subject_options"][0] if row["category"] == SELEPAS else None)
                actual = preview(row["category"], year, row["id"], self.digest,
                                 subject=chosen_subject)
                self.assertEqual(actual["title"], row["title"])
                self.assertEqual(actual["objective"], row["learning_objective"])
                self.assertEqual(actual["subject"],
                                 chosen_subject or "Program Transisi Tahun Satu")
                self.assertEqual(actual["duration_minutes"], 60)
                self.assertEqual(len(actual["phases"]), 6)
                self.assertEqual([x["minutes"] for x in actual["phases"]],
                                 [5, 15, 15, 15, 5, 5])
                self.assertEqual(
                    [x["activity"] for x in actual["phases"][1:4]],
                    row["aktiviti_utama"])
                self.assertFalse(actual["official_sk_sp_attached"])
                self.assertNotIn("SK", actual)
                self.assertNotIn("SP", actual)
                self.assertEqual(actual["status"], "DRAFT_REVIEW")

    def test_subject_crossovers_fail(self):
        row = select(SELEPAS, 6, "S03C", self.digest)
        self.assertEqual(row["subject_options"], ["Matematik"])
        with self.assertRaises(ValueError):
            preview(SELEPAS, 6, "S03C", self.digest, subject="Bahasa Melayu")
        with self.assertRaises(ValueError):
            preview(SELEPAS, 6, "S03C", self.digest)
        with self.assertRaises(ValueError):
            preview(TRANSISI, 1, "K01", self.digest, subject="Matematik")

    def test_stale_identity_is_blocked(self):
        from rph_standalone.aktiviti_khas.engine import SourceUnavailable
        with self.assertRaises(SourceUnavailable):
            preview(SELEPAS, 6, "S03C", "0" * 64, subject="Matematik")


class ProtectedRoutesTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_special_rph_blueprint())
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer " + TOKEN}
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": TOKEN,
            "CIKGULAJU_SPECIAL_RPH_ENABLED": "1",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_private_subjects_and_preview(self):
        path = "/internal/rph/v1/aktiviti-khas"
        denied = self.client.get(path + "/subjects?kind=SELEPAS_TAMAT_SUKATAN&year=6")
        self.assertEqual(denied.status_code, 401)
        r = self.client.get(path + "/subjects?kind=SELEPAS_TAMAT_SUKATAN&year=6",
                            headers=self.headers)
        self.assertEqual(r.status_code, 200)
        subjects = r.get_json()
        self.assertEqual(len(subjects["items"]), 13)
        self.assertEqual(r.headers["Cache-Control"], "private, no-store")
        opts = self.client.get(
            path + "/options?kind=SELEPAS_TAMAT_SUKATAN&year=6&subject=Matematik",
            headers=self.headers)
        self.assertEqual(opts.status_code, 200)
        options = opts.get_json()
        self.assertEqual(len(options["items"]), 1)
        self.assertEqual(options["items"][0]["id"], "S03C")
        prev = self.client.get(
            path + "/preview?kind=SELEPAS_TAMAT_SUKATAN&year=6"
            + "&activity_id=S03C&source_digest=" + options["source_digest"]
            + "&subject=Matematik", headers=self.headers)
        self.assertEqual(prev.status_code, 200)
        data = prev.get_json()
        self.assertEqual(data["title"], "Pasar Mini: Wang, Operasi dan Bajet")
        self.assertEqual(len(data["phases"]), 6)
        self.assertFalse(data["official_sk_sp_attached"])

    def test_wrong_subject_and_source_fail_closed(self):
        path = "/internal/rph/v1/aktiviti-khas"
        digest = _catalog()[1]
        for query, expected in (
            ("options?kind=SELEPAS_TAMAT_SUKATAN&year=6&subject=Semua", 400),
            ("subjects?kind=TRANSISI_TAHUN_1&year=1", 400),
            ("preview?kind=SELEPAS_TAMAT_SUKATAN&year=6&activity_id=S03C"
             + "&subject=Sejarah&source_digest=" + digest, 400),
            ("preview?kind=SELEPAS_TAMAT_SUKATAN&year=6&activity_id=S03C"
             + "&subject=Matematik&source_digest=" + "0" * 64, 409),
            ("preview?kind=TRANSISI_TAHUN_1&year=2&activity_id=K01"
             + "&source_digest=" + digest, 400),
        ):
            with self.subTest(query=query):
                r = self.client.get(path + "/" + query, headers=self.headers)
                self.assertEqual(r.status_code, expected)


if __name__ == "__main__":
    unittest.main()
