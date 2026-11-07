"""Safety gate: not a single draft Sains RPH may be auto-released."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from web.sains_rph_quality_release_gate_20261108 import (
    APPROVALS,SainsRPHNotApproved,approved_count,
    can_publish_sains_rph,content_sha256,require_approved_sains_rph,
)
from tools.audit_rph80_sains_first_20261107 import EXPECTED


SOURCE=("Sains Tahun 5, SP 2.1.1; Guru menunjukkan rangka manusia pada model "
        "dan mengemukakan soalan. Murid membina model rangka, menerangkan "
        "fungsi dan merekod pemerhatian individu. Aktiviti 1 dan Aktiviti 2, "
        "PBD: murid melabel rangka serta menerangkan peranan tulang. "
        "Buku Teks halaman telah diperiksa oleh guru.")
IDENTITY={"year":5,"pdp_code":"SCI-Y5-PDP-001","sk":"2.1","sp":"2.1.1"}
WEIGHTS={"sk_sp":25,"buku_teks_rpt":25,"aktiviti_pbd":25,
         "word_pdf":15,"telegram_web":10}


def candidate():
    return {
        **IDENTITY,
        "source_sha256":content_sha256(SOURCE),
        "status":"FINAL_READY",
        "teacher_panitia_approved":True,
        "safety_reviewed":True,
        "pbd_individual_evidence_reviewed":True,
        "authenticated_web_telegram_e2e_passed":True,
        "scores":dict(WEIGHTS),
        "evidence":{
            "reviewer":"Guru Penilai Panitia",
            "review_date":"2026-10-20",
            "review_is_for_exact_source_sha":True,
            "dskp":"a"*64,
            "textbook_pages":"b"*64,
            "specific_activities_pbd":"c"*64,
            "rendered_word_pdf":"d"*64,
            "runtime_parity":"e"*64,
        },
    }


def write_registry(folder,records):
    path=Path(folder)/"registry.json"
    content=json.loads(APPROVALS.read_text(encoding="utf-8"))
    content["approved"]=records
    path.write_text(json.dumps(content,ensure_ascii=False),encoding="utf-8")
    return path


class TestSainsRPHQualityRelease(unittest.TestCase):
    def test_no_unapproved_draft_public_from_all_342_source_codes(self):
        self.assertEqual(approved_count(),0)
        for year,n in EXPECTED.items():
            for i in range(1,n+1):
                code=f"SCI-Y{year}-PDP-{i:03d}"
                with self.subTest(code=code):
                    self.assertFalse(can_publish_sains_rph(
                        year=year,pdp_code=code,sk="2.1",sp="2.1.1",
                        source_text=SOURCE,source_status="DRAF_HOLD"))
        for year in EXPECTED:
            self.assertFalse(can_publish_sains_rph(
                year=year,pdp_code=f"SCI-Y{year}-PDP-001",
                sk="2.1",sp="2.1.1",
                source_text=SOURCE,source_status="FINAL_READY"))
        with self.assertRaises(SainsRPHNotApproved):
            require_approved_sains_rph(**IDENTITY,source_text=SOURCE,
                                       source_status="FINAL_READY")

    def test_only_exact_80_plus_signed_per_pdp_and_correct_sp_source_is_eligible(self):
        with TemporaryDirectory() as folder:
            registry=write_registry(folder,[candidate()])
            args={**IDENTITY,"source_text":SOURCE,
                  "source_status":"FINAL_READY","registry_path":registry}
            self.assertTrue(can_publish_sains_rph(**args))
            self.assertTrue(require_approved_sains_rph(**args))
            self.assertFalse(can_publish_sains_rph(**{**args,"source_status":"DRAF_HOLD"}))
            self.assertFalse(can_publish_sains_rph(**{**args,"source_text":SOURCE+" changed"}))
            self.assertFalse(can_publish_sains_rph(**{**args,"sp":"2.1.2"}))
            self.assertFalse(can_publish_sains_rph(**{**args,"pdp_code":"SCI-Y5-PDP-002"}))
            self.assertFalse(can_publish_sains_rph(**{**args,"year":4}))
            self.assertFalse(can_publish_sains_rph(**{**args,"sk":"2.2"}))

    def test_score_79_or_critical_minimum_failure_never_release(self):
        with TemporaryDirectory() as folder:
            row=candidate()
            row["scores"]={"sk_sp":20,"buku_teks_rpt":20,"aktiviti_pbd":20,
                           "word_pdf":11,"telegram_web":8}
            registry=write_registry(folder,[row])
            with self.assertRaises(ValueError):
                approved_count(registry_path=registry)
            # Even 85 total fails if core SK/SP is weak.
            row["scores"]={"sk_sp":19,"buku_teks_rpt":25,"aktiviti_pbd":25,
                           "word_pdf":15,"telegram_web":10}
            registry=write_registry(folder,[row])
            with self.assertRaises(ValueError):
                approved_count(registry_path=registry)
            # At exactly 80 with all minima evidence is permitted only for
            # an explicitly READY, signed source; none exist in live ledger.
            row["scores"]={"sk_sp":20,"buku_teks_rpt":20,"aktiviti_pbd":20,
                           "word_pdf":12,"telegram_web":8}
            registry=write_registry(folder,[row])
            self.assertEqual(approved_count(registry_path=registry),1)

    def test_missing_evidence_wrong_sha_or_duplicate_cannot_create_approval(self):
        with TemporaryDirectory() as folder:
            for edit in ("no_teacher","no_auth","no_ref","no_digest","duplicate",
                         "future_date","not_exact_source"):
                record=candidate()
                if edit=="no_teacher":
                    record["teacher_panitia_approved"]=False
                elif edit=="no_auth":
                    record["authenticated_web_telegram_e2e_passed"]=False
                elif edit=="no_ref":
                    del record["evidence"]["dskp"]
                elif edit=="no_digest":
                    record["source_sha256"]="changed"
                elif edit=="future_date":
                    record["evidence"]["review_date"]="2099-01-01"
                elif edit=="not_exact_source":
                    record["evidence"]["review_is_for_exact_source_sha"]=False
                recs=[record,deepcopy(record)] if edit=="duplicate" else [record]
                registry=write_registry(folder,recs)
                with self.subTest(edit=edit),self.assertRaises(ValueError):
                    approved_count(registry_path=registry)

    def test_bad_code_no_blank_or_short_rph(self):
        with self.assertRaises(ValueError):
            content_sha256("generik")
        self.assertFalse(can_publish_sains_rph(
            year=2,pdp_code="SCI-Y2-PDP-052",sk="2.1",sp="2.1.1",
            source_text=SOURCE,source_status="FINAL_READY"))
        self.assertFalse(can_publish_sains_rph(
            year=1,pdp_code="SCI-Y1-PDP-001",sk="2.1",sp="2.1.1",
            source_text=SOURCE,source_status="FINAL_READY"))


if __name__=="__main__":
    unittest.main()
