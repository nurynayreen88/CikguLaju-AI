"""Exercise the Year 1 KSSR reference overlay with the canonical source."""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from web.math_sk_year1_kssr_references import install
from web.telegram_verified_sequence_rph_bridge import (
    _build_state, create_native_sequence_rph_blueprint,
)


class MathSKYear1ReferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        work = tempfile.TemporaryDirectory()
        cls.addClassCleanup(work.cleanup)
        database = Path(work.name) / "canonical.db"
        root = Path(__file__).resolve().parents[1]
        prefix = "CikguLaju_Curriculum_Master_v25_99_MATH_T1_T6_CANONICAL"
        with database.open("wb") as target:
            for index in range(3):
                with (root / f"{prefix}.part{index:02}").open("rb") as source:
                    shutil.copyfileobj(source, target)
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            cls.source = [dict(row) for row in connection.execute("""
                SELECT * FROM verified_pdp_sequence_v2
                  WHERE year_label = 'Tahun 1' AND subject = 'Matematik'
                ORDER BY source_sequence_no, id
            """)]

    def setUp(self):
        def commit(state, mapped):
            state.update(mapped[0], grouped_sp_codes=[r["sp_code"] for r in mapped])

        def unexpected(*args):
            raise AssertionError("Listing must complete before rendering")

        self.runtime = SimpleNamespace(
            CIKGULAJU_DB_V2600_ACTIVE=True,
            _sm2542_rows=lambda year, subject: self.source,
            _sm2542_unique_units=lambda rows: list(dict.fromkeys(
                (r["unit_code"], r["unit_title"]) for r in rows)),
            _commit_multi_sp=commit, _local_rph_text=unexpected,
            create_word_file=unexpected, create_pdf_file=unexpected,
        )
        install(self.runtime)

    def test_canonical_rows_keep_identity_and_receive_checked_references(self):
        result = self.runtime._sm2542_rows("Tahun 1", "Matematik")
        self.assertEqual(len(result), 56)
        keys = ("unit_code", "unit_title", "pdp_sequence_code", "sk_code", "sp_code")
        self.assertEqual([tuple(r[k] for k in keys) for r in self.source],
                         [tuple(r[k] for k in keys) for r in result])
        self.assertEqual(len({row["pdp_title"] for row in result}), 56)
        self.assertTrue(all(r["textbook_ref"] and r["activitybook_ref"] for r in result))
        self.assertTrue(all(r["textbook_ref"] is None and r["activitybook_ref"] is None for r in self.source))
        self.assertIs(self.runtime._sm2542_rows("Tahun 2", "Matematik"), self.source)
        self.assertIs(self.runtime._sm2542_rows("Tahun 1", "Sains"), self.source)

    def test_stale_id_with_different_sp_and_reviewed_values_preserved(self):
        original = self.source[0]
        changed = dict(original, sp_code="1.2.1")
        reviewed = dict(original, textbook_ref="Reviewed TB", activitybook_ref="Reviewed BA", pdp_title="Reviewed title")
        runtime = SimpleNamespace(_sm2542_rows=lambda year, subject: [changed, reviewed])
        install(runtime)
        self.assertEqual(runtime._sm2542_rows("Tahun 1", "Matematik"), [changed, reviewed])

    def test_runtime_without_native_maths_still_starts(self):
        runtime = SimpleNamespace()
        install(runtime)
        self.assertFalse(hasattr(runtime, "_sm2542_rows"))

    def test_web_options_keep_one_unit_one_and_both_references(self):
        app = Flask(__name__)
        app.register_blueprint(create_native_sequence_rph_blueprint(self.runtime))
        client = app.test_client()
        prefix = "/internal/rph/v1/sequence"
        secret = "simulated-canonical-maths-legacy-references-secret"
        headers = {"Authorization": "Bearer " + secret}
        query = {"year": 1, "subject": "MATH"}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": secret}):
            response = client.get(prefix + "/units", headers=headers, query_string=query)
            self.assertEqual(response.status_code, 200)
            units = response.json["items"]
            self.assertEqual(len(units), 8)
            self.assertEqual(sum(row["label"].startswith("1.0 • ") for row in units), 1)
            lengths = []
            for unit in units:
                result = client.get(prefix + "/lessons", headers=headers,
                                    query_string=query | {"unit": unit["value"]})
                self.assertEqual(result.status_code, 200)
                lengths.append(len(result.json["items"]))
                self.assertTrue(all(row.get("textbook_ref") and row.get("activitybook_ref")
                                    for row in result.json["items"]))
            self.assertEqual(lengths, [13, 11, 2, 6, 8, 4, 9, 3])
            teacher = {"class": "Bestari", "date": "2026-11-19",
                       "time": "08:00 - 08:30", "students": "28"}
            state = _build_state(self.runtime, 1, "MATH", units[1]["value"], "PDP24", teacher)
            self.assertEqual(state["sp_code"], "2.6.2")
            self.assertEqual(state["textbook_ref"], "Buku Teks Jilid 1, hlm. 111–113")
            self.assertEqual(state["activitybook_ref"], "Buku Aktiviti Jilid 1, hlm. 120–122")
