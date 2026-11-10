"""Y6 ratio/cadangan source hold — no DB, payments, quotas or file writes.

KPM DSKP Mathematics Y6 (Sep 2021) p56: 7.2.1 Nisbah, 7.3.1
Kadaran, 7.4.1 masalah; topic 8 is Data/Kebolehjadian.
"""
import os
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from flask import Flask

from web.math_y6_ratio_source_hold_20261110 import held_math_y6_ratio_source
from web.telegram_verified_sequence_rph_bridge import (
    _resolve, _unit_token, create_native_sequence_rph_blueprint,
)
from web.telegram_verified_rpt_rph_bridge import SourceUnavailable


UNIT = "Nisbah dan Kadaran"
KEY = _unit_token("8", UNIT)
BAD = {
    "MT6-PDP-079": ("Nisbah", "8.1.1"),
    "MT6-PDP-080": ("Kadaran", "8.2.1"),
    "MT6-PDP-081": ("Penyelesaian Masalah Nisbah dan Kadaran", "8.3.1"),
    "MT6-PDP-082": ("Pengukuhan Nisbah dan Kadaran", "8.1.1;8.2.1;8.3.1"),
    "MT6-PDP-083": ("Aplikasi Nisbah dan Kadaran", "8.1.1;8.2.1"),
    "MT6-PDP-084": ("Penyelesaian Masalah Bukan Rutin Nisbah dan Kadaran", "8.3.1"),
}


def row(code, title, sp):
    return {
        "unit_code": "8", "unit_title": UNIT,
        "pdp_sequence_code": code,
        "source_sequence_no": int(code.rsplit("-", 1)[1]),
        "pdp_title": title,
        "sk_code": ";".join(sorted({part.rsplit(".", 1)[0] for part in sp.split(";")})),
        "sp_code": sp,
        "sk_text": "source", "sp_text": "source",
        "textbook_ref": "", "activitybook_ref": "",
    }


def fixtures():
    return [row(code, title, sp) for code, (title, sp) in BAD.items()]


def fake_runtime(all_rows, output_calls):
    def commit(state, mapped):
        state["grouped_sp_codes"] = [r["sp_code"] for r in mapped]
        state["sp_code"] = mapped[0]["sp_code"]
        state["sk_code"] = mapped[0]["sk_code"]

    def no_output(*args):
        output_calls.append(args)
        raise AssertionError("Held RPH must not be rendered")

    return SimpleNamespace(
        CIKGULAJU_DB_V2600_ACTIVE=True,
        _sm2542_rows=lambda year, subject: all_rows,
        _sm2542_unique_units=lambda rows: [("8", UNIT)],
        _commit_multi_sp=commit,
        _local_rph_text=lambda s: "RPH khusus SK/SP " + "Aktiviti guru dan murid. " * 40,
        create_word_file=no_output,
        create_pdf_file=no_output,
    )


class Year6RatioHoldTests(unittest.TestCase):
    def test_exact_six_held_from_curated_legacy_source(self):
        rows = fixtures()
        self.assertEqual(len(rows), 6)
        for source in rows:
            self.assertTrue(held_math_y6_ratio_source(
                6, "MATH", source["pdp_sequence_code"], [source]))
            self.assertFalse(held_math_y6_ratio_source(
                5, "MATH", source["pdp_sequence_code"], [source]))
            self.assertFalse(held_math_y6_ratio_source(
                6, "SCIENCE", source["pdp_sequence_code"], [source]))
        combined = fixtures()[3]
        self.assertTrue(held_math_y6_ratio_source(
            6, "MATH", "MT6-PDP-082", [combined]))
        self.assertTrue(held_math_y6_ratio_source(
            6, "MATH", "MT6-PDP-082", [
                row("MT6-PDP-082", "Pengukuhan", "8.1.1"),
                row("MT6-PDP-082", "Pengukuhan", "8.2.1"),
                row("MT6-PDP-082", "Pengukuhan", "8.3.1")]))
        self.assertFalse(held_math_y6_ratio_source(
            6, "MATH", "MT6-PDP-082", [
                row("MT6-PDP-082", "Pengukuhan", "8.1.1"),
                row("MT6-PDP-083", "Aplikasi", "8.2.1")]))

    def test_corrected_dskp_codes_automatically_restore_eligibility(self):
        corrected = [
            ("MT6-PDP-079", "7.2.1"),
            ("MT6-PDP-080", "7.3.1"),
            ("MT6-PDP-081", "7.4.1"),
            ("MT6-PDP-082", "7.2.1;7.3.1;7.4.1"),
            ("MT6-PDP-083", "7.2.1;7.3.1"),
            ("MT6-PDP-084", "7.4.1"),
        ]
        for code, sp in corrected:
            with self.subTest(code=code):
                self.assertFalse(held_math_y6_ratio_source(
                    6, "MATH", code, [row(code, BAD[code][0], sp)]))
        # Other source lesson IDs, even with the same 8.x codes, are not
        # blacklisted as these may correctly teach data/probability.
        safe = row("MT6-PDP-085", "Carta pai", "8.1.1")
        self.assertFalse(held_math_y6_ratio_source(6, "MATH", "MT6-PDP-085", [safe]))

    def test_native_resolution_filters_only_six_wrong_legacy_pdp(self):
        available = fixtures() + [
            row("MT6-PDP-085", "Carta pai", "8.1.1"),
        ]
        rt = fake_runtime(available, [])
        _, group = _resolve(rt, 6, "MATH", KEY)
        self.assertEqual(set(group), {"MT6-PDP-085"})
        for code in BAD:
            with self.subTest(code=code), self.assertRaises(SourceUnavailable):
                _resolve(rt, 6, "MATH", KEY, code)
        result = _resolve(rt, 6, "MATH", KEY, "MT6-PDP-085")
        self.assertEqual(result[2][0]["sp_code"], "8.1.1")
        # Year 5 remains available even though this fixture is only for
        # checking that no Year 6-specific hold leaks to other years.
        _, year5_group = _resolve(rt, 5, "MATH", KEY)
        self.assertEqual(len(year5_group), 7)
        _, science_group = _resolve(rt, 6, "SCIENCE", KEY)
        self.assertEqual(len(science_group), 7)

    def test_real_private_flask_route_hides_six_and_blocks_old_links(self):
        rendered = []
        rt = fake_runtime(fixtures() + [
            row("MT6-PDP-085", "Carta pai", "8.1.1"),
        ], rendered)
        app = Flask("math-y6-ratio-hold")
        app.register_blueprint(create_native_sequence_rph_blueprint(rt))
        client = app.test_client()
        secret = "test-internal-source-secret-" + "a" * 40
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": secret,
        }):
            auth = {"Authorization": "Bearer " + secret}
            query = {"year": "6", "subject": "MATH", "unit": KEY}
            choices = client.get("/internal/rph/v1/sequence/lessons",
                                 query_string=query, headers=auth)
            self.assertEqual(choices.status_code, 200)
            self.assertEqual([x["value"] for x in choices.json["items"]],
                             ["MT6-PDP-085"])
            for code in BAD:
                with self.subTest(code=code):
                    old = {**query, "lesson": code}
                    availability = client.get(
                        "/internal/rph/v1/sequence/availability",
                        query_string=old, headers=auth)
                    self.assertEqual(availability.status_code, 404)
                    self.assertFalse(availability.json["available"])
                    for fmt in ("word", "pdf"):
                        attempt = client.post(
                            "/internal/rph/v1/sequence/render",
                            json={
                                "selection": {"year": 6, "subject": "MATH",
                                              "unit": KEY, "lesson": code},
                                "teacher": {
                                    "class": "6 Ikhlas", "date": "2026-11-10",
                                    "time": "08:00 - 09:00", "students": "30",
                                },
                                "format": fmt,
                            }, headers=auth)
                        self.assertEqual(attempt.status_code, 404)
                        self.assertNotIn(b"%PDF-", attempt.data)
                        self.assertNotIn(b"PK\x03\x04", attempt.data)
            self.assertEqual(rendered, [])
            public = client.get("/internal/rph/v1/sequence/lessons",
                                query_string=query)
            self.assertEqual(public.status_code, 401)


if __name__ == "__main__":
    unittest.main()
