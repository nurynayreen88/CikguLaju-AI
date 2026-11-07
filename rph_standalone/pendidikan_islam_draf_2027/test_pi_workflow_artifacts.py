"""Guard against green CI while the expected review artifacts are not uploaded."""
from pathlib import Path
import re
import unittest


EXPECTED = {
    "pi_quality_audit_696.json",
    "pi_pedagogy_proposals_690.json",
    "pi_buku_aktiviti_audit_696.json",
    "pi_ba_candidate_queue_258.json",
    "pi_ba_secondary_evidence_42.json",
    "pi_ba_source_integrity.json",
    "pi_ba_sentence_candidates_174.json",
    "pi_ba_provenance_42.json",
    "pi_ba_verification_register_174.json",
    "pi_ba_verification_register_174.csv",
}


class WorkflowArtifactTests(unittest.TestCase):
    def test_files_generated_checked_and_uploaded(self):
        workflow = (Path(__file__).resolve().parents[2] /
                    ".github/workflows/pi-2027-partial-drafts.yml").read_text(encoding="utf-8")
        self.assertIn("Verify every audit artifact exists, is nonempty", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        checks = workflow.split("for file in \\", 1)[1].split("; do", 1)[0]
        paths = workflow.split("      - name: Upload isolated QA ledger", 1)[1]
        expected_list = [
            "            " + filename for filename in EXPECTED
        ]
        # Ensure each generated file is present in the shell safety check and
        # in upload path separately, preventing empty/partial ZIPs.
        for filename in EXPECTED:
            self.assertIn(filename, checks, filename)
            self.assertIn("            " + filename + "\n", paths, filename)
            self.assertIn(filename, workflow.split("      - name: Verify every", 1)[0], filename)
        lines = [line.rstrip() for line in checks.splitlines() if line.strip()]
        # Bash needs a trailing backslash on all but the last filename.
        for line in lines[:-1]:
            self.assertTrue(line.endswith("\\"), repr(line))
        self.assertFalse(lines[-1].endswith("\\"))


if __name__ == "__main__":
    unittest.main()
