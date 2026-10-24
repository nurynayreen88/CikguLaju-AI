import csv
import tempfile
import unittest
from pathlib import Path
from scripts.pjpk_t2_pk_batch_audit import audit, FILES
import json


class TestT2PKBatchAudit(unittest.TestCase):
    def test_editorial_coverage_and_fail_closed(self):
        records = [r for p in FILES for r in json.loads(p.read_text(encoding="utf-8"))["records"]]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.csv"
            fields = ("entry_id", "year_label", "subject", "entry_kind", "topic", "production_ready")
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fields)
                writer.writeheader()
                for r in records:
                    writer.writerow(dict(entry_id=r["id"], year_label=r["year"],
                                         subject=r["subject"], entry_kind="PDP_CANDIDATE",
                                         topic=r["topic"], production_ready="0"))
            actual, expected, errors = audit(path)
            self.assertEqual(len(actual), 18)
            self.assertEqual(len(expected), 18)
            self.assertEqual(errors, [])
            with path.open("a", encoding="utf-8") as fh:
                fh.write("9999,Tahun 2,Pendidikan Kesihatan,PDP_CANDIDATE,Missing Topic,0\\n")
            _, _, errors = audit(path)
            self.assertTrue(any("coverage mismatch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
