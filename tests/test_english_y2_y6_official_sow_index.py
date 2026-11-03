"""English Years 2–6 official SOW source-ledger audit — read-only, no app imports or DB changes."""
import json
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))
SP=re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")

class EnglishY2Y6OfficialSOWAudit(unittest.TestCase):
    def test_all_800_contiguous_lesson_files(self):
        for year in range(2,7):
            paths=sorted((ROOT/f"rph_standalone/english/year{year}").glob("lesson_[0-9][0-9][0-9].md"))
            self.assertEqual([int(p.stem[-3:]) for p in paths],list(range(1,161)),year)
            self.assertEqual(sum(1 for k in LEDGER["lessons"] if k.startswith(f"{year}/")),160)

    def test_official_exceptions_not_misrepresented(self):
        self.assertEqual(LEDGER["lessons"]["2/160"]["focus"],"Language Arts 42")
        self.assertEqual(LEDGER["lessons"]["3/93"]["main_ls"],"3.2.1")
        self.assertIn("Welcome", LEDGER["lessons"]["3/20"]["issue"])
        self.assertEqual(LEDGER["lessons"]["3/20"]["main_ls"], "4.3.3")
        self.assertIsNone(LEDGER["lessons"]["3/61"]["complementary_ls"])
        self.assertEqual(LEDGER["lessons"]["4/157"]["complementary_ls"],"3.2.3")
        self.assertEqual(LEDGER["lessons"]["5/141"]["complementary_ls"],"4.2.4")
        self.assertTrue(LEDGER["lessons"]["5/160"]["teacher_selected"])
        self.assertTrue(LEDGER["lessons"]["6/160"]["teacher_selected"])
        self.assertTrue(all(LEDGER["lessons"][f"6/{n}"]["teacher_selected"] for n in range(155,159)))

    def test_year4_lesson30_uses_official_cd2_track29(self):
        lesson=(ROOT/"rph_standalone/english/year4/lesson_030.md").read_text(encoding="utf-8")
        self.assertIn("CD2 Track 29", lesson)
        self.assertNotIn("CD1 Track 29", lesson)

    def test_machine_audit_prints_open_mismatches_without_false_ready_claims(self):
        grouped={year:{"fixed":0,"matched":0,"no_explicit_pair":0,"mismatch":[]} for year in range(2,7)}
        for year in range(2,7):
            for n in range(1,161):
                entry=LEDGER["lessons"][f"{year}/{n}"]
                file=(ROOT/f"rph_standalone/english/year{year}/lesson_{n:03d}.md")
                body=file.read_text(encoding="utf-8")
                self.assertRegex(body.splitlines()[0],rf"(?i)\bLesson\s+0*{n}\b")
                if entry["teacher_selected"] or not entry["main_ls"] or not entry["complementary_ls"]:
                    grouped[year]["no_explicit_pair"]+=1
                    continue
                grouped[year]["fixed"]+=1
                # Only the lesson header before the first teaching phase; do not count PBD examples.
                header=re.split(r"(?im)^\s*(?:\d+\.\s*)?(?:\*\*)?(?:## )?Set induction\b",body,maxsplit=1)[0]
                header=header[:2400]
                codes=set(SP.findall(header))
                pair={entry["main_ls"],entry["complementary_ls"]}
                if pair <= codes:
                    grouped[year]["matched"]+=1
                else:
                    grouped[year]["mismatch"].append(n)
            print("ENGLISH_Y%d_SOW_HEADER_AUDIT" % year,grouped[year])
        # This is a discovery audit, not a release authorization; transparent mismatch details
        # are printed before classroom and workbook verification.
        self.assertEqual(sum(v["fixed"]+v["no_explicit_pair"] for v in grouped.values()),800)

if __name__=="__main__":
    unittest.main()
