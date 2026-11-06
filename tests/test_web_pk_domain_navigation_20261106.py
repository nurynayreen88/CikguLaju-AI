"""PK Tahun 2–6: one DSKP domain per menu entry, distinct numbered PdP."""
import unittest
from web.unified_rph_web import unit_options, pdp_options, source_records, PK_DSKP_DOMAINS


class PKGroupedNavigationTests(unittest.TestCase):
    def test_all_163_pk_pdp_preserved_under_nine_domains(self):
        expected={2:35,3:32,4:32,5:32,6:32}
        for year, count in expected.items():
            with self.subTest(year=year):
                rows=source_records(year,"PJPK","PK")
                self.assertEqual(len(rows),count)
                self.assertEqual([x["lesson"] for x in rows],list(range(1,count+1)))
                self.assertEqual(len({x["token"] for x in rows}),count)
                units=unit_options(year,"PJPK","PK")
                self.assertEqual(len(units),9)
                self.assertEqual(
                    [u["label"] for u in units],
                    [f"Bidang {n}: {PK_DSKP_DOMAINS[n]}" for n in range(1,10)])
                all_tokens=[]
                for unit in units:
                    choices=pdp_options(year,"PJPK",unit["value"],"PK")
                    self.assertTrue(choices)
                    self.assertTrue(all(p["label"].startswith("PdP ") for p in choices))
                    all_tokens.extend(p["value"] for p in choices)
                self.assertEqual(all_tokens,[r["token"] for r in rows])

    def test_first_pk_domain_contains_related_activities_not_duplicate_units(self):
        label=f"Bidang 1: {PK_DSKP_DOMAINS[1]}"
        units=unit_options(2,"PJPK","PK")
        self.assertEqual(sum(x["label"]==label for x in units),1)
        choices=pdp_options(2,"PJPK",label,"PK")
        self.assertEqual([v["value"] for v in choices],
                         ["p-2-PK-001","p-2-PK-002","p-2-PK-003","p-2-PK-004"])
        self.assertIn("Postur",choices[0]["label"])
        self.assertIn("Sentuhan",choices[-1]["label"])
        self.assertFalse(pdp_options(2,"PJPK","Postur, rehat dan tidur — mengenal dan mempraktik","PK"))

    def test_pj_stays_with_original_corrected_textbook_units(self):
        for year, n in {2:37,3:38,4:34,5:33,6:34}.items():
            with self.subTest(year=year):
                rows=source_records(year,"PJPK","PJ")
                self.assertEqual(len(rows),n)
                self.assertTrue(all(r["unit"].startswith("Unit ") for r in rows))
                self.assertTrue(all(r["token"].startswith(f"p-{year}-PJ-") for r in rows))
                self.assertTrue(all(r["unit"] not in [x["value"] for x in unit_options(year,"PJPK","PK")]
                                    for r in rows))


if __name__=="__main__":
    unittest.main()
