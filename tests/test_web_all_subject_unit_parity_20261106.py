"""Release guard: every source-backed Web Unit appears once, all PdPs survive.

No source files or user data are changed. A failed source should fail the QA,
not silently shift a Lesson to another Unit or invent a replacement RPH.
"""
import re
import unittest
from web.unified_rph_web import source_records, unit_options, pdp_options


class PrimarySourceUnitParity(unittest.TestCase):
    EXPECTED={
        ("ENGLISH",None):{2:160,3:160,4:160,5:160,6:160},
        ("MORAL",None):{2:42,3:42,4:42,5:42,6:42},
        ("PJPK","PJ"):{2:37,3:38,4:34,5:33,6:34},
        ("PJPK","PK"):{2:35,3:32,4:32,5:32,6:32},
        ("PSV",None):{2:42,3:42,4:42,5:42,6:42},
    }
    def test_every_unit_only_once_and_every_pdp_stays_in_its_original_unit(self):
        for (subject,component),years in self.EXPECTED.items():
            for year,count in years.items():
                with self.subTest(subject=subject,component=component,year=year):
                    records=source_records(year,subject,component)
                    self.assertEqual(len(records),count)
                    tokens=[row["token"] for row in records]
                    self.assertEqual(len(set(tokens)),count)
                    units=unit_options(year,subject,component)
                    labels=[re.sub(r"\s+"," ",u["label"]).strip().casefold()
                            for u in units]
                    self.assertEqual(len(set(labels)),len(labels),
                                     f"Repeated semantic Unit: {subject}/{component}/{year}")
                    self.assertTrue(all(u["value"]==u["label"] for u in units))
                    found=[]
                    for option in units:
                        choices=pdp_options(year,subject,option["value"],component)
                        self.assertTrue(choices,f"Empty Unit: {subject}/{year}/{option}")
                        for row in choices:
                            self.assertTrue(
                                re.match(r"^(?:PdP|Lesson)\s+\d{3}\b",row["label"]),
                                (subject,year,row))
                            self.assertEqual(
                                row["download_enabled"],False)
                            self.assertEqual(
                                row["standalone_rph_verified"],False)
                        found.extend(c["value"] for c in choices)
                    # A real Unit can recur later in the source SOW/RPT:
                    # Unit grouping is therefore allowed to reorder the menu
                    # while preserving every original Lesson/PdP exactly once.
                    self.assertEqual(sorted(found),sorted(tokens),
                                     f"Missing/duplicate PdP: {subject}/{component}/{year}")
                    self.assertEqual(len(found),len(set(found)))

    def test_pk_uses_domain_not_each_pdp_as_unit(self):
        for year in range(2,7):
            self.assertEqual(len(unit_options(year,"PJPK","PK")),9)

    def test_pj_units_no_embedded_activity_heading(self):
        for year in range(2,7):
            units=unit_options(year,"PJPK","PJ")
            self.assertTrue(all(u["label"].startswith("Unit ") for u in units))
            self.assertFalse(any(re.search(r"\bTAJUK\s*:",u["label"],re.I) for u in units))


if __name__=="__main__":
    unittest.main()
