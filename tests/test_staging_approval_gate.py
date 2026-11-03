"""Regression checks for temporary staging-only fail-closed approval."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "pioneer_telegram.py"

class StagingApprovalGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(SOURCE))

    def test_admin_button_does_not_promise_activation(self):
        self.assertIn("🔎 Semak Status Kelulusan", self.source)
        self.assertNotIn("✅ Sahkan Rakan Pembangun", self.source)

    def test_gate_precedes_uuid_grant(self):
        gate = self.source.index("STAGING SAFETY GATE:")
        grant = self.source.index("grant_pioneer(sb, uid, reference, cid, verified=True)")
        self.assertLess(gate, grant)
        segment = self.source[gate:grant]
        self.assertIn("return send(cid,", segment)
        self.assertIn("Permohonan kekal pending", segment)

    def test_no_new_atomic_approval_claimed(self):
        # Explicitly documents the missing implementation.
        self.assertIn('reference = f"pioneer-payment:{uid}:{uuid.uuid4().hex}"', self.source)

if __name__ == "__main__":
    unittest.main()
