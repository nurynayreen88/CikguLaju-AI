"""Read-only, source-backed external audio links for Music Years 2–6.

Source URLs point to the original Google Drive files. Direct download links
require a matching PdP and a successful signed-out file check.
"""
from __future__ import annotations

import json
from functools import lru_cache
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
NUMBER_LIST = re.compile(r"[1-9][0-9]{0,2}(?:\s*,\s*[1-9][0-9]{0,2}){1,20}")
SOURCE_STATUS = "PAUTAN_ASAL_BELUM_DISAHKAN_AKSES_LESEN_DAN_AUDIO"
SOURCE_DOWNLOAD = "https://drive.usercontent.google.com/download?id={}&export=download"
VERIFIED_YEAR4_TRACKS = {
    21: (
        (66, "1tgNnRXXJC6SVvvVRodSQgt1o464hLe7V", "Corak Irama 1"),
        (67, "1tuAys02dAzGePDIVns-gHQ8Xq0DaSwfJ", "Corak Irama 2"),
    ),
    24: (
        (90, "1BY6ptHJRhLH8luim6uPKEavBfZL2NdET", "Contoh Soalan 1"),
        (91, "1vvPxP8YHa3XpsxDgdwqT91NxUp2ODnPg", "Contoh Jawapan 1"),
        (92, "1D2YGkXNHlwnD3pIynjZnkd-HtwrqiMbY", "Contoh Jawapan 2"),
    ),
}


def numbers_from_printed_reference(text):
    """Read a checked numeric range or explicit list of original audio numbers."""
    if not isinstance(text, str):
        return ()
    text = text.strip()
    if NUMBER_LIST.fullmatch(text):
        tracks = tuple(map(int, text.split(",")))
        return tracks if tuple(sorted(set(tracks))) == tracks and tracks[-1] <= 300 else ()
    match = STRICT_NUMBERS.fullmatch(text)
    if match is None:
        return ()
    start, stop = int(match.group(1)), int(match.group(2) or match.group(1))
    if start > stop or stop > 300 or stop - start > 20:
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
            if track is not None and (type(track) is not int or not 1 <= track <= 300):
                return None
            # Unnumbered tracks can be matched only by the exact catalog title.
            key = track if track is not None else title.casefold()
            tracks.setdefault(key, []).append({
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
        keys = numbers_from_printed_reference(
            row.get("source_book_audio_numbers_printed", "")
        )
        named_titles = {}
        if not keys:
            named = row.get("source_book_audio_named")
            if not isinstance(named, list) or not 1 <= len(named) <= 21:
                return []
            for item in named:
                if not isinstance(item, dict):
                    return []
                catalog_title, title = item.get("catalog_title"), item.get("title")
                if not all(isinstance(value, str) and 1 <= len(value) <= 255
                           for value in (catalog_title, title)):
                    return []
                key = catalog_title.casefold()
                if key in named_titles:
                    return []
                named_titles[key] = title
            keys = tuple(named_titles)
        tracks = _source_catalog(year, root=root)
        if tracks is None or any(len(tracks.get(key, ())) != 1 for key in keys):
            return []
        return [
            dict(tracks[key][0], title=named_titles.get(key, tracks[key][0]["title"]),
                 status=SOURCE_STATUS, download_available=False)
            for key in keys
        ]
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError):
        return []


def audio_link_action(year, pdp, *, root=ROOT):
    """Distinguish score review, verified source downloads and view links."""
    links = links_for_pdp(year, pdp, root=root)
    checked_downloads = _checked_downloads(Path(root)).get(str(year), {}).get(str(pdp))
    if isinstance(checked_downloads, list) and checked_downloads == [x["file_id"] for x in links]:
        links = [dict(item, download_url=SOURCE_DOWNLOAD.format(item["file_id"]))
                 for item in links]
    links = [item for item in links if item["track"] is not None or "download_url" in item]
    checked = VERIFIED_YEAR4_TRACKS.get(pdp) if year == 4 else None
    if checked:
        if [(item["track"], item["file_id"]) for item in links] != [
            (track, file_id) for track, file_id, _ in checked
        ]:
            links = []
        else:
            links = [dict(item, title=title, status="PADANAN_SKOR_DISAHKAN")
                     for item, (_, _, title) in zip(links, checked)]
            return {
                "available": True, "button_label": "Buka Audio Sumber",
                "notice": "Rakaman sepadan dengan skor buku teks. Pautan membuka fail pada sumber asal.",
                "links": links, "download_available": False, "content_verified": True,
            }
    if not links:
        return {
            "available": False, "button_label": None,
            "notice": "Audio sumber belum dapat dipadankan dengan yakin.",
            "links": [], "download_available": False, "content_verified": False,
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
        "content_verified": False,
    }


@lru_cache(maxsize=4)
def _checked_downloads(root):
    try:
        path = root / "audio_source_download_audit_20261120.json"
        if path.is_symlink():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        coverage = data.get("verified_pdp_files")
        if (data.get("schema") == 1 and isinstance(coverage, dict)
                and all(isinstance(rows, dict) for rows in coverage.values())):
            return coverage
    except (OSError, ValueError, AttributeError):
        pass
    return {}
