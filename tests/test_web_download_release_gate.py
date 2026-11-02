"""Web release gate must remain closed until all durable safeguards exist."""
import unittest
from web.download_release_gate import public_download_ready, RETRY_SAFETY_REQUIREMENTS


class DownloadReleaseGateTests(unittest.TestCase):
    def test_each_missing_prerequisite_blocks_release(self):
        fields = ("durable_idempotency", "delivery_replay",
                  "production_layout_parity", "approval_verified",
                  "trial_policy_verified")
        for missing in fields:
            with self.subTest(missing=missing):
                flags = {name: True for name in fields}
                flags[missing] = False
                self.assertFalse(public_download_ready(**flags))

    def test_only_complete_gate_can_pass(self):
        self.assertTrue(public_download_ready(
            durable_idempotency=True, delivery_replay=True,
            production_layout_parity=True, approval_verified=True,
            trial_policy_verified=True))

    def test_unknown_or_missing_check_cannot_pass(self):
        with self.assertRaises(ValueError):
            public_download_ready(
                durable_idempotency=1, delivery_replay=True,
                production_layout_parity=True, approval_verified=True,
                trial_policy_verified=True)
        self.assertGreaterEqual(len(RETRY_SAFETY_REQUIREMENTS), 6)


if __name__ == "__main__":
    unittest.main()
