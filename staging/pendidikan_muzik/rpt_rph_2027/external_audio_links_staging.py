"""Read-only, source-backed external audio links for Music Years 2–6.

This only opens original Google Drive *view* pages. It never sends audio bytes,
creates a direct-download URL, grants a license, or consumes RPH credits.
Only strict numeric textbook references are mapped to numbered source files;
a matching filename is not evidence that the recording is authentic/correct.
Requires a separate live-release review; not wired to production WSGI.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ORIGINAL_FOLDER = {
    2: "1UGaW_PK5VO9QlahVKNMC9gXZ9-tC2hoJ",
    3: "1WToAfezUq1S9lzWcIuJMh7An2YLSehkH",
    4: "14jrZyKwWsf0Q2QiC61YfTdDx1KUjT_lf",
    5: "1G_cX6podVJTRZ9qRpEpU4EDtZhxOs9MC",
    6: "1V3QIhEo3jhmVTV1reTb9bIuSGj75VpdO",
}
AUDIO_COUNTS = {2: 89, 3: 82, 4: 118, 5: 161, 6: 167}
GOOGLE_ID = re.compile(r"^[a-zA-Z0-9_-]{10,100}$")
STRICT_NUMBERS = re.compile(
    r"^([1-9]\d{0,2})(?:\s*[-–—]\s*([1-9]\d{0,2}))?"
    r"(?:\s*\((?:halaman\s+[1-9]\d{0,2}|rujukan bercetak)\))?$",
    re.IGNORECASE,
)
SOURCE_STATUS = "PAUTAN_ASAL_BELUM_DISAHKAN_AKSES_LESEN_DAN_AUDIO"


def numbers_from_printed_reference(text):
    """Reject notes, choices (5 atau 8), title ranges and ambiguous subtracks."""
    if not isinstance(text, str):
        return ()
    match = STRICT_NUMBERS.fullmatch(text.strip())
    if match is None:
        return ()
    start, stop = int(match.group(1)), int(match.group(2) or match.group(1))
    if start > stop or stop - start > 20:
        return ()
    return tuple(range(start, stop + 1))


def _source_catalog(year, *, root=ROOT):
    """Defensively validate 617 original URLs; no dynamic URL construction."""
    if type(year) is not int or year not in ORIGINAL_FOLDER:
        return None
    try:
        path = Path(root) / f"audio_source_index_year{year}_20261106.json"
        if path.is_symlink():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if (data.get("schema") != 1 or data.get("year") != year
                or data.get("source_folder") != "https://drive.google.com/drive/folders/" + ORIGINAL_FOLDER[year]
                or data.get("scope") != "EXTERNAL_SOURCE_LINKS_ONLY"
                or any(data.get(k) is not False for k in (
                    "access_verified", "audio_content_verified", "redistribution_permitted"
                ))):
            return None
        items = data.get("files")
        if not isinstance(items, list) or len(items) != AUDIO_COUNTS[year]:
            return None
        seen_ids = set()
        tracks = {}
        for item in items:
            if not isinstance(item, dict):
                return None
            file_id = item.get("file_id")
            url = item.get("source_url")
            mime = item.get("mime_type")
            title = item.get("title")
            track = item.get("track")
            if (not isinstance(file_id, str) or not GOOGLE_ID.fullmatch(file_id)
                    or not isinstance(url, str)
                    or not url.startswith("https://drive.google.com/file/d/" + file_id + "/view")
                    or "?" in url and not url.endswith("?usp=drivesdk")
                    or not isinstance(title, str) or not 1 <= len(title) <= 255
                    or not isinstance(mime, str) or not mime.startswith("audio/")
                    or file_id in seen_ids):
                return None
            seen_ids.add(file_id)
            if track is not None:
                if type(track) is not int or not 1 <= track <= 300:
                    return None
                # Some title variations can share a track; refuse ambiguous mapping.
                tracks.setdefault(track, []).append({
                    "track": track, "title": title, "url": url,
                    "file_id": file_id,
                })
        return tracks
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        return None


def links_for_pdp(year, pdp, *, root=ROOT):
    """Return *links only* when every printed track maps uniquely; otherwise [].

    No source link is ever equivalent to a licensed CikguLaju audio download.
    """
    if (type(year) is not int or year not in ORIGINAL_FOLDER
            or type(pdp) is not int or not 1 <= pdp <= 35):
        return []
    try:
        manifest_file = Path(root) / f"year{year}" / "pdp_manifest.json"
        if manifest_file.is_symlink():
            return []
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if (manifest.get("academic_year") != 2027
                or manifest.get("audio_verified") is not False
                or len(manifest.get("pdps", ())) != 35):
            return []
        row = manifest["pdps"][pdp - 1]
        if (row.get("pdp_id") != f"MZ-Y{year}-{pdp:02d}"
                or row.get("pdp") != pdp
                or row.get("source_book_audio_file_verified") is not False):
            return []
        nums = numbers_from_printed_reference(
            row.get("source_book_audio_numbers_printed", "")
        )
        if not nums:
            return []
        tracks = _source_catalog(year, root=root)
        if tracks is None or any(len(tracks.get(n, ())) != 1 for n in nums):
            return []
        return [
            dict(tracks[n][0], status=SOURCE_STATUS, download_available=False)
            for n in nums
        ]
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError):
        return []


def audio_link_action(year, pdp, *, root=ROOT):
    """Web-friendly data adapter; never describe a link as verified or downloadable."""
    links = links_for_pdp(year, pdp, root=root)
    if not links:
        return {
            "available": False, "button_label": None,
            "notice": "Audio sumber belum dapat dipadankan dengan yakin.",
            "links": [], "download_available": False,
        }
    return {
        "available": True,
        "button_label": "Buka Audio Sumber",
        "notice": (
            "Pautan sumber asal (bukan fail CikguLaju). "
            "Padanan mengikut nombor sahaja; audio, akses dan hak edar belum disahkan. "
            "Jika pemilik membenarkan, gunakan fungsi Google Drive untuk membukanya."
        ),
        "links": links,
        "download_available": False,
    }
