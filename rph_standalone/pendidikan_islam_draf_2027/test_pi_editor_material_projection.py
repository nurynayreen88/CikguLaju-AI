"""Editor preview must preserve all 523 source notes without leaking them into bahan."""
import hashlib
import json
from pathlib import Path
import unittest

from pi_editor_material_projection import preview_catalog
from pi_quality_audit import COUNT, REQUIRED


class EditorMaterialProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=preview_catalog()
        cls.idx={r["id"]:r for r in cls.data["rows"]}

    def test_all_sources_preserved_all_holds_excluded(self):
        d=self.data
        self.assertEqual(d["all_records"],696)
        self.assertEqual(d["active_drafts"],690)
        self.assertEqual(d["held_excluded"],6)
        self.assertEqual(d["hidden_editor_notes_total"],523)
        self.assertEqual(d["unrecognized_material_line_count"],0)
        self.assertEqual(d["release"],"NO_GO")
        self.assertIsNone(d["academic_quality_percent"])
        for id_ in ("T2-L035","T6-L006","T6-L014","T6-L018","T6-L060","T6-L117"):
            self.assertNotIn(id_,self.idx)

    def test_each_display_field_except_bahan_equals_original(self):
        root=Path(__file__).parent
        for year,count in COUNT.items():
            records=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))["records"]
            self.assertEqual(len(records),count)
            for item in records:
                if item["withheld"]:
                    continue
                d=self.idx[item["id"]]
                original=item["fields"]
                self.assertEqual(
                    d["source_material_sha256"],
                    hashlib.sha256(original["bahan"].encode("utf-8")).hexdigest()
                )
                for field in REQUIRED:
                    if field!="bahan":
                        self.assertEqual(d["display_fields"][field],original[field])
                parts=[x.strip() for x in original["bahan"].splitlines() if x.strip()]
                self.assertEqual(d["display_fields"]["bahan"],parts[0])
                self.assertEqual(d["editor_only_material_notes"],parts[1:])
                self.assertEqual(d["hidden_note_count"],len(parts)-1)

    def test_specific_risk_words_do_not_enter_materials_preview(self):
        for id_,token in [
            ("T2-L067","PEMBETULAN DIAUDIT:"),
            ("T2-L003","halaman khusus belum"),
            ("T3-L003","Rekod padanan SP buku teks lama"),
            ("T4-L001","sebelum READY"),
            ("T6-L001","memerlukan semakan visual"),
        ]:
            d=self.idx[id_]
            self.assertNotIn(token,d["display_fields"]["bahan"])
            self.assertTrue(any(token in n for n in d["editor_only_material_notes"]))
        for r in self.idx.values():
            self.assertNotIn("BELUM DISAHKAN",r["display_fields"]["bahan"])
            self.assertNotIn("Padanan SK/TOC terdahulu",r["display_fields"]["bahan"])
            self.assertNotIn("PEMBETULAN DIAUDIT",r["display_fields"]["bahan"])
            self.assertNotIn("Rekod padanan SP buku teks lama",r["display_fields"]["bahan"])
            self.assertTrue(r["preview_only"])
            self.assertFalse(r["ready"])
            self.assertFalse(r["can_publish"])
            self.assertFalse(r["quality_certified"])
            self.assertFalse(r["book_activity_page_verified"])


if __name__=="__main__":
    unittest.main()
