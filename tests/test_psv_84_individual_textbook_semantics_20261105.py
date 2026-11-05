"""Independent per-PdP source-content regression for 84 PSV staging drafts.

Every keyword pair was checked against the source PDF unit/product and the
corresponding RPH teaching phases. This is a content guard only, not approval
to deploy to Telegram or proof that a teacher has accepted each lesson.
"""
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    3: {
            1: ("silang pangkah", "roda"),
            2: ("lokomotif", "asap"),
            3: ("silang pangkah", "lokomotif"),
            4: ("silang pangkah", "apresiasi"),
            5: ("perayaan", "montaj"),
            6: ("poster", "perayaan"),
            7: ("poster", "montaj"),
            8: ("poster", "apresiasi"),
            9: ("saderi", "bendi"),
            10: ("capan", "kain"),
            11: ("saderi", "bendi"),
            12: ("saderi", "bendi"),
            13: ("serangga", "mobail"),
            14: ("cawan", "tali"),
            15: ("mobail", "tali"),
            16: ("mobail", "serangga"),
            17: ("parang ilang", "bentuk"),
            18: ("kadbod", "rafia"),
            19: ("parang ilang", "jalinan"),
            20: ("pameran", "kapsyen"),
            21: ("pameran", "karya"),
            22: ("belon", "kertas"),
            23: ("belon", "felt"),
            24: ("belon", "kolaj"),
            25: ("belon", "kolaj"),
            26: ("gurisan", "oil pastel"),
            27: ("gurisan", "aiskrim"),
            28: ("gurisan", "merak"),
            29: ("gurisan", "merak"),
            30: ("renjisan", "terendak"),
            31: ("renjisan", "aiskrim"),
            32: ("renjisan", "aiskrim"),
            33: ("renjisan", "rangka"),
            34: ("boneka", "tisu"),
            35: ("boneka", "tali"),
            36: ("boneka", "tali"),
            37: ("boneka", "tali"),
            38: ("anyaman", "kelarai"),
            39: ("anyaman", "kelarai"),
            40: ("anyaman", "kelarai"),
            41: ("pameran", "kapsyen"),
            42: ("pameran", "karya"),
    },
    6: {
            1: ("kaktus", "silang pangkah"),
            2: ("alat tulis", "lakaran"),
            3: ("tingkap damai", "tetingkap"),
            4: ("dunia gemilang", "arca"),
            5: ("stabail", "tanggam"),
            6: ("kotak kejutan", "kotak"),
            7: ("realiti alam", "ruang"),
            8: ("lihat dan sentuh", "capan"),
            9: ("kaktus khatulistiwa", "montaj"),
            10: ("lebah", "kotak"),
            11: ("lebah", "kotak"),
            12: ("lebah", "kotak"),
            13: ("lebah", "folio"),
            14: ("koi", "arca"),
            15: ("koi", "roda"),
            16: ("koi", "roda"),
            17: ("koi", "folio"),
            18: ("sisik ikan", "kolaj"),
            19: ("gerak beritma", "berpancar"),
            20: ("lemon", "velkro"),
            21: ("celupan", "kain"),
            22: ("ikatan seni", "kain"),
            23: ("sarung botol", "celupan"),
            24: ("pameran", "kapsyen"),
            25: ("pameran", "karya"),
            26: ("pameran", "refleksi"),
            27: ("loket", "pending"),
            28: ("cucuk sanggul", "cekak"),
            29: ("tanjak", "lipatan"),
            30: ("wau", "sirih"),
            31: ("wau", "cerminan"),
            32: ("wau", "felt"),
            33: ("wau", "rambu"),
            34: ("wau", "folio"),
            35: ("beg batik", "bunga raya"),
            36: ("beg batik", "susunan"),
            37: ("beg batik", "bunga raya"),
            38: ("beg batik", "velkro"),
            39: ("beg batik", "folio"),
            40: ("pameran", "kapsyen"),
            41: ("pameran", "karya"),
            42: ("pameran", "refleksi"),
    },
}


def read_rpt(year):
    path = ROOT / f"rpt_2027/psv/RPT_PSV_Tahun_{year}_2027_DRAF.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class PSV84SourceContentTests(unittest.TestCase):
    def test_every_84_staging_rph_has_individual_source_activity(self):
        self.assertEqual(sum(len(v) for v in REQUIRED.values()), 84)
        for year, checks in REQUIRED.items():
            self.assertEqual(len(checks), 42)
            rows = read_rpt(year)
            self.assertEqual(len(rows), 42)
            for pdp, phrases in checks.items():
                with self.subTest(year=year, pdp=pdp):
                    row = rows[pdp-1]
                    self.assertEqual(row["PdP"], f"{pdp:03d}")
                    rph = ROOT / f"rph_standalone/psv/year{year}/lesson_{pdp:03d}.md"
                    body = rph.read_text(encoding="utf-8")
                    folded = body.casefold()
                    for phrase in phrases:
                        self.assertIn(phrase.casefold(), folded)
                    self.assertIn("**SK:** " + row["SK"], body)
                    self.assertIn("**SP:** " + row["SP"], body)
                    for phase in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup"):
                        self.assertIn(phase, body)
                    self.assertIn("**Status:** DRAF", body)
                    self.assertIn(
                        "hkvtu/vifc" if year == 3 else "hkvtu/cnbo",
                        folded,
                    )

    def test_every_84_staging_adapter_preview_preserves_native_fields(self):
        """Preview all individual lessons through the real fail-closed PSV adapter."""
        from web.psv_2027_rph_release_bridge import adapt_rows, load_candidate
        original = {
            "KELAS": "6 Amanah",
            "TARIKH": "2026-11-05",
            "MASA": "10:00–11:00",
            "REFLEKSI": "Guru catat selepas PdP",
            "CATATAN": "Jangan ubah metadata pengguna",
        }
        count = 0
        for year, checks in REQUIRED.items():
            for pdp in checks:
                with self.subTest(year=year, pdp=pdp):
                    state = {
                        "subject": "Pendidikan Seni Visual",
                        "year": year,
                        "lesson_no": pdp,
                    }
                    candidate = load_candidate(year, pdp, preview=True)
                    self.assertIsNotNone(candidate)
                    row = adapt_rows(state, original, preview=True)
                    self.assertIsNot(row, original)
                    self.assertEqual(row["STANDARD KANDUNGAN"], candidate["sk"])
                    self.assertEqual(row["STANDARD PEMBELAJARAN"], candidate["sp"])
                    self.assertEqual(row["OBJEKTIF PEMBELAJARAN"], candidate["objective"])
                    self.assertEqual(row["KRITERIA KEJAYAAN"], candidate["evidence"])
                    self.assertIn("Aktiviti 1", row["AKTIVITI UTAMA"])
                    self.assertIn("Aktiviti 2", row["AKTIVITI UTAMA"])
                    self.assertTrue(row["BAHAN BANTU MENGAJAR"])
                    self.assertTrue(row["PENTAKSIRAN"])
                    for k, v in original.items():
                        self.assertEqual(row[k], v)
                    self.assertNotIn("DRAF SEMAK", " ".join(map(str, row.values())))
                    count += 1
        self.assertEqual(count, 84)
        untouched = adapt_rows({
            "subject": "Pendidikan Kesenian", "year": 3, "lesson_no": 12
        }, original, preview=True)
        self.assertIs(untouched, original)

    def test_each_84_rpt_sp_is_listed_in_original_year_dskp(self):
        """Literal code whitelist derived from the 2019 Year3 and 2021 Year6 DSKP PDFs."""
        codes = {
            3: {
                "1.1.1", "1.1.2", "1.1.3", "1.1.4", "1.1.5",
                "1.1.6", "1.1.7", "1.1.8", "1.1.9", "1.1.10",
                "2.1.1", "2.1.2", "2.1.3", "2.1.4",
                "3.1.1", "3.1.2", "3.1.3", "3.1.4", "3.1.5",
                "3.3.1", "3.3.2", "3.3.3", "3.3.4", "3.3.5",
                "4.1.1", "4.1.2",
            },
            6: {
                "1.1.1", "1.1.2", "1.1.3",
                "2.1.1", "2.1.2", "2.1.3",
                "3.1.1", "3.2.1", "3.2.2", "3.2.3",
                "4.1.1",
                "5.1.1", "5.1.2", "5.1.3", "5.1.4", "5.1.5",
            },
        }
        for year in (3, 6):
            for row in read_rpt(year):
                with self.subTest(year=year, pdp=row["PdP"]):
                    listed = [s.strip() for s in row["SP"].split(";")]
                    self.assertTrue(set(listed).issubset(codes[year]))
                    if year == 3 and int(row["PdP"]) in (20, 21, 41, 42):
                        # Year3 DSKP prints SK 5.1 despite SP numbering 3.3.x.
                        self.assertEqual(row["SK"], "5.1")
                        self.assertTrue(all(s.startswith("3.3.") for s in listed))

    def test_year6_nine_source_page_ranges_are_specific_and_aligned(self):
        """Original Year6 book pages split by individual teaching objective."""
        cases = {
            10: "26–27", 11: "28–29", 12: "30–31", 13: "32–33",
            14: "34–35", 15: "36–37", 16: "38–43", 17: "44–45",
            21: "56–57",
        }
        rows = read_rpt(6)
        html = (
            ROOT / "rpt_2027/psv/RPT_PSV_Tahun_6_2027_DRAF.html"
        ).read_text(encoding="utf-8")
        for pdp, pages in cases.items():
            with self.subTest(pdp=pdp):
                row = rows[pdp - 1]
                source = (
                    ROOT / f"rph_standalone/psv/year6/lesson_{pdp:03d}.md"
                ).read_text(encoding="utf-8")
                self.assertEqual(row["PdP"], f"{pdp:03d}")
                self.assertEqual(
                    row["Rujukan BT ms (RPT 2026)"], f"Buku teks ms {pages}"
                )
                self.assertIn(f"ms {pages} (halaman khusus PdP", source)
                htmlrow = next(
                    line for line in html.splitlines()
                    if f"<td>{pdp:03d}</td>" in line
                )
                self.assertIn(f"Buku teks ms {pages}", htmlrow)

    def test_no_source_verification_bypasses_telegram_release_gate(self):
        audit = ROOT / "rph_standalone/psv/audits/psv_individual_210_review_20261105.csv"
        with audit.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        targets = [r for r in rows if int(r["Tahun"]) in (3, 6)]
        self.assertEqual(len(targets), 84)
        self.assertTrue(all(r["Kelulusan_terbit"] == "BELUM_READY" for r in targets))
        self.assertTrue(all("BUKU_TEKS_UNIT_KANDUNGAN_DISEMAK" in r["Pemeriksaan_RPH_individu"] for r in targets))
        self.assertTrue(all("https://drive.google.com/file/d/" in r["Bukti_buku"] for r in targets))


if __name__ == "__main__":
    unittest.main()
