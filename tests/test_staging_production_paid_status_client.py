"""Staging's opt-in bridge reads production paid rights without writing grants."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from web.provider_neutral_web_identity import (
    from_verified_google_account, from_verified_linked_telegram_account
)
from web.staging_production_paid_status_client import (
    PROD_URL, PaidStatusBridgeUnavailable, PaidStatusProductionAccountMissing,
    read_paid_status, verified_linked_paid_status, verified_paid_uid_for_rph
)

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
UID = 123456789
CFG = {"host": "cikgulaju-google-payments-staging.onrender.com",
       "supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co"}
TOKEN = "paid-status-staging-private-" + "x" * 52
PROFILE = {"account_id": ACCOUNT, "trial_remaining": 8}
GOOGLE = from_verified_google_account(ACCOUNT, PROFILE)
TELEGRAM = from_verified_linked_telegram_account(UID, ACCOUNT, PROFILE)


class FakeResponse:
    status = 200
    def __init__(self, obj):
        self.raw = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.raw[:n]


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def open(self, req, timeout):
        self.calls.append((req, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return FakeResponse(self.response)


class ProductionPaidBridgeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict("os.environ", {
            "CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED": "1",
            "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN})
        self.env.start()
        self.addCleanup(self.env.stop)

    def reply(self, *, uid=UID, lifetime=True, subscription=False, expiry=None):
        return {"source": "cikgulaju-prod-entitlements-v1",
                "telegram_user_id": uid, "registered": True,
                "rakan_pembangun_active": lifetime,
                "subscription_active": subscription,
                "subscription_expires_at": expiry}

    def test_strict_private_transport_verifies_single_linked_identity(self):
        sender = FakeTransport(self.reply())
        result = read_paid_status(UID, CFG, transport=sender)
        self.assertTrue(result["rakan_pembangun_active"])
        self.assertEqual(set(result), {"rakan_pembangun_active",
                                      "subscription_active", "subscription_expires_at"})
        req, timeout = sender.calls[0]
        self.assertEqual(req.full_url, PROD_URL)
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"telegram_user_id": UID})
        self.assertEqual(timeout, 30)
        self.assertEqual(req.get_header("Authorization"), "Bearer " + TOKEN)

    def test_render_cold_start_gateway_503_is_retried_once_then_verified(self):
        class ColdStart:
            def __init__(self, payload):
                self.calls = []
                self.payload = payload
            def open(self, req, timeout):
                self.calls.append((req.full_url, timeout))
                if len(self.calls) == 1:
                    raise HTTPError(req.full_url, 503, "Render waking", {}, None)
                return FakeResponse(self.payload)
        cold = ColdStart(self.reply(lifetime=True))
        with patch("web.staging_production_paid_status_client.time.sleep") as sleep:
            result = read_paid_status(UID, CFG, transport=cold)
        self.assertTrue(result["rakan_pembangun_active"])
        self.assertEqual(cold.calls, [(PROD_URL, 30), (PROD_URL, 12)])
        sleep.assert_called_once_with(4)

    def test_success_after_three_render_502_failures_without_caching_rights(self):
        class SleepingGateway:
            def __init__(self, payload):
                self.calls=[]
                self.payload=payload
            def open(self, req, timeout):
                self.calls.append(timeout)
                if len(self.calls)<=3:
                    raise HTTPError(req.full_url,502,"Web cold start",{},None)
                return FakeResponse(self.payload)
        gateway=SleepingGateway(self.reply())
        with patch("web.staging_production_paid_status_client.time.sleep") as sleep:
            paid=read_paid_status(UID,CFG,transport=gateway)
        self.assertTrue(paid["rakan_pembangun_active"])
        self.assertEqual(gateway.calls,[30,12,12,12])
        self.assertEqual([c.args[0] for c in sleep.call_args_list],[4,8,12])

    def test_four_transient_502_errors_are_fail_closed(self):
        class FailedGateway:
            def __init__(self):
                self.calls=0
            def open(self, req, timeout):
                self.calls+=1
                raise HTTPError(req.full_url,502,"unavailable",{},None)
        source=FailedGateway()
        with (patch("web.staging_production_paid_status_client.time.sleep"),
              self.assertRaises(PaidStatusBridgeUnavailable)):
            read_paid_status(UID,CFG,transport=source)
        self.assertEqual(source.calls,4)

    def test_invalid_private_token_401_is_never_retried(self):
        class Unauthorized:
            def __init__(self):
                self.calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise HTTPError(req.full_url, 401, "Invalid token", {}, None)
        sender = Unauthorized()
        with (patch("web.staging_production_paid_status_client.time.sleep") as sleep,
              self.assertRaises(PaidStatusBridgeUnavailable) as error):
            read_paid_status(UID, CFG, transport=sender)
        self.assertEqual(sender.calls, 1)
        self.assertIn("401", str(error.exception))
        sleep.assert_not_called()

    def test_bridge_not_enabled_or_staging_project_wrong_never_contacts_source(self):
        sender = FakeTransport(self.reply())
        with patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED": "0"}):
            with self.assertRaises(PaidStatusBridgeUnavailable):
                read_paid_status(UID, CFG, transport=sender)
        with self.assertRaises(PaidStatusBridgeUnavailable):
            read_paid_status(UID, {**CFG, "supabase_url": "https://soxakntcanbycjoygrcx.supabase.co"},
                             transport=sender)
        self.assertEqual(sender.calls, [])

    def test_wrong_subject_and_malformed_response_fail_closed(self):
        for response in (self.reply(uid=UID+1), self.reply(subscription=True),
                         self.reply(expiry="2020-01-01T00:00:00+00:00"),
                         {"source": "cikgulaju-prod-entitlements-v1"},
                         {**self.reply(), "extra": "untrusted"}):
            with self.subTest(response=response):
                with self.assertRaises(PaidStatusBridgeUnavailable):
                    read_paid_status(UID, CFG, transport=FakeTransport(response))
        with self.assertRaises(ValueError):
            read_paid_status(True, CFG, transport=FakeTransport(self.reply()))

    def test_active_subscription_with_valid_future_expiry(self):
        expiry=(datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        result=read_paid_status(UID, CFG, transport=FakeTransport(
            self.reply(lifetime=False,subscription=True,expiry=expiry)))
        self.assertTrue(result["subscription_active"])
        self.assertEqual(result["subscription_expires_at"],expiry)

    def test_google_and_telegram_both_verify_same_production_status(self):
        for actor in (GOOGLE, TELEGRAM):
            with (self.subTest(provider=actor.provider),
                patch("web.google_telegram_link_staging_routes._link_status",
                      return_value={"linked": True, "staging_only": True,
                                    "telegram_user_id": str(UID)}) as mapping,
                patch("web.staging_production_paid_status_client.read_paid_status",
                      return_value={"rakan_pembangun_active": True,
                                    "subscription_active": False,
                                    "subscription_expires_at": None}) as read):
                result=verified_linked_paid_status(actor, CFG)
                self.assertEqual(result["production_access_status"], "verified")
                self.assertTrue(result["production_access_verified"])
                self.assertTrue(result["production_rakan_pembangun_active"])
                mapping.assert_called_once_with(CFG, ACCOUNT)
                read.assert_called_once_with(UID, CFG)

    def test_identity_mismatch_or_unlinked_or_backend_down_never_grant(self):
        with patch("web.google_telegram_link_staging_routes._link_status",
                   return_value={"linked": False}):
            result=verified_linked_paid_status(GOOGLE,CFG)
            self.assertEqual(result["production_access_status"], "not_linked")
        with patch("web.google_telegram_link_staging_routes._link_status",
                   return_value={"linked": True, "telegram_user_id": str(UID+1)}):
            result=verified_linked_paid_status(TELEGRAM,CFG)
            self.assertEqual(result["production_access_status"], "source_unavailable")
            self.assertFalse(result["production_access_verified"])
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "telegram_user_id": str(UID)}),
              patch("web.staging_production_paid_status_client.read_paid_status",
                    side_effect=PaidStatusBridgeUnavailable("network"))):
            result=verified_linked_paid_status(GOOGLE,CFG)
            self.assertEqual(result["production_access_status"], "source_unavailable")
            self.assertFalse(result["production_access_verified"])
            self.assertNotIn("production_rakan_pembangun_active",result)

    def test_generation_paid_entitlement_requires_fresh_link_and_production_proof(self):
        for actor in (GOOGLE, TELEGRAM):
            with (self.subTest(actor=actor.provider),
                  patch("web.google_telegram_link_staging_routes._link_status",
                        return_value={"linked": True, "staging_only": True,
                                      "telegram_user_id": str(UID)}),
                  patch("web.staging_production_paid_status_client.read_paid_status",
                        return_value={"rakan_pembangun_active": True,
                                      "subscription_active": False,
                                      "subscription_expires_at": None}) as reader):
                self.assertEqual(verified_paid_uid_for_rph(actor, CFG), UID)
                reader.assert_called_once_with(UID, CFG)

    def test_generation_nonpaid_or_unlinked_only_uses_free_quota(self):
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": False, "staging_only": True}),
              patch("web.staging_production_paid_status_client.read_paid_status") as read):
            self.assertIsNone(verified_paid_uid_for_rph(GOOGLE, CFG))
            read.assert_not_called()
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "staging_only": True,
                                  "telegram_user_id": str(UID)}),
              patch("web.staging_production_paid_status_client.read_paid_status",
                    return_value={"rakan_pembangun_active": False,
                                  "subscription_active": False,
                                  "subscription_expires_at": None})):
            self.assertIsNone(verified_paid_uid_for_rph(GOOGLE, CFG))

    def test_generation_cannot_pay_when_revoked_stale_or_wrong_telegram(self):
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "staging_only": True,
                                  "telegram_user_id": str(UID + 1)}),
              patch("web.staging_production_paid_status_client.read_paid_status") as read):
            with self.assertRaises(PaidStatusBridgeUnavailable):
                verified_paid_uid_for_rph(TELEGRAM, CFG)
            read.assert_not_called()
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "staging_only": True,
                                  "telegram_user_id": str(UID)}),
              patch("web.staging_production_paid_status_client.read_paid_status",
                    side_effect=PaidStatusBridgeUnavailable("offline"))):
            with self.assertRaises(PaidStatusBridgeUnavailable):
                verified_paid_uid_for_rph(GOOGLE, CFG)
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED":"0"}),
              patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "staging_only": True,
                                  "telegram_user_id": str(UID)})):
            with self.assertRaises(PaidStatusBridgeUnavailable):
                verified_paid_uid_for_rph(GOOGLE, CFG)

    def test_google_only_free_trial_never_requires_render_bridge(self):
        with (patch.dict("os.environ",
                         {"CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED": "0"}),
              patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": False, "staging_only": True}) as mapping,
              patch("web.staging_production_paid_status_client.read_paid_status") as bridge):
            self.assertIsNone(verified_paid_uid_for_rph(GOOGLE, CFG))
            mapping.assert_called_once_with(CFG, ACCOUNT)
            bridge.assert_not_called()

    def test_unlinked_telegram_session_cannot_inherit_google_trial(self):
        with patch("web.google_telegram_link_staging_routes._link_status",
                   return_value={"linked": False, "staging_only": True}):
            with self.assertRaises(PaidStatusBridgeUnavailable):
                verified_paid_uid_for_rph(TELEGRAM, CFG)

    def test_production_user_missing_is_not_a_false_negative_entitlement(self):
        with (patch("web.google_telegram_link_staging_routes._link_status",
                    return_value={"linked": True, "telegram_user_id": str(UID)}),
              patch("web.staging_production_paid_status_client.read_paid_status",
                    side_effect=PaidStatusProductionAccountMissing("missing"))):
            result=verified_linked_paid_status(GOOGLE,CFG)
            self.assertEqual(result["production_access_status"], "production_account_missing")
            self.assertFalse(result["production_access_verified"])


if __name__ == "__main__":
    unittest.main()
