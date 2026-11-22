"""Pinned KP2027 Year-1 SK asset contracts, NOT public release authorization.

Curriculum sources have been checked, but original archives remain QA pending
academic and live quota-gated Web E2E. Do not expose source bytes or signed URLs.
No Flask/Telegram import or database writing is permitted from this module.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from types import MappingProxyType
from zipfile import ZipFile, BadZipFile


PACKS = MappingProxyType({
    "ALAM": {"object":"kp2027/sk/tahun-1/alam/v10/64-lesson-word-pdf.zip",
             "bytes":4673901,"sha256":"b1ae8dcab0894bacc894d7fb310ff5ece27a1077e84846a64a86a61235d3a8ef",
             "files":64,"groups":{"A":64,"B":64},"per_group_file":False,"prefix":"ALAM"},
    "MATH": {"object":"kp2027/sk/tahun-1/matematik/v11/249-lesson-word-pdf.zip",
             "bytes":18105236,"sha256":"07003ed9b0037359ff30a8956ba328d3d5eb76ad44417bf1be5be18d74fe50cf",
             "files":249,"groups":{"A":125,"B":124},"per_group_file":True,"prefix":"MATH"},
    "BM_SK": {"object":"kp2027/sk/tahun-1/bahasa-melayu/v12/353-lesson-word-pdf.zip",
             "bytes":25507411,"sha256":"392cca683d87aeb72cac9b7fe48ddeaa210d0c973d9d4850e2acb180c6cf8349",
             "files":353,"groups":{"A":178,"B":175},"per_group_file":True,"prefix":"BM_SK"},
    "PJ": {"object":"kp2027/sk/tahun-1/pendidikan-jasmani/v12/127-lesson-word-pdf.zip",
           "bytes":9277365,"sha256":"e6fde0aa186fd7deb0738cb56d101381814019cdbc6e4cab38144148ba987111",
           "files":127,"groups":{"A":64,"B":63},"per_group_file":True,"prefix":"PJ"},
})

BUCKET = "cikgulaju-materials"
RELEASE_STATUS = "QA_HOLD_ACADEMIC_WEB_E2E"


class UnreleasedKP2027(Exception):
    """No approved release manifest, no download; don't substitute a Drive URL."""


def pack_spec(subject):
    if not isinstance(subject,str) or subject not in PACKS:
        raise ValueError("Invalid KP2027 Tahun 1 SK subject")
    return PACKS[subject]


def expected_members(subject):
    p = pack_spec(subject)
    names=set()
    for kind,ext in (("Word","docx"),("PDF","pdf")):
        if not p["per_group_file"]:
            names.update(f"{kind}/{p['prefix']}_T1_LESSON{i:03d}.{ext}" for i in range(1,p['files']+1))
        else:
            for group,limit in p["groups"].items():
                names.update(f"{kind}/{p['prefix']}_T1_{group}_LESSON{i:03d}.{ext}" for i in range(1,limit+1))
    return names


def verify_qa_zip(subject, data):
    """Offline byte-level release preflight only; cannot confer user access."""
    p=pack_spec(subject)
    if not isinstance(data,bytes) or len(data)!=p["bytes"] or sha256(data).hexdigest()!=p["sha256"]:
        raise UnreleasedKP2027("Unrecognized or modified QA archive")
    try:
        with ZipFile(BytesIO(data)) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or z.testzip() is not None:
                raise UnreleasedKP2027("Duplicate or invalid ZIP members")
            expected=expected_members(subject)
            actual=set(names)
            if not expected.issubset(actual) or len(actual)!=len(expected)+3:
                raise UnreleasedKP2027("Incomplete or additional KP2027 archive files")
            if any(".." in x or x.startswith("/") or "\\" in x for x in names):
                raise UnreleasedKP2027("Unsafe ZIP member name")
            for name in expected:
                content=z.read(name)
                if not 1000<=len(content)<=10_000_000:
                    raise UnreleasedKP2027("Invalid RPH size")
                if name.endswith(".pdf") and not content.startswith(b"%PDF-"):
                    raise UnreleasedKP2027("Invalid PDF data")
                if name.endswith(".docx"):
                    with ZipFile(BytesIO(content)) as word:
                        if word.testzip() is not None or "word/document.xml" not in word.namelist():
                            raise UnreleasedKP2027("Invalid Word document")
        return {"subject":subject,"lesson_documents":p["files"],"formats":("word","pdf"),"status":RELEASE_STATUS}
    except (OSError,BadZipFile,ValueError,KeyError) as exc:
        raise UnreleasedKP2027("Invalid KP2027 QA archive") from exc


def get_download(*, subject, group, lesson, file_format, account=None, approved=False):
    """Never serves QA files, not even to an authenticated or paying account.

    Future production code must have separate, independently signed academic
    release manifest, a replayable user-bound charging ledger and verified
    private Storage objects before exposing any file.
    """
    pack_spec(subject)
    if group not in ("A","B") or type(lesson) is not int or lesson < 1 or lesson > PACKS[subject]["groups"][group]:
        raise ValueError("Invalid KP2027 group/lesson")
    if file_format not in ("word","pdf"):
        raise ValueError("Invalid KP2027 format")
    raise UnreleasedKP2027("KP2027 Year 1 content remains QA; public download not enabled")
