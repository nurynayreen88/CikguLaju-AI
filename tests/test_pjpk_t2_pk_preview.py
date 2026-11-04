import tempfile
import unittest
from pathlib import Path
from scripts.pjpk_t2_pk_preview import generate, render, SOURCES
import json


class TestT2PKPreview(unittest.TestCase):
    def test_all_eighteen_render_with_safe_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(generate(folder), 18)
            pages = list(Path(folder).glob("T2_PK_*.html"))
            self.assertEqual(len(pages), 18)
            for page in pages:
                text = page.read_text(encoding="utf-8")
                for required in ("RANCANGAN PENGAJARAN HARIAN", "BELUM DILULUSKAN UNTUK PRODUKSI",
                                 "Objektif:", "BBM:", "Set Induksi", "Aktiviti 1", "Aktiviti 2",
                                 "Pengukuhan / Penilaian", "Penutup", "Pentaksiran:", "Refleksi:",
                                 "Slot RPT / Halaman buku teks:", "Belum disahkan"):
                    self.assertIn(required, text, (page.name, required))

    def test_ready_record_is_rejected(self):
        record = json.loads(SOURCES[0].read_text(encoding="utf-8"))["records"][0].copy()
        record["production_ready"] = True
        with self.assertRaises(ValueError):
            render(record)


if __name__ == "__main__":
    unittest.main()
