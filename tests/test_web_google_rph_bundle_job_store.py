"""Staging RPH private uploads, retry consistency, and atomic finalization."""
from io import BytesIO
import json
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import Mock
from zipfile import ZipFile, ZIP_DEFLATED

from web.google_rph_bundle_job_store import (
    prepare_private_bundle, selection_fingerprint, publish_rendered_bundle,
    BundleCommitUnconfirmed,
)
from web.provider_neutral_web_identity import from_verified_google_account

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
JOB = "a3d7e1bb-f5b2-4529-9d10-144e11831144"
CONF = {"supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co",
        "staging_service_key": "sb_secret_" + "x" * 42}
PDF = b"%PDF-1.7\n" + b"x"*730 + b"\n%%EOF\n"


def word():
    b = BytesIO()
    with ZipFile(b, "w", ZIP_DEFLATED) as file:
        file.writestr("[Content_Types].xml", "<Types/>" * 20)
        file.writestr("word/document.xml", "<document>" + "x"*800 + "</document>")
    return b.getvalue().ljust(520,b" ")


class Reply:
    status=200
    def __init__(self, data, status=200):
        self.status=status
        self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n): return self.data[:n]


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.actor = from_verified_google_account(
            ACCOUNT,{"account_id":ACCOUNT,"trial_remaining":10})
        self.selection=selection_fingerprint(
            {"year":3,"subject":"ENGLISH","unit":"Unit One","lesson":"e-3-003"},
            {"class":"3 Amanah","date":"2026-11-07",
             "time":"08:00 - 09:00","students":"28"})
        self.calls=[]

    def rpc(self,req,timeout):
        self.calls.append(req.full_url)
        if req.full_url.endswith("/prepare_web_rph_bundle_staging"):
            return Reply(json.dumps({"job_id":JOB,"status":"prepared"}).encode())
        if req.full_url.endswith("/complete_web_rph_bundle_staging"):
            payload=json.loads(req.data)
            self.assertEqual(payload["p_account_id"],ACCOUNT)
            self.assertEqual(payload["p_job_id"],JOB)
            self.assertEqual(len(payload["p_manifest_sha256"]),64)
            return Reply(json.dumps({
                "job_id":JOB,"status":"ready","allowed":True,
                "remaining":9,"replayed":False,"access_mode":"trial"
            }).encode())
        raise AssertionError("Unrecognized RPC")

    def upload(self,req,timeout):
        self.calls.append(req.full_url)
        self.assertEqual(req.get_method(),"POST")
        self.assertNotIn("Authorization",dict(req.header_items()))
        self.assertEqual(dict(req.header_items())["X-upsert"],"false")
        return Reply(b'{"Key":"private"}',status=201)

    def test_prepare_returns_job_without_debit(self):
        result=prepare_private_bundle(
            CONF,self.actor,JOB,self.selection,transport=self.rpc)
        self.assertEqual(result,{"job_id":JOB,"status":"prepared"})
        self.assertEqual(len(self.calls),1)
        self.assertIn("prepare_web_rph_bundle_staging",self.calls[0])

    def test_full_bundle_is_uploaded_before_atomic_debit(self):
        response=publish_rendered_bundle(
            CONF,self.actor,JOB,self.selection,word(),PDF,
            rpc_transport=self.rpc,upload_transport=self.upload)
        self.assertTrue(response["allowed"])
        self.assertEqual(response["remaining"],9)
        self.assertEqual(len(self.calls),4)
        self.assertIn("prepare_web_rph_bundle_staging",self.calls[0])
        self.assertIn("/storage/v1/object/web-rph-bundles-staging/",self.calls[1])
        self.assertTrue(self.calls[1].endswith(".docx"))
        self.assertTrue(self.calls[2].endswith(".pdf"))
        self.assertIn("complete_web_rph_bundle_staging",self.calls[3])

    def test_pdf_upload_failure_cannot_call_quota(self):
        def upload(req,timeout):
            self.calls.append(req.full_url)
            if req.full_url.endswith(".pdf"):
                raise URLError("offline")
            return Reply(b"{}",201)
        with self.assertRaises(BundleCommitUnconfirmed):
            publish_rendered_bundle(CONF,self.actor,JOB,self.selection,word(),PDF,
                    rpc_transport=self.rpc,upload_transport=upload)
        self.assertEqual(len(self.calls),3)
        self.assertFalse(any("complete_web_rph" in x for x in self.calls))

    def test_replayed_job_returns_stored_artifacts_without_new_charge(self):
        def rpc(req,timeout):
            return Reply(json.dumps({"job_id":JOB,"status":"ready"}).encode())
        upload=Mock(side_effect=AssertionError("must not upload"))
        result=publish_rendered_bundle(
            CONF,self.actor,JOB,self.selection,word(),PDF,
            rpc_transport=rpc,upload_transport=upload)
        self.assertEqual(result,{"job_id":JOB,"status":"ready","already_ready":True})
        upload.assert_not_called()

    def test_identical_private_files_can_be_reused_after_timeout(self):
        def upload(req,timeout):
            self.calls.append(req.full_url)
            raise HTTPError(req.full_url,409,"already exists",{},None)
        def existing(cfg,account,job,fmt):
            self.assertEqual((account,job),(ACCOUNT,JOB))
            return word() if fmt=="word" else PDF
        result=publish_rendered_bundle(
            CONF,self.actor,JOB,self.selection,word(),PDF,
            rpc_transport=self.rpc,upload_transport=upload,
            existing_reader=existing)
        self.assertEqual(result["status"],"ready")
        self.assertEqual(len(self.calls),4)

    def test_different_existing_file_rejected_without_charge(self):
        def conflict(req,timeout):
            self.calls.append(req.full_url)
            raise HTTPError(req.full_url,409,"already exists",{},None)
        with self.assertRaises(BundleCommitUnconfirmed):
            publish_rendered_bundle(
                CONF,self.actor,JOB,self.selection,word(),PDF,
                rpc_transport=self.rpc,upload_transport=conflict,
                existing_reader=lambda cfg,acc,jid,fmt:b"not matching")
        self.assertFalse(any("complete_web_rph" in x for x in self.calls))

    def test_invalid_native_word_is_not_stored_or_charged(self):
        upload=Mock(side_effect=AssertionError("no external requests"))
        with self.assertRaises(ValueError):
            publish_rendered_bundle(
                CONF,self.actor,JOB,self.selection,b"not docx"*100,PDF,
                rpc_transport=upload,upload_transport=upload)
        upload.assert_not_called()

    def test_account_and_job_are_never_accepted_without_proof(self):
        for bogus in (None,{},False):
            with self.subTest(bogus=bogus), self.assertRaises(ValueError):
                prepare_private_bundle(CONF,bogus,JOB,self.selection,
                                       transport=Mock(side_effect=AssertionError("no call")))
        for malformed in ("", "fake-job",ACCOUNT.upper()):
            with self.subTest(malformed=malformed),self.assertRaises(ValueError):
                prepare_private_bundle(CONF,self.actor,malformed,self.selection,
                                       transport=Mock(side_effect=AssertionError("no call")))


if __name__ == "__main__":
    unittest.main()
