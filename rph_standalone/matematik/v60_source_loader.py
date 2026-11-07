"""Read-only, SHA-verified v60 Mathematik RPH Markdown source, 585 lessons.

Contents are an exact byte-for-byte transcription of the Markdown members of
CIKGULAJU_MATEMATIK_v60_585_RPH_OBJEKTIF_PBD_T4_STAGING.zip, SHA256:
a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271

NO database access, live Telegram/Web integration, file overwrite or RPT update.
The Word/PDF originals are NOT embedded here; the separate ZIP is needed for
those exact binary files. This source is not a production activation flag.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parent / "v60_source"
MANIFEST_NAME = "manifest.json"
SOURCE_SHA256 = "a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271"
YEARS = range(2, 7)

class SourceIntegrityError(RuntimeError):
    """Fail closed on any mismatch, missing lesson or corrupt source pack."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=1)
def manifest() -> dict:
    try:
        m = json.loads((ROOT / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SourceIntegrityError("Manifest RPH Matematik v60 tidak boleh dibaca") from exc
    if (m.get("source_archive_sha256") != SOURCE_SHA256
            or m.get("version") != "v60"
            or m.get("schema") != "cikgulaju.math_rph.v60.markdown.snapshot.v1"
            or m.get("final_ready") is not False
            or set(m.get("year_packs", {})) != {str(y) for y in YEARS}):
        raise SourceIntegrityError("Manifest tidak sepadan dengan sumber Matematik v60")
    return m


@lru_cache(maxsize=5)
def load_year(year: int) -> tuple[str, ...]:
    if type(year) is not int or year not in YEARS:
        raise ValueError("Tahun Matematik mesti integer 2 hingga 6")
    spec = manifest()["year_packs"][str(year)]
    if spec.get("lessons") != 117 or spec.get("first_lesson") != 1 or spec.get("last_lesson") != 117:
        raise SourceIntegrityError("Bilangan Lesson tidak tepat")
    filename = f"Tahun_{year}.json.zlib.b64.txt"
    if spec.get("filename") != filename:
        raise SourceIntegrityError("Nama sumber tahun tidak sepadan")
    try:
        text = (ROOT / filename).read_bytes()
        if _sha256(text) != spec["b64_text_sha256"]:
            raise SourceIntegrityError("Checksum pek teks tidak sepadan")
        compressed = base64.b64decode(b"".join(text.splitlines()), validate=True)
        if _sha256(compressed) != spec["compressed_sha256"]:
            raise SourceIntegrityError("Checksum kandungan mampat tidak sepadan")
        raw = zlib.decompress(compressed)
        if len(raw) != spec["raw_bytes"] or _sha256(raw) != spec["raw_sha256"]:
            raise SourceIntegrityError("Checksum sumber asal tidak sepadan")
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, zlib.error, KeyError) as exc:
        raise SourceIntegrityError(f"Gagal membaca RPH Tahun {year}") from exc
    if data.get("year") != year or len(data.get("lessons", [])) != 117:
        raise SourceIntegrityError("Senarai 117 Lesson tidak lengkap")
    lessons = []
    for number, item in enumerate(data["lessons"], start=1):
        md = item.get("markdown")
        if (item.get("lesson") != number or not isinstance(md, str)
                or _sha256(md.encode("utf-8")) != item.get("sha256")
                or not md.startswith(f"# RPH Matematik Tahun {year} — Lesson {number:03d}")):
            raise SourceIntegrityError(f"Lesson {year}/{number:03d} rosak atau tidak lengkap")
        lessons.append(md)
    return tuple(lessons)


def get_lesson(year: int, lesson: int) -> str:
    if type(lesson) is not int or not 1 <= lesson <= 117:
        raise ValueError("Nombor Lesson mesti integer 1 hingga 117")
    return load_year(year)[lesson - 1]


def verify_all() -> int:
    return sum(len(load_year(year)) for year in YEARS)


def export_markdown(destination: str | Path) -> int:
    """Explicit local export. Refuses existing destination; never writes any DB."""
    target = Path(destination)
    if target.exists():
        raise FileExistsError("Destinasi sudah wujud; tiada fail ditimpa")
    count = verify_all()
    target.mkdir(parents=True, exist_ok=False)
    for year in YEARS:
        directory = target / f"Tahun_{year}"
        directory.mkdir()
        for number, md in enumerate(load_year(year), start=1):
            (directory / f"lesson_{number:03d}.md").write_text(md, encoding="utf-8")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify/read exact Maths v60 RPH Markdown; no production activation")
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--verify", action="store_true", help="Validate all 585 lessons (default)")
    options.add_argument("--export", metavar="EMPTY_DEST_DIR", help="Extract 585 Markdown files into a new directory")
    options.add_argument("--lesson", nargs=2, type=int, metavar=("YEAR", "LESSON"), help="Print a lesson")
    args = parser.parse_args()
    if args.lesson:
        print(get_lesson(*args.lesson))
    elif args.export:
        print(f"Verified and exported {export_markdown(args.export)} Markdown lessons")
    else:
        print(f"Verified {verify_all()} exact RPH Markdown lessons from source SHA256 {SOURCE_SHA256}")

if __name__ == "__main__":
    main()
