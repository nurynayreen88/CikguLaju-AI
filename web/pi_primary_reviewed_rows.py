"""Source-checked Pendidikan Islam RPH corrections for selected KSSR lessons."""

import re


# Year, curriculum row ID and sequence identify the source on both native paths.
# The text anchors below are checked again before applying the corrections.
_AL_KAFIRUN_RANGES = {
    ("Tahun 3", 1387, 1): ("3-1", "1 هيڠݢ 3"),
    ("Tahun 3", 1391, 5): ("5-4", "4 هيڠݢ 5"),
}
_JAWI_LETTERS = ("Tahun 1", 1166, 3)
_JAWI_SYLLABLES = ("Tahun 2", 1277, 3)
_JAWI_PREFIXES = ("Tahun 3", 1390, 4)
_STANDARD_CODE = re.compile(r"(?<![\d.])\d+\.\d+(?:\.\d+)?(?![\d.])")
_JAWI_PREFIX_TEXT = "تيك س"
_UPPER_PRIMARY_JAWI = {
    ("Tahun 4", 1538, 4): {
        "KRITERIA KEJAYAAN": "موريد مڠنل ڤستي همزة 3/4 ڤد 3 ڤرکاتاءن دان ممباچ کتيݢ-تيݢڽ دڠن بتول.",
        "SET INDUKSI": "ݢورو منونجوقکن کد همزة. موريد منچاري تندا همزة ڤد کد ڤرکاتاءن.",
        "AKTIVITI UTAMA": (
            "اکتيۏيتي 1 - ݢورو منونجوقکن کد ڤرکاتاءن درڤد بوکو تيک س دان منندا کدودوقن همزة 3/4.\n"
            "اکتيۏيتي 2 - موريد مڠاسيڠکن کد يڠ ادا همزة 3/4 دان يڠ تيدق ادا. موريد ممباچ کد برڤاسڠن.\n"
            "اکتيۏيتي 3 - موريد منندا همزة دان ممباچ 3 ڤرکاتاءن سچارا اينديۏيدو."
        ),
        "PENTAKSIRAN": "ݢورو مريکود کدودوقن همزة دان سبوتن باݢي ستياڤ ساتو درڤد 3 ڤرکاتاءن.",
        "PENUTUP": "موريد منونجوقکن همزة ڤد ساتو کد دان ممباچ ڤرکاتاءن ايت.",
    },
    ("Tahun 5", 1690, 4): {
        "KRITERIA KEJAYAAN": "موريد ممباچ 3 ڤرکاتاءن درڤد ڤتيقن دان ممبينا 1 ايات جاوي تنتڠ عملن هيدوڤ صيحت.",
        "SET INDUKSI": "ݢورو منونجوقکن ݢمبر کچرسن بادن. موريد مثبوت ساتو عملن هيدوڤ صيحت.",
        "AKTIVITI UTAMA": (
            "اکتيۏيتي 1 - ݢورو مڠݢوناکن ڤتيقن جاوي برتيما عملن هيدوڤ صيحت. موريد ممباچ برڤاسڠن.\n"
            "اکتيۏيتي 2 - موريد مڠݢاريس 3 ڤرکاتاءن ساسرن دان ممباچڽ. ݢورو ممبتولکن سبوتن.\n"
            "اکتيۏيتي 3 - موريد منوليس 3 ڤرکاتاءن يڠ دسبوت ݢورو دان ممبينا ساتو ايات ڤنديق تنتڠ عملن صيحت."
        ),
        "PENTAKSIRAN": "ݢورو مڽمق باچاءن ڤتيقن، ايجاءن 3 ڤرکاتاءن دان کتيڤتن مکسود ايات سچارا اينديۏيدو.",
        "PENUTUP": "موريد ممباچ اياتڽ دان منونجوقکن ڤرکاتاءن ساسرن.",
    },
    ("Tahun 6", 1834, 4): {
        "KRITERIA KEJAYAAN": "موريد ممباچ 3 ڤرکاتاءن دان ممبينا 1 ايات جاوي تنتڠ ݢونا ساتو چيڤتاءن ساءين س دان تيکنولوݢي.",
        "SET INDUKSI": "ݢورو منونجوقکن ݢمبر ساتو چيڤتاءن. موريد مڽبوت ݢوناڽ.",
        "AKTIVITI UTAMA": (
            "اکتيۏيتي 1 - موريد ممباچ ڤتيقن جاوي تنتڠ چيڤتاءن دان کݢوناءنڽ. ݢورو ممبيمبيڠ باچاءن.\n"
            "اکتيۏيتي 2 - موريد مميليه 3 ڤرکاتاءن دريڤد ڤتيقن. موريد مڠيجا دان منوليسڽ سمولا.\n"
            "اکتيۏيتي 3 - موريد ممبينا ساتو ايات جاوي يڠ منرڠکن ݢونا ساتو چيڤتاءن، کمودين ممباچڽ."
        ),
        "PENTAKSIRAN": "ݢورو مڽمق باچاءن، ايجاءن 3 ڤرکاتاءن دان ايات تنتڠ کݢوناءن چيڤتاءن سچارا اينديۏيدو.",
        "PENUTUP": "موريد ممباچ سمولا ايات يڠ تله دبايقي.",
    },
}


def _standards(codes, texts):
    """Use a clause only when it is explicitly labelled in its source text."""
    if len(codes) != len(texts):
        return None
    clauses = []
    for index, (code, source) in enumerate(zip(codes, texts)):
        text = str(source or "").strip()
        markers = list(_STANDARD_CODE.finditer(text))
        if markers:
            matches = [i for i, marker in enumerate(markers) if marker[0] == code]
            if len(matches) == 1:
                i = matches[0]
                end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
                text = text[markers[i].end():end]
            elif not matches and index == 0 and markers[0][0] in codes[1:]:
                # Telegram strips the selected leading code before storing the text.
                text = text[:markers[0].start()]
            else:
                return None
        text = text.strip(" \t\n–—-:;")
        if not text:
            return None
        clauses.append(f"{code} {text}")
    return "\n".join(clauses)


def apply_primary_reviewed_rows(state, rows):
    source = state.get("_quick_selected_rpt_row_v2388") or state.get("quick_rpt_row") or {}
    # The Web detail join may expose its own ID. The selected RPT entry remains
    # the authoritative ID and matches the Telegram selection.
    identity = (
        state.get("year"),
        state.get("rpt_entry_id"),
        source.get("sequence_no"),
    )
    if identity == _JAWI_LETTERS:
        if state.get("selected_sp_codes") != ["7.1.1", "7.1.2"]:
            return rows
        rows.update({
            "KRITERIA KEJAYAAN": "موريد مثبوت نام 5 دريڤد 6 حروف دان ملاکر 2 بنتوق حرف مڠيکوت چونتوه.",
            "SET INDUKSI": "ݢورو منونجوقکن کد حرف ا دان ب. موريد مڠنل ڤستي ڤربيذاءن بنتوق دان نقطه.",
            "AKTIVITI UTAMA": (
                "اکتيۏيتي 1 - ݢورو منونجوقکن کد ا، ب، ت، ث، ج دان چ. موريد مثبوت نام ستياڤ حرف.\n"
                "اکتيۏيتي 2 - موريد ممادنکن کد يڠ سام دان مڽاتاکن بيلڠن نقطه. ݢورو ممبتولکن سبوتن.\n"
                "اکتيۏيتي 3 - ݢورو منونجوقکن چارا ملاکر بنتوق ب دان چ. موريد ملاکر کدوا-دوا بنتوق ايت."
            ),
            "PENTAKSIRAN": "ݢورو مڽمق سبوتن 6 حرف دان 2 لاکرن سچارا اينديۏيدو. ريکود حرف دان لاکرن يڠ ڤرلو دبايقي.",
            "PENUTUP": "موريد مثبوت ساتو حرف ڤيليهن دان منونجوقکن کد يڠ سڤادن.",
        })
    elif identity == _JAWI_SYLLABLES:
        if state.get("selected_sp_codes") != ["6.1.1", "6.1.2"]:
            return rows
        rows.update({
            "KRITERIA KEJAYAAN": "موريد ممباچ 3 ڤرکاتاءن تيݢ سوکو کات دان ممبينا 2 ڤرکاتاءن مڠݢوناکن کد سوکو کات.",
            "SET INDUKSI": "ݢورو منونجوقکن ݢمبر باݢي ساتو ڤرکاتاءن تيݢ سوکو کات. موريد منڤوق مڠيکوت سوکو کات.",
            "AKTIVITI UTAMA": (
                "اکتيۏيتي 1 - ݢورو منونجوقکن 3 کد ڤرکاتاءن تيݢ سوکو کات. موريد ممباچ ساتو ڤرساتو.\n"
                "اکتيۏيتي 2 - موريد مڽوسون 3 کد سوکو کات باݢي ستياڤ ڤرکاتاءن دان ممباچڽ کڤد راکن.\n"
                "اکتيۏيتي 3 - موريد ممباچ 3 ڤرکاتاءن دان ممبينا 2 ڤرکاتاءن سچارا اينديۏيدو دهادڤن ݢورو."
            ),
            "PENTAKSIRAN": "ݢورو مريکود 3 باچاءن دان 2 سوسونن سوکو کات، کمودين ممبتولکن يڠ کورڠ تڤت.",
            "PENUTUP": "موريد ممباچ سمولا ساتو ڤرکاتاءن دڠن تورتن سوکو کات يڠ بتول.",
        })
    elif identity == _JAWI_PREFIXES:
        objective = rows.get("OBJEKTIF PEMBELAJARAN", "")
        if state.get("selected_sp_codes") != ["7.1.1"] or _JAWI_PREFIX_TEXT not in objective:
            return rows
        rows.update({
            "OBJEKTIF PEMBELAJARAN": objective.replace("ڤلادع", "ڤلادڠ"),
            "KRITERIA KEJAYAAN": "موريد ممباچ ڤتيقن ڤنديق دان مثبوت 3 ڤرکاتاءن برايمبوهن اولن دڠن بتول.",
            "SET INDUKSI": "ݢورو منونجوقکن ݢمبر ڤلادڠ. موريد مثبوت ڤرکاتاءن يڠ برکاءيتن دڠن ݢمبر.",
            "AKTIVITI UTAMA": (
                "اکتيۏيتي 1 - ݢورو ممباچ ڤتيقن ڤنديق يڠ مڠاندوڠي بکرجا، ڤلادڠ دان ملوکيس. موريد مڠيکوت باچاءن.\n"
                "اکتيۏيتي 2 - موريد مڠݢاريس 3 ڤرکاتاءن برايمبوهن اولن دان ممباچ ڤتيقن برڤاسڠن.\n"
                "اکتيۏيتي 3 - موريد ممباچ ڤتيقن سچارا اينديۏيدو. ݢورو ممبتولکن سبوتن يڠ کورڠ تڤت."
            ),
            "PENTAKSIRAN": "ݢورو مڽمق باچاءن ڤتيقن دان مريکود بيلڠن ڤرکاتاءن ساسرن يڠ دباچ دڠن بتول.",
            "PENUTUP": "موريد ممباچ سمولا ساتو ڤرکاتاءن يڠ تله دبايقي.",
        })
    elif identity in _UPPER_PRIMARY_JAWI:
        if state.get("selected_sp_codes") != ["7.1.1", "7.1.2"]:
            return rows
        rows.update(_UPPER_PRIMARY_JAWI[identity])
    elif identity in _AL_KAFIRUN_RANGES:
        old_range, verse_range = _AL_KAFIRUN_RANGES[identity]
        objective = rows.get("OBJEKTIF PEMBELAJARAN", "")
        anchor = f"سورة الكافرون اية {old_range}"
        if anchor not in objective or "1.1.1" not in (state.get("selected_sp_codes") or []):
            return rows
        rows.update({
            "OBJEKTIF PEMBELAJARAN": objective.replace(anchor, f"سورة الكافرون اية {verse_range}"),
            "KRITERIA KEJAYAAN": f"موريد ممباچ ايات {verse_range} دڠن سبوتن دان تجويد يڠ بتول.",
            "SET INDUKSI": f"ݢورو ممڤردڠرکن باچاءن ايات {verse_range} درڤد سورة الكافرون. موريد منونجوقکن ايات يڠ ددڠر.",
            "AKTIVITI UTAMA": (
                f"اکتيۏيتي 1 - ݢورو ممباچ ايات {verse_range} سچارا تلاقي دان مشافهة. موريد مڠيکوت باچاءن ايات دمي ايات.\n"
                "اکتيۏيتي 2 - موريد ممباچ برڤاسڠن. راکن مڽمق تورتن ايات دان ݢورو ممبتولکن سبوتن دان تجويد.\n"
                "اکتيۏيتي 3 - موريد ممباچ ايات سچارا اينديۏيدو دهادڤن ݢورو."
            ),
            "PENTAKSIRAN": "ݢورو مريکود کتڤتن سبوتن، تورتن ايات دان تجويد باݢي ستياڤ موريد.",
            "PENUTUP": "موريد ممباچ سمولا ڤوتوڠن ايات يڠ تله دبايقي.",
        })
    else:
        return rows

    for field, prefix in (("STANDARD KANDUNGAN", "sk"), ("STANDARD PEMBELAJARAN", "sp")):
        codes = state.get(f"selected_{prefix}_codes") or []
        texts = state.get(f"grouped_{prefix}_texts") or []
        standards = _standards(codes, texts)
        if standards:
            rows[field] = standards
    return rows
