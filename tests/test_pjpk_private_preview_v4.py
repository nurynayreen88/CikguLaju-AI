"""End-to-end offline checks for all-year private PJPK draft preview."""
import csv
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pjpk_private_menu import list_menu_rows
from pjpk_rph_engine import generate
from preview_server import DB, QUARANTINE, home, pdf
from pjpk_private_same_bot_v4 import install

ROOT = Path(__file__).resolve().parents[1]

class PJPKPrivatePreviewV4Tests(unittest.TestCase):
    def test_all_year_menu_and_quarantine_are_exact(self):
        rows = list_menu_rows(DB)
        self.assertEqual(len(rows), 161)
        statuses = {}
        for row in rows:
            statuses[row["entry_status"]] = statuses.get(row["entry_status"], 0) + 1
        self.assertEqual(statuses, {
            "REVIEW_ONLY": 147,
            "ANCHOR_NOT_PDP": 13,
            "SOURCE_CONFLICT_BLOCKED": 1,
        })
        self.assertEqual(len(QUARANTINE), 10)
        eligible = [r for r in rows if r["entry_status"] == "REVIEW_ONLY" and r["entry_id"] not in QUARANTINE]
        blocked = [r for r in rows if r["entry_status"] != "REVIEW_ONLY" or r["entry_id"] in QUARANTINE]
        self.assertEqual(len(eligible), 137)
        self.assertEqual(len(blocked), 24)
        self.assertEqual(len({r["entry_id"] for r in eligible}), 137)

    def test_all_137_drafts_render_and_production_stays_blocked(self):
        rows = list_menu_rows(DB)
        eligible = [r for r in rows if r["entry_status"] == "REVIEW_ONLY" and r["entry_id"] not in QUARANTINE]
        for row in eligible:
            text = generate(str(DB), row["entry_id"], mode="preview")
            self.assertIn("DRAF SEMAKAN — BUKAN RPH PRODUKSI", text)
            self.assertIn("Status: DISEKAT DARIPADA PRODUKSI", text)
        with self.assertRaises(ValueError):
            generate(str(DB), eligible[0]["entry_id"], mode="production")

    def test_all_24_blocked_records_fail_closed(self):
        rows = list_menu_rows(DB)
        blocked = [r for r in rows if r["entry_status"] != "REVIEW_ONLY" or r["entry_id"] in QUARANTINE]
        for row in blocked:
            with self.assertRaises(ValueError, msg=str(row["entry_id"])):
                generate(str(DB), row["entry_id"], mode="preview")
            with self.assertRaises(ValueError, msg="PDF " + str(row["entry_id"])):
                pdf(row["entry_id"])

    def test_pdf_output_and_menu_page(self):
        rows = list_menu_rows(DB)
        eligible = [r for r in rows if r["entry_status"] == "REVIEW_ONLY" and r["entry_id"] not in QUARANTINE]
        self.assertIn("Pratonton PJPK (BUKAN PRODUKSI)", home())
        for row in eligible:
            output = pdf(row["entry_id"])
            self.assertTrue(output.startswith(b"%PDF-"), row["entry_id"])
            self.assertGreater(len(output), 1000, row["entry_id"])

    def test_private_same_bot_access_gate_and_existing_menu_preserved(self):
        os.environ["PJPK_SAME_BOT_TESTER_IDS"] = "123"
        events = []
        class Response:
            ok = True
            def json(self):
                return {"ok": True}
        def old_subjects(cid, label):
            events.append(("normal_subjects", cid, label))
            return "NORMAL_OK"
        def old_callback(cid, data):
            events.append(("normal_callback", cid, data))
            return "OLD_OK"
        def send(cid, message, kb=None):
            events.append(("send", cid, message, kb))
            return "SENT"
        def send_document(cid, path, caption):
            data = Path(path).read_bytes()
            self.assertTrue(data.startswith(b"%PDF-"))
            events.append(("pdf", cid, caption))
            return Response()
        namespace = {
            "__file__": str(ROOT / "app.py"),
            "subjects": old_subjects,
            "callback": old_callback,
            "send": send,
            "send_document": send_document,
            "_telegram_delivery_ok_v25279": lambda r: bool(getattr(r, "ok", False)) and r.json().get("ok") is True,
        }
        self.assertTrue(install(namespace))
        self.assertEqual(namespace["subjects"](999, "Tahun 1"), "NORMAL_OK")
        self.assertEqual(sum(e[0] == "send" for e in events), 0)
        self.assertEqual(namespace["subjects"](123, "Tahun 1"), "NORMAL_OK")
        self.assertEqual(sum(e[0] == "send" for e in events), 1)
        self.assertEqual(namespace["callback"](123, "home"), "OLD_OK")
        self.assertEqual(namespace["callback"](999, "pjpkprivate_year_1"), "SENT")
        events.clear()
        namespace["callback"](123, "pjpkprivate_subject_1_PJ")
        buttons = [b for row in events[-1][3] for b in row]
        pdf_buttons = [b for b in buttons if b["callback_data"].startswith("pjpkprivate_pdf_")]
        self.assertEqual(len(pdf_buttons), 28)  # 36 review-only entries minus eight quarantined T1 PJ duplicates
        events.clear()
        result = namespace["callback"](123, pdf_buttons[0]["callback_data"])
        self.assertTrue(getattr(result, "ok", False))
        self.assertTrue(any(e[0] == "pdf" for e in events))

if __name__ == "__main__":
    unittest.main()
