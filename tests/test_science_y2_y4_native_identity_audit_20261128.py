import unittest
from unittest.mock import Mock,patch
from tools.science_y2_y4_native_identity_audit_20261128 import snapshot,log_read_only

class SourceIdentityAudit(unittest.TestCase):
    def test_exact_standards_null_duration_and_no_private_fields(self):
        rt=Mock()
        rt.CIKGULAJU_DB_V2600_ACTIVE=True
        data=[dict(unit_code="3.1",unit_title="Manusia",pdp_sequence_code="SCI-Y2-PDP-001",
            pdp_title="Pembiakan manusia",source_sequence_no=1,sk_code="3.1",
            sk_text="Pembiakan dan tumbesaran manusia",sp_code="3.1.1",
            sp_text="Menyatakan cara manusia membiak.",textbook_ref="Buku Teks m/s 24",
            telegram_user_id=123456,secret="DO_NOT_EXPORT")]
        rt._sm2542_rows.return_value=data
        rt._sm2542_unique_units.return_value=[("3.1","Manusia")]
        with patch("web.telegram_verified_sequence_rph_bridge.sains_unit_awal.add_opening_units",side_effect=lambda y,r:r):
            result=snapshot(rt,2)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["lesson_id"],"SCI-Y2-PDP-001")
        self.assertEqual(result[0]["standards"][0]["sp_code"],"3.1.1")
        self.assertIsNone(result[0]["minutes"])
        self.assertNotIn("DO_NOT_EXPORT",str(result))
        self.assertNotIn("123456",str(result))
        rt.create_word_file.assert_not_called()
        rt.create_pdf_file.assert_not_called()
        rt._local_rph_text.assert_not_called()

    def test_unsupported_year(self):
        with self.assertRaises(ValueError):snapshot(Mock(),5)
        with self.assertRaises(ValueError):snapshot(Mock(),"2")

if __name__=="__main__":unittest.main()
