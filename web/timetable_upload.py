"""Shared limits and response contract for the timetable reader."""
import re

MAX_UPLOAD = 8 * 1024 * 1024
MAX_RESULT = 65536
READER_PATH = "/internal/timetable/v1/read"
DAYS = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")
TIME = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")


class UnreadableTimetable(ValueError):
    pass


class TimetableReaderUnavailable(RuntimeError):
    pass


def upload_mime(data):
    if not 0 < len(data) <= MAX_UPLOAD:
        raise UnreadableTimetable("Pilih satu fail jadual berukuran maksimum 8 MB.")
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise UnreadableTimetable("Pilih gambar JPG, PNG, WebP atau fail PDF.")


def validate_result(result):
    if not isinstance(result, dict) or set(result) != {"entries", "uncertain", "unreadable_pages"}:
        raise TimetableReaderUnavailable
    entries = result["entries"]
    if not isinstance(entries, list) or not 0 < len(entries) <= 80:
        raise TimetableReaderUnavailable
    for field in ("uncertain", "unreadable_pages"):
        if type(result[field]) is not int or not 0 <= result[field] <= 1200:
            raise TimetableReaderUnavailable
    for row in entries:
        limits = {"day": 6, "start": 5, "end": 5, "class_name": 40, "subject": 60}
        if not isinstance(row, dict) or row.keys() != limits.keys():
            raise TimetableReaderUnavailable
        if any(not isinstance(row[key], str) or len(row[key]) > length
               or any(ord(char) < 32 for char in row[key]) for key, length in limits.items()):
            raise TimetableReaderUnavailable
        if (row["day"] not in DAYS or not TIME.fullmatch(row["start"])
                or not TIME.fullmatch(row["end"]) or row["start"] >= row["end"]):
            raise TimetableReaderUnavailable
    return result
