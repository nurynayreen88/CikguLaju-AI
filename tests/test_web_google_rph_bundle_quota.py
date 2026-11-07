"""Never debit a staging Google trial unless both RPH outputs exist."""
from io import BytesIO
import json
import unittest
from unittest.mock import Mock
from zipfile import ZipFile, ZIP_DEFLATED

from web.provider_neutral_web_identity import from_verified_google_account
from web.google_rph_bundle_quota import (
    BundleNotRendered, BundleChargeUnconfirmed,
    rendered_bundle_sha256, server_generation_reference,
    charge_successful_google_bundle,
)

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
SECRET = "sb_secret_" + "x" * 45
CONFIG = {"supabase_url":"https://eqrcjlnvcytkgazptbor.supabase.co",
          "staging_service_key":SECRET}


def document_word():
    stream=BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>" * 10)
        archive.writestr("word/document.xml", "<document>" + "x" * 800 + "</document>")
    return stream.getvalue().ljust(520,b" ")


def document_pdf():
    return b"%PDF-1.7\n" + b"0" * 600 + b"\n%%EOF\n"


class Reply:
    status = 200
    def __init__(self, data):
        self.body=json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self, limit): return self.body[:limit]


class BundleQuotaTests(unittest.TestCase):
    def setUp(self):
        self.actor=from_verified_google_account(
            ACCOUNT, {"account_id":ACCOUNT,"trial_remaining":10})
        self.ref=server_generation_reference()

    def test_manifest_stable_for_exact_pair(self):
        original=rendered_bundle_sha256(document_word(),document_pdf())
        self.assertEqual(len(original),64)
        self.assertEqual(original,rendered_bundle_sha256(document_word(),document_pdf()))
        self.assertNotEqual(original,rendered_bundle_sha256(document_word(),document_pdf()+b"x"))

    def test_generation_ref_is_canonical_uuid(self):
        import uuid
        self.assertEqual(str(uuid.UUID(self.ref)),self.ref)

    def test_missing_malformed_docs_no_debit(self):
        bogus=[(b"",document_pdf()),(b"xxxx"*200,document_pdf()),
               (document_word(),b""),(document_word(),b"x"*750),
               (document_word(),b"%PDF-1.7"+"x".encode()*600)]
        network=Mock(side_effect=AssertionError("must never debit"))
        for word,pdf in bogus:
            with self.subTest(word_len=len(word),pdf_len=len(pdf)):
                with self.assertRaises(BundleNotRendered):
                    charge_successful_google_bundle(
                        CONFIG,self.actor,self.ref,word,pdf,transport=network)
        network.assert_not_called()

    def test_paid_and_trial_rpc_response_validation(self):
        details={"allowed":True,"remaining":9,
                 "replayed":False,"access_mode":"trial"}
        calls=[]
        def responder(req,timeout):
            calls.append(req)
            return Reply(details)
        actual=charge_successful_google_bundle(
            CONFIG,self.actor,self.ref,document_word(),document_pdf(),transport=responder)
        self.assertEqual(actual,details)
        self.assertEqual(len(calls),1)
        headers=dict(calls[0].header_items())
        self.assertEqual(headers.get("Apikey"),SECRET)
        self.assertNotIn("Authorization",headers)
        self.assertIn("/rpc/consume_web_rph_bundle_staging",calls[0].full_url)
        posted=json.loads(calls[0].data)
        self.assertEqual(posted["p_account_id"],ACCOUNT)
        self.assertEqual(posted["p_generation_ref"],self.ref)
        self.assertEqual(len(posted["p_manifest_sha256"]),64)

    def test_ambiguous_backend_failure_cannot_claim_uncharged(self):
        from urllib.error import URLError
        with self.assertRaises(BundleChargeUnconfirmed):
            charge_successful_google_bundle(CONFIG,self.actor,self.ref,
                document_word(),document_pdf(),
                transport=lambda req,timeout:(_ for _ in ()).throw(URLError("reset")))
        with self.assertRaises(BundleChargeUnconfirmed):
            charge_successful_google_bundle(CONFIG,self.actor,self.ref,
                document_word(),document_pdf(),
                transport=lambda req,timeout:Reply({"allowed":True, "remaining":True,
                                                    "replayed":False,"access_mode":"trial"}))

    def test_unverified_actor_cannot_reach_quota(self):
        for actor in (None, {}, ACCOUNT, True):
            with self.subTest(actor=actor), self.assertRaises(ValueError):
                charge_successful_google_bundle(CONFIG,actor,self.ref,
                    document_word(),document_pdf(),
                    transport=Mock(side_effect=AssertionError("network")))

    def test_uuid_ref_from_browser_cannot_be_arbitrary(self):
        for ref in ("my-lesson", "", 1234, None):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                charge_successful_google_bundle(CONFIG,self.actor,ref,
                    document_word(),document_pdf(),
                    transport=Mock(side_effect=AssertionError("network")))


if __name__=="__main__":
    unittest.main()
