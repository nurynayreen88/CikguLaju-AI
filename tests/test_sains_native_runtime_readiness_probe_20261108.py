"""Read-only production Science diagnostic; no draft unlock or generation."""
from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.sains_native_runtime_readiness_probe_20261108 import (
    YEARS, readiness, log_readiness,
)


def fake_runtime(*,active=True,missing_year=None):
    calls={"render":0,"credits":0,"database_writes":0}
    def rows_reader(label,subject):
        year=int(str(label).split()[-1])
        if year==missing_year:return []
        return [{
            "unit_code":"","unit_title":"Unit 2: Manusia",
            "theme":"Unit 2: Manusia",
            "pdp_sequence_code":f"SCI-Y{year}-PDP-001",
            "source_sequence_no":1,
            "pdp_title":"Sains tubuh manusia",
            "sk_code":"2.1","sp_code":"2.1.1",
            "sp_text":"Menyatakan bahagian asas tubuh manusia.",
        }]
    def units(rows):
        return list(dict.fromkeys((r["unit_code"],r["unit_title"]) for r in rows))
    def commit(state,items):
        state["sk_code"]=items[0]["sk_code"]
        state["sp_code"]=items[0]["sp_code"]
        state["grouped_sp_codes"]=[v["sp_code"] for v in items]
    def native_rows(state,text):
        return {
            "AKTIVITI UTAMA":"Aktiviti 1: Guru memerhati. Murid mencatat.",
            "STANDARD PEMBELAJARAN":state["sp_code"],
        }
    return SimpleNamespace(
        CIKGULAJU_DB_V2600_ACTIVE=active,
        CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE=False,
        _sm2542_rows=rows_reader,_sm2542_unique_units=units,
        _commit_multi_sp=commit,
        _local_rph_text=lambda state:(
            "Murid memerhati model, mencatat dan membuat kesimpulan tepat; "*15),
        _rph_rows=native_rows,
        create_word_file=lambda *a: calls.__setitem__("render",calls["render"]+1),
        counters=calls,
    )


class ScienceProductionReadiness(unittest.TestCase):
    def test_five_year_existing_db_sample_source_and_rows_ready_without_mutation(self):
        runtime=fake_runtime()
        with patch.dict(os.environ,{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1"}):
            result=readiness(runtime)
        self.assertTrue(result["primary_db_active"])
        self.assertTrue(result["native_web_bridge_enabled"])
        self.assertEqual(set(result["years"]),{"2","3","4","5","6"})
        self.assertTrue(result["all_five_years_sample_ready"])
        self.assertEqual(result["opening_unit_pdp_counts"]["1"], {"Kemahiran Saintifik": 4})
        self.assertEqual(result["opening_unit_pdp_counts"]["6"], {"Kemahiran Saintifik": 5})
        self.assertEqual(result["academic_individual_approval_count"],0)
        self.assertFalse(result["new_342_academically_ready"])
        self.assertFalse(result["web_telegram_real_download_tested"])
        self.assertEqual(runtime.counters,{"render":0,"credits":0,"database_writes":0})

    def test_one_year_db_missing_reports_source_issue_without_hiding_others(self):
        runtime=fake_runtime(missing_year=4)
        result=readiness(runtime)
        self.assertFalse(result["all_five_years_sample_ready"])
        self.assertFalse(result["years"]["4"]["sample_source_text_ready"])
        self.assertTrue(result["years"]["3"]["sample_word_pdf_row_builder_ready"])
        self.assertTrue(result["years"]["5"]["sample_word_pdf_row_builder_ready"])
        self.assertTrue(result["years"]["6"]["sample_word_pdf_row_builder_ready"])

    def test_primary_db_off_reports_failure_without_generating_user_document(self):
        runtime=fake_runtime(active=False)
        result=readiness(runtime)
        self.assertFalse(result["all_five_years_sample_ready"])
        self.assertTrue(all("source_error_type" in v for v in result["years"].values()))
        self.assertEqual(runtime.counters["render"],0)

    def test_log_failure_does_not_block_main_telegram_wsgi_startup(self):
        with patch("tools.sains_native_runtime_readiness_probe_20261108.readiness",
                   side_effect=RuntimeError("source offline")):
            self.assertIsNone(log_readiness(fake_runtime()))


if __name__=="__main__":
    unittest.main()
