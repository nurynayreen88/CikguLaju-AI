"""Offline regression checks for Rakan Pembangun approval. No network or DB writes."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pioneer_telegram.py"


class RakanPembangunApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(SOURCE))

    def test_uuid_generation_is_executable_code(self):
        assigns = [
            node for node in ast.walk(self.tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "reference" for t in node.targets)
        ]
        self.assertTrue(any(
            isinstance(n.value, ast.JoinedStr)
            and "uuid.uuid4()" in ast.get_source_segment(self.source, n.value)
            for n in assigns
        ), "Approval must generate a unique reference as executable Python")

    def test_grant_before_local_approval(self):
        grant = self.source.index("grant_pioneer(sb, uid, reference, cid, verified=True)")
        mark = self.source.index('ns["_mark_payment_request"](rid, "approved", cid, "Rakan Pembangun RM10')
        self.assertLess(grant, mark)

    def test_receipt_required(self):
        self.assertIn('req.get("notes") != "proof_received_admin_notified"', self.source)

    def test_transaction_reuse_is_not_yet_verified(self):
        # This is a known missing safeguard, not a passing end-to-end security test.
        self.assertIn('reference = f"pioneer-payment:{uid}:{uuid.uuid4().hex}"', self.source)


if __name__ == "__main__":
    unittest.main()
