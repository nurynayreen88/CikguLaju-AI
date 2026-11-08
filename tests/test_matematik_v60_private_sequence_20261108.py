"""Matematik v60 Web-to-Telegram private sequence uses the same verified source.

Tests the source selection function without an actual user, payment debit,
database migration, external HTTP request or runtime deployment.
"""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.telegram_verified_sequence_rph_bridge import _source_text, SourceUnavailable
from rph_standalone.matematik.v60_source_loader import get_lesson

ENABLED = {"CIKGULAJU_ENV":"staging","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}

def selected(year,lesson,sk,sp):
    return {
        "task":"rph","quick_material_flow":True,"year":f"Tahun {year}",
        "subject":"Matematik", "source_sequence_no":lesson,"pdp_no":lesson,
        "pdp_sequence_code":f"verified-{year}-{lesson:03d}",
        "sk_code":sk,"sp_code":sp,"selected_sp_codes":[sp],
    }

class NativeMathSequenceSource(unittest.TestCase):
    def test_web_returns_exact_telegram_v60_markdown(self):
        runtime=SimpleNamespace(_local_rph_text=lambda _: "Legacy RPH")
        examples=[(2,1,"1.1","1.1.1"),(4,14,"1.7","1.7.2"),(4,103,"7.1","7.1.2"),(6,117,"8.3","8.3.1")]
        with patch.dict(os.environ,ENABLED):
            for year,number,sk,sp in examples:
                with self.subTest(year=year,lesson=number):
                    state=selected(year,number,sk,sp)
                    self.assertEqual(_source_text(runtime,state),get_lesson(year,number))

    def test_bad_sp_or_ambiguous_native_pdp_fails_closed(self):
        runtime=SimpleNamespace(_local_rph_text=lambda _: "Legacy RPH")
        with patch.dict(os.environ,ENABLED):
            for state in (
                selected(4,14,"1.7","1.7.1"),
                dict(selected(4,14,"1.7","1.7.2"),selected_sp_codes=["1.7.2","1.7.3"]),
                dict(selected(4,14,"1.7","1.7.2"),pdp_sequence_code=""),
            ):
                with self.subTest(state=state):
                    with self.assertRaises(SourceUnavailable):
                        _source_text(runtime,state)

    def test_production_disabled_uses_existing_native_engine(self):
        runtime=SimpleNamespace(_local_rph_text=lambda _: "Legacy verified source " * 40)
        with patch.dict(os.environ,{"CIKGULAJU_ENV":"production","CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED":"1"}):
            self.assertEqual(_source_text(runtime,selected(4,14,"1.7","1.7.2")),"Legacy verified source " * 40)

if __name__=="__main__":
    unittest.main()
