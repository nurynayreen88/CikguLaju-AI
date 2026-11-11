"""Read an opt-in, local CikguLaju Pendidikan Islam V5 staging bundle.

This module DOES NOT install a Telegram handler, change database content, or
mark teacher-review materials as ready. Callers must opt into `staging=True`.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

_LESSON_PATTERN = re.compile(r"T([2-6])-L(\d{3})$")
_DOCX_PREFIX = b"PK\x03\x04"
_PDF_PREFIX = b"%PDF-"

class BundleValidationError(ValueError):
    """Fail closed when a staging bundle is unavailable or inconsistent."""

class PIBundleV5:
    def __init__(self, archive_path: str | Path, *, staging: bool = False):
        if staging is not True:
            raise PermissionError("Draft Pendidikan Islam bundle requires staging=True")
        self.path = Path(archive_path).resolve(strict=True)
        with zipfile.ZipFile(self.path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise BundleValidationError("Duplicate ZIP member names")
            if archive.testzip() is not None:
                raise BundleValidationError("Corrupted ZIP")
            try:
                manifest = json.loads(archive.read("KATALOG/manifest_v5.json"))
                catalog = json.loads(archive.read("KATALOG/catalog.json"))
            except (KeyError, ValueError) as exc:
                raise BundleValidationError("Missing or invalid catalog/manifest") from exc
            if manifest.get("status") != "STAGING_NOT_READY" or manifest.get("publication_status") != "DRAF":
                raise BundleValidationError("Unexpected release manifest status")
            if manifest.get("rph_count") != 696 or len(catalog) != 696:
                raise BundleValidationError("Expected 696 unique lessons")
            lookup = {}
            guides = 0
            for rec in catalog:
                year, lesson = rec.get("tahun"), rec.get("lesson")
                if type(year) is not int or year not in range(2,7):
                    raise BundleValidationError("Invalid year")
                if type(lesson) is not int or lesson < 1 or lesson > 200:
                    raise BundleValidationError("Invalid lesson")
                ident = f"T{year}-L{lesson:03d}"
                if rec.get("lesson_id") != ident or not _LESSON_PATTERN.fullmatch(ident):
                    raise BundleValidationError("Mismatched lesson ID")
                if (year, lesson) in lookup:
                    raise BundleValidationError("Duplicate lesson")
                name = rec.get("rph_path", "")
                if (not isinstance(name, str) or not name.startswith("RPH_2027/")
                    or not name.endswith(".docx") or name not in names
                    or f"PI_T{year}_LESSON_{lesson:03d}_" not in name):
                    raise BundleValidationError("Wrong or missing RPH path")
                checksum = rec.get("rph_sha256", "")
                if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
                    raise BundleValidationError("Invalid RPH SHA256")
                guide = rec.get("optional_tasmi_guide")
                if guide is not None:
                    if (not isinstance(guide, str) or not guide.startswith("PANDUAN_TASMI/")
                        or not guide.endswith(".pdf") or guide not in names
                        or rec.get("optional_guide_is_official") is not False):
                        raise BundleValidationError("Missing or misleading optional guide")
                    guides += 1
                lookup[year,lesson] = rec
            if len(lookup) != 696 or guides != 8:
                raise BundleValidationError("Incorrect catalog totals")
            self._catalog = lookup
            self._manifest = manifest

    @property
    def manifest(self):
        return dict(self._manifest)

    def lesson_ids(self):
        return tuple(sorted(self._catalog))

    def read_rph(self, year: int, lesson: int, *, allow_teacher_draft: bool = False):
        if allow_teacher_draft is not True:
            raise PermissionError("Teacher-review RPH cannot be served as READY")
        record = self._catalog[year, lesson]
        with zipfile.ZipFile(self.path) as archive:
            data = archive.read(record["rph_path"])
        if not data.startswith(_DOCX_PREFIX):
            raise BundleValidationError("Invalid DOCX")
        if hashlib.sha256(data).hexdigest() != record["rph_sha256"]:
            raise BundleValidationError("RPH SHA mismatch")
        return data

    def read_optional_tasmi_guide(self, year: int, lesson: int):
        record = self._catalog[year, lesson]
        path = record["optional_tasmi_guide"]
        if path is None:
            return None
        with zipfile.ZipFile(self.path) as archive:
            data = archive.read(path)
        if not data.startswith(_PDF_PREFIX):
            raise BundleValidationError("Invalid PDF guide")
        return data

    def record(self, year: int, lesson: int):
        return dict(self._catalog[year, lesson])