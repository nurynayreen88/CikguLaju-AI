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
    # Repeated generic v26.00 opening headings across 229 real BM PdPs.
    # Only replace when the selected SP has exact verified wording.
    "baca dan anotasi", "bacaan berpandu", "dengar dan catat",
    "rancang isi", "apresiasi teks", "cari kad betul",
    "bina daripada model", "jejak/salin berpandu",
    "kenal dan baca", "dengar dan tunjuk", "dengar/lihat model",
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
        r"(?<=\S)[ \t]*(?=(?:[1-9]|1\d)[.)][ \t]*" + action + ")",
        "\n", result, flags=re.I,
    )
    result = re.sub(
        r"(?<=\S)[ \t]*(?=(?:Aktiviti|Activity)[ \t]+[1-9]\d*"
        r"(?:[ \t]*\([ \t]*\d{1,2}[ \t]*(?:minit|minutes?|mins?)[ \t]*\))?"
        r"[ \t]*(?:[:：]|[–—-]))",
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
    if any(v in s for v in ("mencatat maklumat", "menyusun dan mencatat",
                            "membanding beza dan mencatat", "menjana idea berdasarkan bahan")):
        return "mencatat"
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
                            "seni bahasa", "puisi", "seloka", "seni kata lagu",
                            "menyanyikan lagu", "melagukan", "mengubah suai cerita",
                            "mempersembahkan karya", "lirik lagu")):
        return "seni bahasa"
    if any(v in s for v in ("kata nama", "kata kerja", "kata adjektif",
                            "kata sendi", "kata ganda", "kata majmuk",
                            "imbuhan", "tatabahasa", "pelbagai jenis ayat",
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
    if family == "mencatat":
        return (
            f"Guru memaparkan bahan sebenar bertajuk {t}{source}. Murid "
            "mengenal pasti butiran penting dan membezakan maklumat utama "
            "daripada contoh atau huraian sampingan.",
            "Murid menyusun isi daripada sumber ke dalam catatan berstruktur "
            "seperti jadual atau peta maklumat yang sesuai dengan kehendak "
            "SP. Pasangan menyemak maklumat agar tidak mengubah maksud asal.",
            "Murid mencatat sekurang-kurangnya tiga maklumat penting daripada "
            "bahagian bahan yang belum dibincangkan; guru menilai ketepatan, "
            "susunan isi dan kesetiaan terhadap sumber."
        )
    if family == "bertutur" and "tersurat" in low_sp and "tersirat" in low_sp:
        return (
            f"Guru memperdengarkan atau memaparkan situasi dalam {t}{source}. "
            "Murid menyatakan maklumat yang disebut secara jelas, kemudian "
            "menerangkan petunjuk bagi maklumat tersirat.",
            "Secara berpasangan murid membanding beza dua maklumat atau "
            "situasi daripada bahan; mereka menjelaskan persamaan, perbezaan "
            "dan alasan yang disokong petunjuk.",
            "Murid menerangkan satu maklumat tersurat dan satu maklumat "
            "tersirat secara individu dengan alasan yang munasabah. "
            "Guru menilai ketepatan perbandingan dan penyampaian lisan."
        )
    if family == "seni bahasa" and "mengubah suai" in low_sp:
        if "puisi" in low_sp:
            return (
                f"Guru membimbing murid membaca puisi sebenar daripada "
                f"bahan {t}{source} dan mengenal pasti tema, diksi serta maksud.",
                "Murid mengubah suai beberapa perkataan atau larik puisi "
                "secara berpandu sambil mengekalkan maksud yang sesuai; "
                "pasangan menyemak kelancaran dan kesantunan bahasa.",
                "Murid mempersembahkan puisi yang telah diubah suai dan "
                "menerangkan satu pilihan kata. Guru menilai kreativiti "
                "serta kesesuaian maksud."
            )
        if "cerita" in low_sp:
            return (
                f"Guru memilih cerita daripada bahan {t}{source}; murid "
                "mengenal pasti watak, peristiwa dan pengajaran asal.",
                "Secara berpasangan murid mengubah suai dialog atau bahagian "
                "peristiwa secara berpandu tanpa menghilangkan urutan cerita, "
                "kemudian menyemak bahasa yang digunakan.",
                "Murid mempersembahkan hasil olahan cerita dengan sebutan "
                "yang jelas dan menjelaskan perubahan yang dibuat."
            )
        if "lagu" in low_sp:
            return (
                f"Guru memperdengarkan lagu daripada bahan {t}{source}; murid "
                "mengenal pasti tema, maksud dan pilihan kata dalam lirik.",
                "Murid mengubah suai seni kata terpilih mengikut pola irama "
                "asal menggunakan diksi yang sesuai; kumpulan menguji "
                "kelancaran sebutan ketika menyanyikan baris baharu.",
                "Kumpulan mempersembahkan seni kata yang diolah dan "
                "menerangkan maksudnya; guru menilai diksi, sebutan dan gaya."
            )
    if family == "seni bahasa" and ("menyanyikan" in low_sp or "lagu" in low_sp):
        return (
            f"Guru memperdengarkan lagu yang berkaitan dengan {t}{source}; "
            "murid mengenal pasti kata dan maksud lirik sebelum latihan sebutan.",
            "Murid menyanyikan lagu secara berkumpulan mengikut irama, "
            "sebutan serta intonasi yang sesuai; mereka melakukan aksi "
            "yang benar-benar sepadan dengan makna lirik.",
            "Murid menyampaikan sebahagian lagu dan menjelaskan satu "
            "maksud atau pengajaran daripada lirik; guru menilai penghayatan."
        )
    if family == "seni bahasa" and "seloka" in low_sp:
        return (
            f"Guru memperdengarkan seloka dalam bahan {t}{source}; "
            "murid meneliti maksud dan nada yang sepadan dengan pengajaran.",
            "Murid berlatih melafazkan dan melagukan seloka dengan nada, "
            "sebutan serta jeda yang sesuai secara berpasangan.",
            "Murid mempersembahkan seloka secara individu dan menyatakan "
            "satu pengajaran berdasarkan rangkap sebenar."
        )
    if family == "tatabahasa" and "kata majmuk" in low_sp:
        return (
            f"Guru memperlihatkan contoh kata majmuk daripada bahan {t}{source}; "
            "murid mengenal pasti gabungan kata serta maksud dalam konteks.",
            "Pasangan mengelaskan contoh kata majmuk dan membina ayat "
            "mengikut konteks bahan. Guru membimbing pembetulan ejaan "
            "serta penggunaan yang kurang sesuai.",
            "Murid membina sekurang-kurangnya tiga ayat menggunakan kata "
            "majmuk yang betul; guru menilai ketepatan maksud dan ejaan."
        )
    if family == "tatabahasa" and "jenis ayat" in low_sp:
        return (
            f"Guru memaparkan beberapa jenis ayat yang benar-benar muncul "
            f"dalam bahan {t}{source}; murid menentukan tujuan setiap ayat.",
            "Pasangan membandingkan bentuk ayat dan membina contoh baharu "
            "mengikut konteks, kemudian menyemak tanda baca dan struktur.",
            "Murid membina tiga ayat daripada jenis yang dipelajari "
            "serta memberikan sebab pilihan ayat; guru merekod penguasaan."
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
        # Only Bahasa Melayu verified SK 1.x denotes oral communication.
        # SP 1.2.2 requests explaining/comparing implicit/explicit facts,
        # without necessarily containing the verb "bertutur".
        if (not fam and str(rec.get("sk_code") or "").startswith("1.")
                and ("menjelaskan" in desc.casefold()
                     or "membanding beza" in desc.casefold())):
            fam = "bertutur"
        if fam and fam not in found:
            found.append(fam)
    return tuple(found[:2])



# Headings explain the verified BM skill instead of repeating generic lessons.
# Only the refinement's three generated headings change; lesson source, SK/SP
# and teacher-authored activity paragraphs are not touched.
_PHASE_HEADINGS = {
    "mendengar": ("Dengar dan cam", "Respons terhadap ujaran", "PBD mendengar"),
    "bertutur": ("Model pertuturan", "Interaksi berpasangan", "PBD pertuturan"),
    "membaca": ("Baca dan cari bukti", "Fahami teks", "PBD pemahaman"),
    "menulis": ("Rancang penulisan", "Bina dan semak", "PBD penulisan"),
    "mencatat": ("Kenal pasti isi", "Catatan berpandu", "PBD catatan"),
    "imlak": ("Dengar dan tulis", "Semak ejaan", "PBD imlak"),
    "sunting": ("Kenal pasti kesalahan", "Sunting dan jelaskan", "PBD suntingan"),
    "mekanis": ("Model tulisan", "Latihan menyalin", "PBD tulisan"),
    "seni bahasa": ("Hayati karya", "Latihan persembahan", "PBD seni bahasa"),
    "tatabahasa": ("Kenal bentuk bahasa", "Bina contoh", "PBD tatabahasa"),
}

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
    first_labels = _PHASE_HEADINGS[families[0]]
    second_labels = _PHASE_HEADINGS[families[1]] if secondary else first_labels
    final_label = "PBD gabungan kemahiran" if secondary else first_labels[2]
    output["AKTIVITI UTAMA"] = "\n".join((
        f"Aktiviti 1 – {first_labels[0]} (15 minit)", "1. " + first,
        f"Aktiviti 2 – {second_labels[1]} (20 minit)", "2. " + second,
        f"Aktiviti 3 – {final_label} (15 minit)", "3. " + third,
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
