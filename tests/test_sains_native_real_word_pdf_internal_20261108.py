"""Authenticated, true Flask-route Word/PDF smoke; no user billing or DB writes."""
from __future__ import annotations

import os
from flask import Flask
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tools.sains_native_internal_real_documents_smoke_20261108 import (
    check_real_native_api, log_when_enabled, _check_doc, ENABLED,
)
from web.sains_342_native_staging_source_20261108 import install
from web.telegram_verified_sequence_rph_bridge import (
    create_native_sequence_rph_blueprint,
)
from test_sains_342_native_staging_source_20261108 import fake_runtime


SECRET="p"*48


def make_app():
    runtime=fake_runtime()
    app=Flask("sains_real_native_smoke_test")
    runtime.app=app
    with patch.dict(os.environ,{
        "CIKGULAJU_SAINS_342_INTERNAL_REVIEW":"1",
        "CIKGULAJU_CURRICULUM_DEPLOYMENT":"staging",
        "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW":"0",
        "RENDER_SERVICE_ID":"",
    }):
        assert install(runtime) is True
    runtime.CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE=False
    app.register_blueprint(create_native_sequence_rph_blueprint(runtime))
    return runtime


class TestNativeScienceRealDocumentGate(unittest.TestCase):
    def test_actual_flask_http_bearer_to_word_pdf_for_all_five_years(self):
        runtime=make_app()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":SECRET,
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
        }):
            report=check_real_native_api(runtime)
        self.assertEqual(set(report["years"]),{"2","3","4","5","6"})
        self.assertTrue(report["five_years_actual_render_passed"],report)
        self.assertFalse(report["credits_modified"])
        self.assertFalse(report["database_modified"])
        self.assertFalse(report["authoring_342_release_approved"])
        for year,status in report["years"].items():
            self.assertTrue(status["units_ready"])
            self.assertTrue(status["lesson_ready"])
            self.assertTrue(status["source_available"])
            self.assertTrue(status["word_ready"])
            self.assertTrue(status["pdf_ready"])
            self.assertGreater(status["word_size_bytes"],1000)
            self.assertGreater(status["pdf_size_bytes"],1000)
            self.assertTrue(status["sample_pdp"].startswith(f"SCI-Y{year}-PDP-"))

    def test_disabled_flag_never_calls_render_or_checks_secret(self):
        calls={"n":0}
        class NoRuntime:
            def __getattr__(self,key):
                calls["n"]+=1
                raise AssertionError("No access permitted when disabled")
        with patch.dict(os.environ,{ENABLED:"0"}):
            self.assertIsNone(log_when_enabled(NoRuntime()))
        self.assertEqual(calls["n"],0)

    def test_enabled_smoke_never_overrides_academic_draft_hold(self):
        runtime=make_app()
        with patch.dict(os.environ,{
            ENABLED:"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":SECRET,
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
        }):
            report=log_when_enabled(runtime)
            self.assertTrue(report["five_years_actual_render_passed"],report)
            self.assertFalse(report["authoring_342_release_approved"])
        runtime.CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE=True
        with patch.dict(os.environ,{ENABLED:"1"}):
            self.assertIsNone(log_when_enabled(runtime))

    def test_without_secret_never_sends_document(self):
        runtime=make_app()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"",
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
        }):
            with self.assertRaises(RuntimeError):
                check_real_native_api(runtime)

    def test_http_errors_never_count_as_real_doc_success(self):
        runtime=make_app()
        for fmt in ("word","pdf"):
            with self.subTest(fmt=fmt):
                with runtime.app.test_request_context():
                    from flask import jsonify,make_response
                    response=make_response(jsonify({"error":"Not ready"}),503)
                    with self.assertRaises(ValueError):
                        _check_doc(fmt,response)


if __name__=="__main__":
    unittest.main()
