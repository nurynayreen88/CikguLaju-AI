"""Read-only HTTP adapter for a separately verified authoritative curriculum API.

The endpoint must be deployed alongside the Telegram runtime (or backed by its
authoritative datastore). This module never silently falls back to a snapshot.
No credentials, API URLs, or file paths are returned to browser clients.
"""
from urllib.parse import urlsplit, urlencode
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler
import json
from web.authoritative_curriculum_source import (
    CurriculumKey, SharedSourceUnavailable, validate_curriculum_key,
)


class _StdlibResponse:
    def __init__(self, response):
        self.status_code = response.status
        self._body = response.read(1024 * 1024 + 1)
        if len(self._body) > 1024 * 1024:
            raise ValueError('oversized curriculum response')

    def json(self):
        return json.loads(self._body)


class _StdlibTransport:
    def get(self, url, *, params, headers, timeout, allow_redirects):
        # No redirect handler: do not forward bearer tokens to another host.
        class _NoRedirect(__import__('urllib.request', fromlist=['HTTPRedirectHandler']).HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, newurl):
                return None
        query = urlencode(params)
        req = Request(url + '?' + query, headers=headers, method='GET')
        opener = build_opener(HTTPHandler(), HTTPSHandler(), _NoRedirect())
        with opener.open(req, timeout=timeout[1]) as response:
            return _StdlibResponse(response)


class AuthoritativeHttpCurriculumSource:
    def __init__(self, base_url, token, *, transport=None):
        parts = urlsplit(base_url)
        if (parts.scheme != "https" or not parts.hostname or parts.username
                or parts.password or parts.query or parts.fragment or parts.port
                or not token or len(token) < 32):
            raise ValueError("Verified HTTPS source and strong service token required")
        self.base_url = base_url.rstrip("/")
        self.token = token
        if transport is None:
            transport = _StdlibTransport()
        self.transport = transport

    def _read(self, endpoint, params):
        try:
            response = self.transport.get(
                self.base_url + "/internal/curriculum/v1/" + endpoint,
                params=params,
                headers={"Authorization": "Bearer " + self.token,
                         "Accept": "application/json"},
                timeout=(3, 8), allow_redirects=False,
            )
            if response.status_code != 200:
                raise SharedSourceUnavailable("Authoritative source unavailable")
            data = response.json()
            if not isinstance(data, dict) or data.get("source") != "telegram-runtime-v1":
                raise SharedSourceUnavailable("Unverified curriculum response")
            if not isinstance(data.get("items"), list) or len(data["items"]) > 500:
                raise SharedSourceUnavailable("Invalid curriculum response")
            if not all(isinstance(item, dict) for item in data["items"]):
                raise SharedSourceUnavailable("Invalid curriculum records")
            return data["items"]
        except Exception as exc:
            # Requests/network/JSON errors are all unavailable-source failures.
            # Never expose credentials or internal endpoint details to callers.
            raise SharedSourceUnavailable("Authoritative source unavailable") from exc

    def list_subjects(self, year):
        self._validate_year(year)
        return self._read("subjects", {"year": year})

    def list_units(self, year, subject_code, component=None):
        self._validate_year(year)
        self._validate_subject(subject_code)
        params = {"year": year, "subject": subject_code}
        if subject_code == "PJPK":
            if component not in ("PJ", "PK"):
                raise ValueError("PJPK requires verified component")
            params["component"] = component
        elif component not in (None, ""):
            raise ValueError("Component only applies to PJPK")
        return self._read("units", params)

    def list_lessons(self, year, subject_code, unit, component=None):
        self._validate_year(year)
        self._validate_subject(subject_code)
        if not isinstance(unit, str) or not unit.strip() or len(unit) > 300:
            raise ValueError("Invalid unit")
        params = {"year": year, "subject": subject_code, "unit": unit}
        if subject_code == "PJPK":
            if component not in ("PJ", "PK"):
                raise ValueError("PJPK requires verified component")
            params["component"] = component
        elif component not in (None, ""):
            raise ValueError("Component only applies to PJPK")
        return self._read("lessons", params)

    def get_approved_materials(self, key):
        validate_curriculum_key(key)
        return self._read("approved-materials", {
            "year": key.year, "subject": key.subject_code, "lesson": key.lesson_id,
        })

    @staticmethod
    def _validate_year(year):
        if type(year) is not int or year not in range(1, 7):
            raise ValueError("Invalid year")

    @staticmethod
    def _validate_subject(subject):
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 32:
            raise ValueError("Invalid subject")
