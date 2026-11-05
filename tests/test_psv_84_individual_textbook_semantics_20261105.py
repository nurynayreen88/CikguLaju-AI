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

    def test_no_source_verification_bypasses_telegram_release_gate(self):
        audit = ROOT / "rph_standalone/psv/audits/psv_individual_210_review_20261105.csv"
        with audit.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        targets = [r for r in rows if int(r["Tahun"]) in (3, 6)]
        self.assertEqual(len(targets), 84)
        self.assertTrue(all(r["Kelulusan_terbit"] == "BELUM_READY" for r in targets))


if __name__ == "__main__":
    unittest.main()
