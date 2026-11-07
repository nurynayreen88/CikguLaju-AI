"""Fail-closed per-PdP academic release gate for Sains Tahun 2–6.

No RPH source is public merely because it exists in main or its Word/PDF
passed technical CI. All 342 are HOLD until individual, exact-source
academic evidence exists. This module is read-only; it does NOT install a
runtime overlay, write DB/user credits, create approvals or authorize a
production deployment.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re

from tools.audit_rph80_sains_first_20261107 import EXPECTED, WEIGHTS, grade_from_evidence

ROOT=Path(__file__).resolve().parents[1]
APPROVALS=ROOT/"audits/sains_342_individual_academic_release_approvals_20261108.json"
EVIDENCE_SHA_FIELDS=("dskp","textbook_pages","specific_activities_pbd",
                     "rendered_word_pdf","runtime_parity")
SP_PATTERN=re.compile(r"[1-9]\d*\.[1-9]\d*\.[1-9]\d*")
DIGEST_PATTERN=re.compile(r"[0-9a-f]{64}")
RELEASE_STATUS="FINAL_READY"


class SainsRPHNotApproved(PermissionError):
    """Requested new authored Sains RPH is not approved for public delivery."""


def content_sha256(source_text):
    """Bind a review to the exact authored RPH source, never to a PdP number alone."""
    if isinstance(source_text,str):
        payload=source_text.encode("utf-8")
    elif isinstance(source_text,bytes):
        payload=source_text
    else:
        raise TypeError("Science RPH must be a str or bytes source")
    if len(payload)<150:
        raise ValueError("Insufficient source-specific RPH text")
    return sha256(payload).hexdigest()


def _expected_code(year,pdp_code):
    if type(year) is not int or year not in EXPECTED:
        return False
    if not isinstance(pdp_code,str):
        return False
    match=re.fullmatch(r"SCI-Y([2-6])-PDP-(\d{3})",pdp_code)
    return bool(match and int(match.group(1))==year
                and 1<=int(match.group(2))<=EXPECTED[year])


def _identity(record):
    year=record.get("year")
    code=record.get("pdp_code")
    sk=record.get("sk")
    sp=record.get("sp")
    if not _expected_code(year,code):
        return False
    if (not isinstance(sk,str) or not isinstance(sp,str)
            or not SP_PATTERN.fullmatch(sp) or sp.rsplit(".",1)[0]!=sk):
        return False
    return bool(DIGEST_PATTERN.fullmatch(str(record.get("source_sha256") or "")))


def _verified_evidence(record):
    evidence=record.get("evidence")
    scores=record.get("scores")
    if not isinstance(evidence,dict) or not isinstance(scores,dict):
        return None
    if any(not DIGEST_PATTERN.fullmatch(str(evidence.get(k) or ""))
           for k in EVIDENCE_SHA_FIELDS):
        return None
    reviewer=evidence.get("reviewer")
    signed=evidence.get("review_date")
    if not isinstance(reviewer,str) or len(reviewer.strip())<5:
        return None
    if not isinstance(signed,str):
        return None
    try:
        reviewed_date=date.fromisoformat(signed)
    except ValueError:
        return None
    if not date(2026,1,1)<=reviewed_date<=date.today():
        return None
    if evidence.get("review_is_for_exact_source_sha") is not True:
        return None
    if not (record.get("teacher_panitia_approved") is True
            and record.get("safety_reviewed") is True
            and record.get("pbd_individual_evidence_reviewed") is True
            and record.get("authenticated_web_telegram_e2e_passed") is True):
        return None
    score=grade_from_evidence(scores,evidence)
    if score is None or score<80:
        return None
    return score


def _read_approvals(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    expected={"schema_version","subject","scope","original_source_count",
              "source_counts","approval_policy","approved"}
    if (set(data)!=expected or data["schema_version"]!=1
        or data["subject"]!="Sains" or data["original_source_count"]!=342
        or data["source_counts"]!={str(year):count for year,count in EXPECTED.items()}
        or not isinstance(data["approved"],list)):
        raise ValueError("Unrecognized Sains academic release registry")
    codes=set()
    for rec in data["approved"]:
        if not isinstance(rec,dict) or not _identity(rec):
            raise ValueError("Invalid Sains release approval identity")
        if rec["pdp_code"] in codes:
            raise ValueError("Duplicate Sains approval "+rec["pdp_code"])
        codes.add(rec["pdp_code"])
        if rec.get("status")!=RELEASE_STATUS or _verified_evidence(rec) is None:
            raise ValueError("Incomplete Sains academic release approval")
    return data["approved"]


def approved_count(*,registry_path=APPROVALS):
    """Verified records in registry, not automatically-public RPHs."""
    return len(_read_approvals(registry_path))


def can_publish_sains_rph(*,year,pdp_code,sk,sp,source_text,source_status,
                          registry_path=APPROVALS):
    """Return True only for an exact, independently approved source identity.

    Call this at the future delivery boundary before advertising or returning
    a newly authored Sains RPH. Other subjects' legacy paths are untouched.
    Source status is separately required to be FINAL_READY (never DRAF/HOLD).
    """
    if not _expected_code(year,pdp_code) or source_status!=RELEASE_STATUS:
        return False
    if not isinstance(sk,str) or not isinstance(sp,str):
        return False
    if not SP_PATTERN.fullmatch(sp) or sp.rsplit(".",1)[0]!=sk:
        return False
    digest=content_sha256(source_text)
    entries=_read_approvals(registry_path)
    matching=[r for r in entries if r["pdp_code"]==pdp_code]
    if len(matching)!=1:
        return False
    row=matching[0]
    return bool(row["year"]==year and row["sk"]==sk and row["sp"]==sp
                and row["source_sha256"]==digest
                and row["status"]==RELEASE_STATUS
                and _verified_evidence(row) is not None)


def require_approved_sains_rph(**kwargs):
    if not can_publish_sains_rph(**kwargs):
        raise SainsRPHNotApproved("Sains RPH is not individually approved for public release")
    return True


if __name__=="__main__":
    total=approved_count()
    print(f"SAINS_RELEASE_GATE: {total}/342 individually approved; "
          "staging documents and CI successes alone are NEVER public approval")
