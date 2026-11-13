"""Original textbook readers for selected Telegram Science and History PdP."""
import re

from web.native_telegram_sejarah_2027_client import list_sejarah_lessons
from web.native_telegram_sequence_rph_client import list_native_lessons

SCIENCE_BOOKS = {
    1: (44, 47, "https://fliphtml5.com/rjler/yoow/BUKU_TEKS_SAINS_TAHUN_1_SEMAKAN/"),
    2: (52, 58, "https://fliphtml5.com/oudxg/ntkx/Buku_Teks_Digital_Sains_Tahun_2_SK_KSSR_Semakan_2007/"),
    3: (46, 54, "https://fliphtml5.com/ptqlr/bxbt/D3_BUKU_TEKS_SAINS_-_SAINS_SKDAM/"),
    4: (80, 85, "https://fliphtml5.com/itzsi/xpxe/BUKU_TEKS_SAINS_TAHUN_4/"),
    5: (84, 88, "https://fliphtml5.com/lbufr/faxv/TAHUN_5_SAINS_KSSR_BUKU_TEKS_Part_1/"),
    6: (85, 89, "https://fliphtml5.com/rmzqa/gqmb/Sains_T6_SK/"),
}
HISTORY_BOOKS = {
    4: "https://fliphtml5.com/jfuhh/cmqw/Buku_Teks_Sejarah_Tahun_4/",
    5: "https://fliphtml5.com/mlzri/alte/Sejarah_T5_SK/",
    6: "https://fliphtml5.com/itcew/pnmn",
}
PAGES = re.compile(r"Buku Teks m/s ([1-9][0-9]{0,2})(?:[–-]([1-9][0-9]{0,2}))?")


def textbook_reference(year, subject, unit, lesson):
    if subject == "SCIENCE" and year in SCIENCE_BOOKS:
        first, last, url = SCIENCE_BOOKS[year]
        match = re.fullmatch(rf"ST{year}-PDP-([0-9]{{3}})", lesson)
        if not match or not first <= int(match[1]) <= last:
            return None
        rows = list_native_lessons(year, subject, unit)
        name = "Sains"
    elif subject == "SEJARAH" and year in HISTORY_BOOKS and lesson in ("001", "002", "003"):
        rows = list_sejarah_lessons(year, unit)
        url = HISTORY_BOOKS[year]
        name = "Sejarah"
    else:
        return None

    matches = [row for row in rows if row["value"] == lesson]
    if len(matches) != 1:
        return None
    reference = matches[0].get("textbook_ref")
    pages = PAGES.fullmatch(reference) if isinstance(reference, str) else None
    if not pages or (pages[2] and int(pages[2]) <= int(pages[1])):
        return None
    printed = f"{pages[1]}–{pages[2]}" if pages[2] else pages[1]
    return {"type": "textbook", "title": f"Buku Teks {name} Tahun {year} • m/s {printed}",
            "url": url, "action": "Buka Buku Teks"}
