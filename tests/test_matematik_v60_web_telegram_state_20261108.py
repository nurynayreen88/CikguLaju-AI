"""End-to-end native identity construction from a verified Maths PdP selection.

No SQL writes, no browser, no user quota debit, no Render services.
Tests the real source resolver -> state -> v60 content -> native output rows.
"""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.telegram_verified_sequence_rph_bridge import (
    _build_state, _unit_token, _source_text, SourceUnavailable,
)
from web.matematik_v60_native_rows import adapt_rows
from rph_standalone.matematik.v60_source_loader import get_lesson

FLAG={"CIKGULAJU_ENV":"staging","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}
CLASS={"class":"4 Amanah","date":"2026-11-08","time":"08:00-09:00","students":"32"}


def _runtime(*, multi=False, number=14, code="PDP-T4-014"):
    rows=[{"unit_code":"U1","unit_title":"Operasi Bergabung",
           "pdp_sequence_code":code,"source_sequence_no":number,
           "pdp_title":"Darab dan bahagi","sk_code":"1.7","sp_code":"1.7.2",
           "sk_text":"Operasi bergabung", "sp_text":"Darab dan bahagi",
           "textbook_ref":"Buku Teks T4 hlm. 43–47",
           "activitybook_ref":""}]
    if multi:
        rows.append(dict(rows[0],sp_code="1.7.3"))
    def commit(state, mapped):
        state["grouped_sp_codes"]=[row["sp_code"] for row in mapped]
        state["selected_sp_codes"]=list(state["grouped_sp_codes"])
        state["grouped_sk_codes"]=[row["sk_code"] for row in mapped]
        state["sp_code"]=mapped[0]["sp_code"]
        state["sk_code"]=mapped[0]["sk_code"]
    return SimpleNamespace(
        CIKGULAJU_DB_V2600_ACTIVE=True,
        _sm2542_rows=lambda y,s:rows,
        _sm2542_unique_units=lambda rows:[("U1","Operasi Bergabung")],
        _commit_multi_sp=commit,
        _local_rph_text=lambda s:"Legacy document " * 75,
    )


class NativeStateToV60(unittest.TestCase):
    def test_teacher_native_sequence_retains_source_and_context(self):
        rt=_runtime()
        with patch.dict(os.environ,FLAG):
            state=_build_state(rt,4,"MATH",_unit_token("U1","Operasi Bergabung"),"PDP-T4-014",CLASS)
            self.assertEqual(state["source_sequence_no"],14)
            self.assertEqual(state["sk_code"],"1.7")
            self.assertEqual(state["selected_sp_codes"],["1.7.2"])
            self.assertEqual(state["rph_date"],"08/11/2026")
            self.assertEqual(state["rph_class"],"4 Amanah")
            self.assertEqual(state["rph_time"],"08:00-09:00")
            self.assertEqual(state["rph_students"],"32")
            self.assertEqual(_source_text(rt,state),get_lesson(4,14))
            output=adapt_rows(state,{"KELAS":"4 Amanah","TARIKH":"08/11/2026",
                                     "MASA":"08:00-09:00","BILANGAN MURID":"32"})
            self.assertEqual(output["TAJUK"],"Operasi bergabung darab dan bahagi")
            self.assertIn("24 × 15 ÷ 6",output["SET INDUKSI"])
            self.assertIn("Aktiviti 1",output["AKTIVITI UTAMA"])
            self.assertEqual(output["KELAS"],"4 Amanah")
            self.assertEqual(output["TARIKH"],"08/11/2026")

    def test_missing_pdp_and_multi_sp_are_not_marked_available(self):
        with patch.dict(os.environ,FLAG):
            rt=_runtime()
            with self.assertRaises(SourceUnavailable):
                _build_state(rt,4,"MATH",_unit_token("U1","Operasi Bergabung"),"UNKNOWN",CLASS)
            rt=_runtime(multi=True)
            state=_build_state(rt,4,"MATH",_unit_token("U1","Operasi Bergabung"),"PDP-T4-014",CLASS)
            with self.assertRaises(SourceUnavailable):
                _source_text(rt,state)

if __name__=="__main__":
    unittest.main()
