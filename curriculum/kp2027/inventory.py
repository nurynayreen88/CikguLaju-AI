"""KP2027 Year 1/Form 1 source gate, independent of KSSR/KSSM production DB.

A document *link* does not authorize SK/SP extraction, RPT or RPH.
No runtime AI, no old curriculum fallback, no network, no DB mutation.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
INVENTORY = ROOT / "source_inventory_20261106.json"
LEVELS = ("Tahun 1", "Tingkatan 1")
EVIDENCE = frozenset({
    "TRAINING_PORTAL", "REPORT_ONLY", "DOCUMENT_LISTED",
    "DOCUMENT_LINK_INDEXED", "TENDER_ONLY", "SUBJECT_OFFERING_CONFIRMED",
})
CURRICULUM = "KP2027"
STATUS = "AUDIT_ONLY_NO_RPH"


class KP2027SourceUnverified(ValueError):
    """A real source is missing, mismatched, or not manually approved."""


def _approved_link(url):
    if not isinstance(url, str) or not 10 < len(url) < 1400:
        return False
    p = urlsplit(url)
    return (p.scheme == "https" and bool(p.hostname)
            and p.hostname in ("www.moe.gov.my", "moe.gov.my", "sites.google.com",
                               "drive.google.com", "repositori.bpk.moe-dl.edu.my",
                               "linktr.ee")
            and not p.username and not p.password and not p.fragment)


def load_inventory(path=INVENTORY):
    path = Path(path)
    if (path.is_symlink() or not path.is_file()
            or not 100 <= path.stat().st_size <= 300_000):
        raise KP2027SourceUnverified("Registry source unavailable")
    raw = path.read_bytes()
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise KP2027SourceUnverified("Invalid registry document") from exc
    if (data.get("schema_version") != "1.0"
            or data.get("curriculum") != CURRICULUM
            or data.get("release_status") != STATUS
            or not isinstance(data.get("subject_records"), list)):
        raise KP2027SourceUnverified("Unknown curriculum registry or release state")
    policy = data.get("policy", {})
    if not all(policy.get(field) is True for field in (
            "no_legacy_substitution", "no_inferred_standards",
            "no_silent_fallback", "document_download_required",
            "per_standard_page_audit_required", "legacy_db_untouched",
            "deploy_flag_default_off")):
        raise KP2027SourceUnverified("Unsafe source policy")
    seen = set()
    subjects = {}
    for row in data["subject_records"]:
        if not isinstance(row, dict):
            raise KP2027SourceUnverified("Malformed subject row")
        key = (row.get("level"), row.get("subject"))
        if (key[0] not in LEVELS or not isinstance(key[1], str)
                or not 2 <= len(key[1]) < 100 or key in seen):
            raise KP2027SourceUnverified("Unknown level or duplicate subject")
        seen.add(key)
        if (row.get("evidence_status") not in EVIDENCE
                or not _approved_link(row.get("source_index_url"))):
            raise KP2027SourceUnverified("Invalid source metadata")
        link = row.get("document_link_url")
        if link is not None and not _approved_link(link):
            raise KP2027SourceUnverified("Invalid DK link")
        if (row.get("document_pdf_downloaded") is not False
                or row.get("document_original_sha256") is not None
                or row.get("document_version_confirmed") is not False
                or row.get("standards_extracted") is not False
                or row.get("standards_audited") is not False
                or row.get("standard_count_verified") != 0
                or row.get("rpt_ready") is not False
                or row.get("rph_ready") is not False
                or row.get("readiness") != "WAITING_ORIGINAL_DK"):
            raise KP2027SourceUnverified("Unapproved programme falsely marked READY")
        subjects[key] = row
    if not subjects or not all(any(level == k[0] for k in subjects)
                                for level in LEVELS):
        raise KP2027SourceUnverified("Both levels must be represented")
    if ("Tahun 1", "Sejarah") in subjects:
        raise KP2027SourceUnverified("Sejarah not a KP2027 Year 1 subject")
    if ("Tahun 1", "Alam dan Manusia") not in subjects:
        raise KP2027SourceUnverified("Missing Year 1 integrated subject")
    for programme in data.get("programmes", []):
        if (programme.get("level") not in LEVELS
                or programme.get("as_subject") is not False
                or not _approved_link(programme.get("source_index_url"))):
            raise KP2027SourceUnverified("Unapproved character-programme mapping")
    return data, hashlib.sha256(raw).hexdigest()


def levels():
    return list(LEVELS)


def subjects_for(level):
    if level not in LEVELS:
        raise ValueError("KP2027 only enabled for Year 1 and Form 1 in 2027")
    data, digest = load_inventory()
    subjects = [
        {
            "id": r["id"], "subject": r["subject"], "level": r["level"],
            "evidence_status": r["evidence_status"], "readiness": r["readiness"],
            "source_index_url": r["source_index_url"],
            "document_link_url": r["document_link_url"],
            "document_pdf_downloaded": False, "rpt_ready": False, "rph_ready": False,
        }
        for r in data["subject_records"] if r["level"] == level
    ]
    return subjects, digest


def status_for(level, subject, expected_digest=None):
    if level not in LEVELS or not isinstance(subject, str):
        raise ValueError("Invalid level or subject")
    rows, digest = subjects_for(level)
    if expected_digest is not None and (
            not isinstance(expected_digest, str)
            or not re.fullmatch("[0-9a-f]{64}", expected_digest)
            or digest != expected_digest):
        raise KP2027SourceUnverified("KP2027 source version changed")
    found = [row for row in rows if row["subject"] == subject]
    if len(found) != 1:
        raise KP2027SourceUnverified("Subject not indexed")
    return dict(found[0], source_digest=digest, curriculum=CURRICULUM)


def verified_standards_for(level, subject, *, strict=True):
    """Never manufacture SK/SP or permit KSSR/KSSM fallback for KP2027."""
    status_for(level, subject)
    if strict:
        raise KP2027SourceUnverified(
            "No original KP2027 DK PDF/standard page audit for requested subject")
    return []


def request_rph(level, subject, *args, **kwargs):
    status_for(level, subject)
    raise KP2027SourceUnverified(
        "KP2027 RPH disabled until original DK, SP/SPi and source-page verification")


def request_rpt(level, subject, *args, **kwargs):
    status_for(level, subject)
    raise KP2027SourceUnverified(
        "KP2027 RPT disabled until original DK, SP/SPi and source-page verification")
