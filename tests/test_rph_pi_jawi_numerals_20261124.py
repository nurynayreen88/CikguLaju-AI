"""The live PI RPH presents Arabic-Indic numerals without editing lesson data."""
from collections import Counter
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from docx import Document
from lxml import etree

from web.rph_pi_jawi_numerals_20261124 import (
    is_active_pi_rph, jawi_display_digits, display_pi_rows,
    jawi_word_display_digits, install,
)
from web.rph_reference_style_20261121 import color_for_state, style_word_path
from test_pi_active_jawi_content_right_20261123 import native_pi_word

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _state():
    return {"task": "rph", "subject": "Pendidikan Islam", "year": "Tahun 2"}


def _styled_realistic_word(tmp_path):
    file = tmp_path / "actual_pi.docx"
    file.write_bytes(native_pi_word())
    fill = color_for_state(_state())
    assert style_word_path(file, fill, premium_header=True, rtl_jawi=True)
    return file


def test_jawi_digits_are_exact_and_idempotent_but_url_is_not_broken():
    example = ("تاهون 2 • 1.1.1 • اکتيۏيتي 3 • آية 1–29 • "
               "30 murid • https://host.com/book/2027/page2 "
               "admin123@example.com")
    expected = ("تاهون ٢ • ١.١.١ • اکتيۏيتي ٣ • آية ١–٢٩ • "
                "٣٠ murid • https://host.com/book/2027/page2 "
                "admin123@example.com")
    assert jawi_display_digits(example) == expected
    assert jawi_display_digits(expected) == expected
    assert jawi_display_digits(None) is None
    assert jawi_display_digits("<font size='12'>Aktiviti 3</font>&#160;") == (
        "<font size='12'>Aktiviti ٣</font>&#160;"
    )


def test_pi_rows_change_only_render_values_not_original_data_or_routes():
    original = {
        "STANDARD KANDUNGAN": "1.1",
        "STANDARD PEMBELAJARAN": "1.1.1",
        "AKTIVITI UTAMA": "اکتيۏيتي 1\n1. ڤڠاجرن",
        "REFLEKSI": "30 murid mencapai objektif",
        "Sumber": "https://example.com/sumber/2027/12",
        "Other": 3,
    }
    copy = dict(original)
    rendered = display_pi_rows(_state(), original)
    assert original == copy
    assert rendered is not original
    assert rendered["STANDARD KANDUNGAN"] == "١.١"
    assert rendered["STANDARD PEMBELAJARAN"] == "١.١.١"
    assert rendered["AKTIVITI UTAMA"] == "اکتيۏيتي ١\n١. ڤڠاجرن"
    assert rendered["REFLEKSI"] == "٣٠ murid mencapai objektif"
    assert rendered["Sumber"] == original["Sumber"]
    assert rendered["Other"] == 3
    assert display_pi_rows(_state(), rendered) is rendered
    for unrelated in (
        {**_state(), "subject": "Bahasa Melayu"},
        {**_state(), "task": "rpt"},
        {**_state(), "curriculum": "KP2027"},
        {**_state(), "school_type": "SJKC"},
        {**_state(), "programme": "PPKI"},
        {**_state(), "curriculum_version": "DLP"},
    ):
        assert display_pi_rows(unrelated, original) is original
        assert not is_active_pi_rph(unrelated)


def test_jawi_native_word_only_visible_digits_change_source_and_zip_stable(tmp_path):
    file = _styled_realistic_word(tmp_path)
    original = file.read_bytes()
    changed = jawi_word_display_digits(original)
    assert changed != original
    assert jawi_word_display_digits(changed) == changed
    with ZipFile(BytesIO(original)) as a, ZipFile(BytesIO(changed)) as b:
        assert a.namelist() == b.namelist()
        assert b.testzip() is None
        for path in a.namelist():
            if path != "word/document.xml":
                assert a.read(path) == b.read(path)
        old = etree.fromstring(a.read("word/document.xml"))
        new = etree.fromstring(b.read("word/document.xml"))
        assert [x.tag for x in old.iter()] == [x.tag for x in new.iter()]
        original_text = [x.text for x in old.iter(W+"t")]
        revised_text = [x.text for x in new.iter(W+"t")]
        assert len(original_text) == len(revised_text)
        assert any("0" <= n <= "9" for text in original_text for n in (text or ""))
        assert not any("0" <= n <= "9" for text in revised_text for n in (text or ""))
        assert any("٣٠" in x for x in revised_text if x)
    doc = Document(BytesIO(changed))
    assert doc.paragraphs[0].text == "رنچڠن ڤڠاجرن هارين"
    assert len(doc.tables) == 4
    assert "١.١" in doc.tables[1].cell(0, 1).text or (
        "١.١" in "\n".join(c.text for table in doc.tables for row in table.rows for c in row.cells))
    assert "اکتيۏيتي ٢" in doc.tables[2].cell(2, 1).text


def test_unknown_word_layouts_remain_byte_identical(tmp_path):
    import io
    unstyled = native_pi_word()
    assert jawi_word_display_digits(unstyled) == unstyled
    normal = Document()
    normal.add_paragraph("Year 2027")
    out = io.BytesIO()
    normal.save(out)
    assert jawi_word_display_digits(out.getvalue()) == out.getvalue()
    assert jawi_word_display_digits(b"bad-docx") == b"bad-docx"


def test_runtime_guard_converts_pi_rows_and_word_but_not_bm(tmp_path):
    source = _styled_realistic_word(tmp_path).read_bytes()
    word = tmp_path / "download.docx"
    class Runtime:
        def _rph_rows(self, state, original):
            return {"STANDARD KANDUNGAN": "1.1",
                    "AKTIVITI UTAMA": "اکتيۏيتي 2"}
        def create_word_file(self, state, original, user_id):
            word.write_bytes(source)
            return str(word)

    runtime = Runtime()
    original_rows = runtime._rph_rows
    assert install(runtime)
    assert not install(runtime)
    pi_rows = runtime._rph_rows(_state(), "")
    assert pi_rows["STANDARD KANDUNGAN"] == "١.١"
    assert pi_rows["AKTIVITI UTAMA"] == "اکتيۏيتي ٢"
    assert runtime._rph_rows({"task":"rph","subject":"Bahasa Melayu"}, "") == original_rows(_state(),"")
    runtime.create_word_file(_state(), "", "user")
    doc = Document(word)
    assert "اکتيۏيتي ٢" in doc.tables[2].cell(2, 1).text
    runtime.create_word_file({"task":"rph","subject":"Bahasa Melayu"}, "", "user")
    assert word.read_bytes() == source
