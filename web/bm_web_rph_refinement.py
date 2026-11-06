"""BM Web-native RPH refinement from the selected Telegram verified PdP.

Only the signed BM Web source state opts in. No database writes or global
Telegram BM callback changes. Existing SK/SP, class/date, source identifiers,
and other-subject documents remain authoritative.
"""
from __future__ import annotations

import re
from functools import wraps

SOURCE = "verified_pdp_sequence"
_STATE_FLAG = "_bm_web_native_source"
_NUMBERED_FIELDS = ("SET INDUKSI", "AKTIVITI UTAMA", "PENUTUP",
                    "PEMULIHAN / PENGAYAAN")

# The old generator uses these cross-subject shells even for a BM lesson.
# Do not replace a source-specific document which is already more detailed.
_GENERIC_CUES = (
    "teroka dengan", "cabaran konteks sebenar", "stesen pembelajaran",
    "bahan manipulatif", "bahan yang sesuai", "kad tugasan berlainan",
    "situasi harian ringkas", "bimbingan buku teks/visual",
    "tugasan berperingkat", "contoh yang sepadan dengan sp",
    "latihan pendek berperingkat", "saya buat, kita buat",
    "memanipulasi/meneliti bahan",
    # Recognized topic-neutral stock headings from the actual BM v26.00 RPH.
    "siapa/apakah ini?", "ikut dan ulang", "tanya jawab bergambar",
    "exit lisan", "dengar untuk maklumat", "soal jawab berpandu",
    "kongsi semula", "pbd lisan", "kenal unsur", "latihan kreatif",
    "maklum balas (10 minit)",
)


def split_numbered_steps(value):
    """Put actual numbered tasks on fresh lines without breaking SP/decimals.

    Preserve real line breaks and all step wording. Handles legacy one-line
    '1. Guru ... 2. Murid ...' and inline 'Aktiviti 2' headings. The rule
    requires a task verb following the ordinal to avoid changing 1.1.1, dates,
    the book page range, or numbered curriculum codes.
    """
    result = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    action = r"(?:Guru|Murid|Secara|Pasangan|Kumpulan|Setiap|Beberapa|Teacher|Pupils)\b"
    result = re.sub(
        r"(?<=\S)[ \t]*(?=(?:[1-9]|1\d)\.\s*" + action + ")",
        "\n", result, flags=re.I,
    )
    result = re.sub(
        r"(?<=\S)[ \t]*(?=(?:Aktiviti|Activity)\s+[1-9]\d*\s*[–—:-])",
        "\n", result, flags=re.I,
    )
    return "\n".join(line.rstrip() for line in result.split("\n")).strip()


def complete_verified_bm_standards(database_path, year, standards):
    """Backfill empty SP texts from the *same* verified v26.00 DB.

    Some verified_pdp_sequence rows retain codes but empty sk_text/sp_text.
    Verify exact year/subject/SK/SP against curriculum_standards; never use
    a different subject's same code or substitute an unverified paragraph.
    Read-only and fail closed on missing/ambiguous authoritative wording.
    """
    import sqlite3
    from pathlib import Path
    original = tuple(dict(item) for item in standards)
    try:
        path = Path(database_path)
        if not path.is_file() or type(year) is not int or year not in range(1, 7):
            return original
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            conn.execute("PRAGMA query_only=ON")
            improved = []
            for item in original:
                sk = str(item.get("sk_code") or "").strip()
                sp = str(item.get("sp_code") or "").strip()
                if not sk or not sp:
                    improved.append(item)
                    continue
                rows = conn.execute(
                    """SELECT DISTINCT sk_text,sp_text FROM curriculum_standards
                       WHERE year_label=? AND subject='Bahasa Melayu'
                         AND sk_code=? AND sp_code=? AND verified=1""",
                    (f"Tahun {year}", sk, sp)
                ).fetchall()
                if len(rows) == 1 and rows[0][1] and str(rows[0][1]).strip():
                    entry = dict(item)
                    if not str(entry.get("sp_text") or "").strip():
                        entry["sp_text"] = str(rows[0][1]).strip()
                    if not str(entry.get("sk_text") or "").strip() and rows[0][0]:
                        entry["sk_text"] = str(rows[0][0]).strip()
                    improved.append(entry)
                else:
                    improved.append(item)
            return tuple(improved)
    except (sqlite3.Error, OSError, ValueError, TypeError):
        return original


def _family(sp_text):
    s = " ".join(str(sp_text or "").lower().split())
    if not s:
        return None
    if any(v in s for v in ("imlak", "dikte")):
        return "imlak"
    if any(v in s for v in ("mengedit", "menyunting", "membetulkan kesalahan")):
        return "sunting"
    if any(v in s for v in ("menulis secara mekanis", "tulisan berangkai",
                            "menyalin", "membentuk huruf")):
        return "mekanis"
    if any(v in s for v in ("menulis", "menghasilkan", "mengarang", "membina perenggan",
                            "membina ayat")):
        return "menulis"
    if any(v in s for v in ("membaca", "meneliti kandungan teks", "memahami bahan bacaan")):
        return "membaca"
    if any(v in s for v in ("mendengar", "mengecam sebutan", "mengecam bunyi")):
        return "mendengar"
    if any(v in s for v in ("bertutur", "berkomunikasi", "bersoal jawab",
                            "menceritakan", "bercerita", "berbual")):
        return "bertutur"
    if any(v in s for v in ("pantun", "sajak", "syair", "gurindam", "mendeklamasi",
                            "seni bahasa")):
        return "seni bahasa"
    if any(v in s for v in ("kata nama", "kata kerja", "kata adjektif",
                            "kata sendi", "kata ganda", "imbuhan", "tatabahasa",
                            "membina ayat berdasarkan")):
        return "tatabahasa"
    return None


def _task(family, topic, reference, sp_text=""):
    """Observable BM-specific tasks without inventing textbook passages."""
    t = f"‘{topic}’"
    source = f" ({reference})" if reference else ""
    low_sp = " ".join(str(sp_text or "").lower().split())
    if family == "mendengar" and "ayat tunggal" in low_sp and "ayat majmuk" in low_sp:
        return (
            f"Guru membacakan ayat tunggal dan ayat majmuk yang dipilih daripada "
            f"bahan {t}{source}. Murid mendengar, mengecam sebutan dan "
            "menyatakan jenis ayat tanpa membaca teks terlebih dahulu.",
            "Guru membacakan semula ayat dalam urutan berbeza. Pasangan murid "
            "menunjukkan kad 'tunggal' atau 'majmuk', mengulang sebutan "
            "dan membetulkan perbezaan yang didengar.",
            "Guru menyebut empat ayat lagi daripada konteks yang sama. "
            "Murid mengecam jenis ayat dan menyebut semula sekurang-kurangnya "
            "tiga ayat dengan sebutan tepat secara individu."
        )
    if family == "mendengar" and all(x in low_sp for x in ("soalan", "suruhan", "pesanan", "permintaan")):
        return (
            f"Guru menyampaikan empat jenis ujaran berdasarkan situasi {t}{source}: "
            "soalan, suruhan, pesanan dan permintaan. Murid mendengar dan "
            "menentukan respons yang sesuai bagi setiap satu.",
            "Murid berpasangan: seorang menyebut ujaran berdasarkan kad "
            "situasi rakan, pasangannya memberikan respons; mereka bertukar "
            "peranan dan membaiki respons yang kurang tepat.",
            "Secara individu murid mendengar empat ujaran baharu dan memberi "
            "respons lisan yang sesuai. Guru merekod ketepatan isi respons "
            "serta kesantunan bahasa."
        )
    if family == "bertutur" and "peribahasa" in low_sp:
        return (
            f"Guru memilih peribahasa yang benar-benar terkandung dalam bahan "
            f"{t}{source}; murid menjelaskan maksud berdasarkan konteks cerita.",
            "Pasangan murid membina dialog ringkas tentang situasi dalam "
            f"{t}, menyelitkan peribahasa daripada bahan asal dengan makna "
            "yang tepat, kemudian berlatih sebutan dan intonasi.",
            "Murid bercerita atau mengujarkan dialog kepada kelas dengan "
            "sekurang-kurangnya satu peribahasa yang digunakan secara tepat. "
            "Guru menilai isi, maksud peribahasa dan penyampaian."
        )
    if family == "imlak":
        return (
            f"Guru memilih frasa sebenar daripada bahan {t}{source}, "
            "membacanya tanpa memperlihatkan ejaan; murid menulis secara imlak.",
            "Pasangan menyemak ejaan dan tanda baca menggunakan frasa rujukan; "
            "setiap murid membetulkan kesilapan pada hasil sendiri.",
            "Guru mendikte tiga frasa baharu daripada bahan yang sama; "
            "murid menulis secara individu dan guru merekod ketepatan."
        )
    if family == "sunting":
        return (
            f"Guru menyediakan petikan pendek berpandukan bahan {t}{source}; "
            "murid menandakan kesalahan bahasa yang berkaitan dengan SP.",
            "Pasangan menyunting petikan, menulis pembetulan dan memberi sebab "
            "bagi sekurang-kurangnya dua perubahan.",
            "Murid menyunting satu petikan ringkas baharu secara individu; "
            "guru menyemak ketepatan pembetulan."
        )
    if family == "mekanis":
        return (
            f"Guru memodelkan bentuk huruf, jarak dan tanda baca menggunakan "
            f"perkataan daripada bahan {t}{source}; murid meneliti contoh.",
            "Murid menyalin perkataan atau ayat yang dipilih daripada bahan "
            "dengan bentuk huruf dan jarak yang konsisten; pasangan menyemak.",
            "Murid menulis semula dua ayat tanpa menyalin contoh rakan; "
            "guru menilai kekemasan, ejaan dan tanda baca."
        )
    if family == "menulis":
        return (
            f"Guru meneliti rangsangan atau maklumat daripada bahan {t}{source} "
            "bersama murid, lalu memilih isi yang berkaitan dengan kehendak SP.",
            "Murid merancang isi dan menghasilkan ayat atau perenggan mengikut "
            "bentuk penulisan yang ditetapkan; pasangan memberi satu cadangan.",
            "Murid menyemak isi, susunan, ejaan dan tanda baca kemudian "
            "membaiki sekurang-kurangnya satu bahagian hasil tulisan."
        )
    if family == "membaca":
        return (
            f"Guru memilih teks sebenar yang berkaitan dengan {t}{source}; "
            "murid membaca dan menandakan perkataan atau maklumat penting.",
            "Secara berpasangan murid menjawab soalan isi dan mencari ayat "
            "dalam teks yang menyokong setiap jawapan, bukan meneka.",
            "Murid menjawab tiga soalan pemahaman secara individu dan "
            "menunjukkan bukti teks; guru merekod respons yang tepat."
        )
    if family == "mendengar":
        return (
            f"Guru menyebut frasa atau ayat berkaitan {t}{source} dua kali "
            "tanpa memperlihatkan teks; murid mengecam maklumat yang didengar.",
            "Guru menukar urutan sebutan; murid memadankan maklumat dengan "
            "kad/gambar yang disediakan lalu menyebut semula secara bergilir.",
            "Secara individu murid memberi respons terhadap tiga ujaran baharu "
            "daripada bahan yang sama; guru menilai ketepatan mendengar dan sebutan."
        )
    if family == "bertutur":
        return (
            f"Guru memodelkan satu pertukaran ujaran dalam situasi {t}{source}; "
            "murid mengenal pasti maksud dan laras bahasa yang sesuai.",
            "Murid menjalankan dialog atau soal jawab berpasangan, memberi "
            "sekurang-kurangnya tiga respons yang relevan serta bertukar peranan.",
            "Murid memberikan satu respons lisan spontan dalam situasi baharu "
            "yang masih berkaitan; guru menilai sebutan, kesantunan dan isi."
        )
    if family == "seni bahasa":
        return (
            f"Guru memperdengarkan atau memperlihatkan karya yang dinyatakan "
            f"pada bahan {t}{source}; murid mengenal pasti bunyi atau maksud.",
            "Murid menyampaikan bahagian karya secara berkumpulan mengikut "
            "intonasi atau gaya yang sesuai, kemudian menerangkan satu nilai.",
            "Murid menyampaikan satu rangkap atau bahagian secara individu; "
            "guru menilai sebutan, penghayatan dan kefahaman."
        )
    if family == "tatabahasa":
        return (
            f"Guru memaparkan contoh kata atau ayat daripada bahan {t}{source}; "
            "murid mengenal pasti unsur bahasa yang dikehendaki SP.",
            "Pasangan mengelaskan atau membina contoh baharu dan menerangkan "
            "sebab penggunaan bentuk bahasa tersebut dalam ayat.",
            "Murid membina tiga ayat atau respons ringkas menggunakan unsur "
            "bahasa yang dipelajari; guru menyemak penggunaannya."
        )
    return None


def _confirmed_families(state):
    standards = state.get("_bm_web_verified_standards")
    if not isinstance(standards, (tuple, list)) or not standards:
        return ()
    found = []
    for rec in standards:
        if not isinstance(rec, dict):
            return ()
        code = str(rec.get("sp_code") or "").strip()
        desc = str(rec.get("sp_text") or "").strip()
        if not code or not desc:
            continue
        fam = _family(desc)
        if fam and fam not in found:
            found.append(fam)
    return tuple(found[:2])


def refine_web_bm_rows(state, rows):
    """BM Web only: retain good existing RPH, fix all numbered boundaries.

    For a proven generic shell, replace only activity-related fields when
    a verified SP verb and a real source PdP title provide enough context.
    Do not pretend a textbook page or exact passage was individually approved.
    """
    if (not isinstance(state, dict)
            or state.get(_STATE_FLAG) != SOURCE
            or state.get("subject") != "Bahasa Melayu"
            or not isinstance(rows, dict)):
        return rows
    output = dict(rows)
    for field in _NUMBERED_FIELDS:
        if field in output:
            output[field] = split_numbered_steps(output[field])

    topic = str(state.get("pdp_title") or "").strip()
    families = _confirmed_families(state)
    original = str(output.get("AKTIVITI UTAMA") or "")
    if (not topic or not families or not original
            or not any(cue in original.casefold() for cue in _GENERIC_CUES)):
        return output

    reference = str(state.get("textbook_ref") or "").strip()
    verified = state.get("_bm_web_verified_standards") or ()
    description = " ".join(str(item.get("sp_text") or "") for item in verified
                           if isinstance(item, dict))
    primary = _task(families[0], topic, reference, description)
    if not primary:
        return output
    secondary = (_task(families[1], topic, reference, description)
                 if len(families) > 1 else None)
    first = primary[0]
    second = secondary[1] if secondary else primary[1]
    third = primary[2] if not secondary else (
        primary[2] + " " + secondary[2]
    )
    output["SET INDUKSI"] = (
        f"5 minit\n1. Guru memperkenalkan tajuk ‘{topic}’ menggunakan "
        "rangsangan yang sepadan dengan sumber dipilih.\n"
        "2. Murid menyatakan satu pemerhatian atau pengetahuan awal."
    )
    output["AKTIVITI UTAMA"] = "\n".join((
        "Aktiviti 1 – Teliti dan model (15 minit)", "1. " + first,
        "Aktiviti 2 – Latihan berpandu (20 minit)", "2. " + second,
        "Aktiviti 3 – PBD individu (15 minit)", "3. " + third,
    ))
    output["PENUTUP"] = (
        "5 minit\n1. Murid menyatakan satu kemahiran bahasa yang dikuasai "
        f"melalui ‘{topic}’.\n2. Guru merumuskan dapatan PBD dan menetapkan "
        "sokongan kepada murid yang masih memerlukan bimbingan."
    )
    return output


def install(runtime):
    """Install once on the actual Telegram document renderer; no state mutation."""
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False
    if getattr(runtime, "_bm_web_refinement_installed", False) is True:
        return True

    @wraps(previous)
    def wrapped(state, *args, **kwargs):
        result = previous(state, *args, **kwargs)
        return refine_web_bm_rows(state, result)

    runtime._rph_rows = wrapped
    runtime._bm_web_refinement_installed = True
    return True
