"""Guard the exact seven SK/SP corrections and PI Jawi PDF first box."""
from collections import Counter
from types import SimpleNamespace
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, Table

from web.rph_verified_standard_labels_20261124 import (
    _VERIFIED, display_verified_standards, install,
)
from web.rph_pi_native_pdf_header_20261124 import (
    HEADER_LABELS, PI_FILL, CenteredJawiTitle, reflow_verified_pi_header,
)


def _state(subject, year):
    prefix = f"MT{year}" if subject == "Matematik" else f"SCI-Y{year}"
    return {"task": "rph", "subject": subject,
            "year": f"Tahun {year}", "pdp_sequence_code": prefix + "-PDP-001"}


def test_all_seven_verified_source_codes_expand_only_at_output():
    for (subject, year), (sk, sk_name, sp, sp_name) in _VERIFIED.items():
        state = _state(subject, year)
        initial = {
            "STANDARD KANDUNGAN": sk, "STANDARD PEMBELAJARAN": sp,
            "OBJEKTIF PEMBELAJARAN": "Keep this original objective.",
            "AKTIVITI UTAMA": "Keep all teacher and pupil steps.",
            "REFLEKSI": "Keep teacher reflection.",
        }
        revised = display_verified_standards(state, initial)
        assert initial["STANDARD KANDUNGAN"] == sk
        assert revised["STANDARD KANDUNGAN"] == f"{sk} {sk_name}"
        assert revised["STANDARD PEMBELAJARAN"] == f"{sp} {sp_name}"
        assert {k: v for k, v in revised.items() if k not in (
            "STANDARD KANDUNGAN", "STANDARD PEMBELAJARAN"
        )} == {k: v for k, v in initial.items() if k not in (
            "STANDARD KANDUNGAN", "STANDARD PEMBELAJARAN"
        )}
        assert display_verified_standards(state, revised) is revised


def test_all_verified_combined_math_sp_clauses_have_complete_descriptions():
    from web.rph_verified_standard_labels_20261124 import _EXTRA_SPS
    for year, raw in ((2, "1.1.1(i);1.1.1(ii)"),
                      (3, "1.1.1(ii);1.1.1(iii)"),
                      (4, "1.1.1(i);1.1.1(ii)"),
                      (5, "1.1.1(i);1.1.1(ii);1.1.1(iii)")):
        state = _state("Matematik", year)
        rows = {"STANDARD KANDUNGAN": "1.1",
                "STANDARD PEMBELAJARAN": raw,
                "AKTIVITI UTAMA": "No teacher instruction loss"}
        source_copy = dict(rows)
        output = display_verified_standards(state, rows)
        assert rows == source_copy
        assert output["STANDARD PEMBELAJARAN"].count(";") == raw.count(";")
        assert "1.1 Nilai nombor" == output["STANDARD KANDUNGAN"]
        for code, label in _EXTRA_SPS.get(("Matematik", year), {}).items():
            assert f"{code} {label}" in output["STANDARD PEMBELAJARAN"]
        assert output["AKTIVITI UTAMA"] == "No teacher instruction loss"
        assert display_verified_standards(state, output) is output
        bad = {**rows, "STANDARD PEMBELAJARAN": raw + ";9.9.9"}
        assert display_verified_standards(state, bad)["STANDARD PEMBELAJARAN"] == bad["STANDARD PEMBELAJARAN"]


def test_pdf_preserves_all_roman_subclauses_and_legacy_for_every_other_string():
    from web.rph_math_multisp_pdf_guard_20261124 import (
        _VERIFIED_COMPOUNDS, preserve_math_subclauses, install as install_pdf
    )
    assert len(_VERIFIED_COMPOUNDS) == 4
    def legacy(value):
        return "OLD_DEDUP_RESULT"

    for exact in _VERIFIED_COMPOUNDS:
        assert preserve_math_subclauses(exact, legacy) == exact
    for other in ("1.1.1(i) Teori berlainan; 1.1.1(ii) Tiada bukti",
                  "1.1.1(i) Membaca", "1.1.1(i);1.1.1(ii)",
                  "٢.١ معيار تعليم", "<b>1.1.1(i)</b>"):
        assert preserve_math_subclauses(other, legacy) == "OLD_DEDUP_RESULT"

    runtime = SimpleNamespace(_dedup_standard_lines_v25216=legacy)
    assert install_pdf(runtime) is True
    assert install_pdf(runtime) is False
    for exact in _VERIFIED_COMPOUNDS:
        assert runtime._dedup_standard_lines_v25216(exact) == exact
    assert runtime._dedup_standard_lines_v25216("Other subject") == "OLD_DEDUP_RESULT"


def test_no_guessing_multistandard_specialty_or_other_lessons():
    example = _state("Sains", 5)
    source = {"STANDARD KANDUNGAN": "2.1",
              "STANDARD PEMBELAJARAN": "2.1.1",
              "REFLEKSI": "exact teacher text"}
    changed = display_verified_standards(example, source)
    assert changed is not source
    assert source == {"STANDARD KANDUNGAN":"2.1",
                      "STANDARD PEMBELAJARAN":"2.1.1",
                      "REFLEKSI":"exact teacher text"}
    for state in (
        {**example, "pdp_sequence_code": "OTHER-LESSON"},
        {**example, "year": "Tahun 4"},
        {**example, "subject": "Science"},
        {**example, "curriculum": "DLP"},
        {**example, "programme": "PPKI"},
        {**example, "school_type": "SJKC"},
        {**example, "task": "rpt"},
    ):
        assert display_verified_standards(state, source) is source
    assert display_verified_standards(example, {**source,
        "STANDARD PEMBELAJARAN":"2.1.1; 2.1.2"})["STANDARD PEMBELAJARAN"] == "2.1.1; 2.1.2"
    assert display_verified_standards(example, {**source,
        "STANDARD KANDUNGAN":"2.1 Sistem Rangka Manusia"})["STANDARD KANDUNGAN"] == "2.1 Sistem Rangka Manusia"


def test_install_exactly_once_wraps_only_final_rows():
    class Runtime:
        def _rph_rows(self, state, source):
            return {"STANDARD KANDUNGAN":"2.1", "STANDARD PEMBELAJARAN":"2.1.1",
                    "AKTIVITI UTAMA":source}
    runtime = Runtime()
    assert install(runtime) is True
    assert install(runtime) is False
    output = runtime._rph_rows(_state("Sains", 5), "Exact original activity")
    assert output["STANDARD PEMBELAJARAN"].startswith("2.1.1 Memerihalkan")
    assert output["AKTIVITI UTAMA"] == "Exact original activity"


def _pi_story():
    style = getSampleStyleSheet()["Normal"]
    item = lambda text: Paragraph(text, style)
    # Native PI ReportLab has reversed two-column row order already:
    # value LEFT, label RIGHT (do not reverse again).
    rows = [[item("value " + str(i)), item(label)]
            for i, label in enumerate(HEADER_LABELS)]
    rows += [[item("isi " + str(i)), item("label " + str(i))]
             for i in range(9)]
    info = Table(rows, colWidths=[124*mm,48*mm])
    activity = Table([[item("langkah 1"), item("فاسا"), item("note")]],
                     colWidths=[28*mm,112*mm,32*mm])
    footer = Table([[item("رفليكسي"), item("teacher text")]],
                   colWidths=[124*mm,48*mm])
    return [item("رنچڠن ڤڠاجرن هارين"), Spacer(1,2*mm), info,
            Spacer(1,3*mm), activity, Spacer(1,3*mm), footer]


def test_pi_two_panel_pdf_reuses_all_jawi_objects_and_retains_rtl_labels():
    state={"task":"rph","subject":"Pendidikan Islam","year":"Tahun 2"}
    original=_pi_story()
    first=original[2]
    before=Counter(id(v) for row in first._cellvalues for v in row)
    revised=reflow_verified_pi_header(state,original)
    assert len(revised)==9
    assert isinstance(revised[0], CenteredJawiTitle)
    assert revised[0].original is original[0]
    assert revised[-3] is original[4]
    assert revised[-1] is original[6]
    banner=revised[2]
    teacher, identity = banner._cellvalues[0]
    # PDF physical positions: Kelas/Tarikh LEFT; PI/Tahun/Tajuk RIGHT.
    assert len(teacher._cellvalues) == 5
    assert len(identity._cellvalues) == 3
    assert [row[1].text for row in identity._cellvalues] == [
        HEADER_LABELS[i] for i in (0, 1, 7)]
    assert [row[1].text for row in teacher._cellvalues] == [
        HEADER_LABELS[i] for i in (5, 2, 3, 4, 6)]
    body=revised[4]
    assert len(body._cellvalues)==9
    after=Counter(id(v) for table in (identity, teacher, body)
                  for row in table._cellvalues for v in row)
    assert before==after
    background = [row for row in banner._bkgrndcmds if row[0] == "BACKGROUND"]
    assert len(background) == 2
    assert all(row[-1] == PI_FILL for row in background)
    assert any(row[-1] == PI_FILL for row in body._bkgrndcmds)
    assert reflow_verified_pi_header({**state, "programme":"PPKI"}, original) is original
    assert reflow_verified_pi_header({**state, "curriculum":"DLP"}, original) is original
    assert reflow_verified_pi_header({"task":"rph","subject":"Bahasa Arab"},original) is original
    broken=_pi_story()
    broken[2]._cellvalues[0][1].text="Unknown"
    assert reflow_verified_pi_header(state,broken) is broken



def test_native_jawi_title_is_visually_centered_without_changing_its_glyph_image():
    """The native title is drawn at the right; the wrapper centers its glyphs."""
    from PIL import Image as PILImage, ImageDraw
    from reportlab.lib.utils import ImageReader

    class AlreadyShapedNativeTitle:
        def __init__(self):
            self.text = "رنچڠن ڤڠاجرن هارين"
            self._img = None

        def wrap(self, available_width, available_height):
            # Original renderer: transparent raster with text on far RIGHT.
            canvas = PILImage.new("RGBA", (300, 45), (255, 255, 255, 0))
            ImageDraw.Draw(canvas).rectangle((240, 7, 281, 29), fill=(0, 0, 0, 255))
            self._img = ImageReader(canvas)
            return available_width, 15

    title = AlreadyShapedNativeTitle()
    centered = CenteredJawiTitle(title)
    assert centered.wrap(180, 40) == (180, 15)

    class CaptureCanvas:
        def __init__(self):
            self.calls = []
        def drawImage(self, image, x, y, **kwargs):
            self.calls.append((image, x, y, kwargs))

    capture = CaptureCanvas()
    centered.canv = capture
    centered.draw()
    assert len(capture.calls) == 1
    image, x, y, kwargs = capture.calls[0]
    actual_centre = x + kwargs["width"] / 2
    assert abs(actual_centre - 90) < .01
    assert kwargs["height"] == 15
    assert title._img._image.getchannel("A").getbbox() == (240, 7, 282, 30)
    assert image._image.getchannel("A").getbbox() == (0, 7, 42, 30)


def test_word_pi_palette_matches_pdf_and_keeps_original_rtl_panels():
    from web.rph_reference_style_20261121 import color_for_state
    from web.rph_premium_header_20261121 import premium_header_bytes
    from test_pi_active_jawi_content_right_20261123 import native_pi_word
    from web.rph_reference_style_20261121 import style_three_table_word_bytes
    from docx import Document
    from io import BytesIO
    from zipfile import ZipFile
    from lxml import etree
    from collections import Counter

    color = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    assert color == "ECE4F6"
    source = native_pi_word()
    result = premium_header_bytes(style_three_table_word_bytes(source, color),
                                  color, rtl_jawi=True)
    doc = Document(BytesIO(result))
    assert len(doc.tables) == 4
    assert doc.tables[0].cell(0, 0).text.startswith("مات ڤلاجرن")
    assert "کلس" in doc.tables[0].cell(0, 1).text
    with ZipFile(BytesIO(result)) as zipfile:
        root = etree.fromstring(zipfile.read("word/document.xml"))
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    header = root.find(W+"body").findall(W+"tbl")[0]
    cells = header.find(W+"tr").findall(W+"tc")
    assert header.find(W+"tblPr/"+W+"bidiVisual") is not None
    assert [cell.find(W+"tcPr/"+W+"shd").get(W+"fill") for cell in cells] == [color, color]
    title = next(x for x in root.find(W+"body").findall(W+"p")
                 if "رنچڠن ڤڠاجرن هارين" in "".join(n.text or "" for n in x.iter(W+"t")))
    assert title.find(W+"pPr/"+W+"jc").get(W+"val") == "center"


def test_all_native_math_science_years_use_exact_selected_source_labels_only():
    for subject in ("Matematik", "Sains"):
        for year in range(2, 7):
            state = _state(subject, year)
            state["_rph_verified_display_standard_pairs"] = [
                {"sk_code": "9.2", "sk_text": "9.2 Huraian sumber sebenar",
                 "sp_code": "9.2.1", "sp_text": "Menjelaskan konsep sumber"},
                {"sk_code": "9.2", "sk_text": "9.2 Huraian sumber sebenar",
                 "sp_code": "9.2.2", "sp_text": "Menerangkan contoh sumber"},
            ]
            original = {"STANDARD KANDUNGAN": "9.2",
                        "STANDARD PEMBELAJARAN": "9.2.1;9.2.2",
                        "AKTIVITI UTAMA": "Original activities",
                        "REFLEKSI": "Original reflection"}
            revised = display_verified_standards(state, original)
            assert revised["STANDARD KANDUNGAN"] == "9.2 Huraian sumber sebenar"
            assert revised["STANDARD PEMBELAJARAN"] == (
                "9.2.1 Menjelaskan konsep sumber; 9.2.2 Menerangkan contoh sumber")
            assert revised["AKTIVITI UTAMA"] == original["AKTIVITI UTAMA"]
            assert revised["REFLEKSI"] == original["REFLEKSI"]
            assert original["STANDARD PEMBELAJARAN"] == "9.2.1;9.2.2"
            assert display_verified_standards(state, revised) is revised
            assert display_verified_standards({**state, "programme": "DLP"}, original) is original


def test_missing_or_conflicting_source_labels_never_invent_or_partially_expand():
    state = _state("Sains", 3)
    source = [{"sk_code": "9.2", "sk_text": "First description",
               "sp_code": "9.2.1", "sp_text": "9.2.1"},
              {"sk_code": "9.2", "sk_text": "Conflicting description",
               "sp_code": "9.2.2", "sp_text": "Actual description"}]
    state["_rph_verified_display_standard_pairs"] = source
    rows = {"STANDARD KANDUNGAN": "9.2", "STANDARD PEMBELAJARAN": "9.2.1;9.2.2"}
    assert display_verified_standards(state, rows) is rows
    assert source[0]["sp_text"] == "9.2.1"


def test_previously_audited_official_label_has_priority_over_source_variant():
    state = _state("Matematik", 6)
    state["_rph_verified_display_standard_pairs"] = [
        {"sk_code": "1.1", "sk_text": "Source variant",
         "sp_code": "1.1.1", "sp_text": "Source variant"}
    ]
    rows = {"STANDARD KANDUNGAN": "1.1", "STANDARD PEMBELAJARAN": "1.1.1"}
    out = display_verified_standards(state, rows)
    assert out["STANDARD KANDUNGAN"] == "1.1 Nombor bulat hingga 10 000 000"
    assert out["STANDARD PEMBELAJARAN"].startswith("1.1.1 Membaca, menyebut dan menulis")


def test_pi_compact_identity_word_removes_only_labels_and_bolds_jawi():
    from test_pi_active_jawi_content_right_20261123 import formatted_original
    from web.rph_pi_compact_identity_20261124 import compact_pi_identity
    from docx import Document
    from io import BytesIO
    from lxml import etree
    from zipfile import ZipFile
    _, source = formatted_original()
    result = compact_pi_identity(source)
    assert result != source
    assert compact_pi_identity(result) == result
    doc = Document(BytesIO(result))
    before = Document(BytesIO(source))
    p = doc.tables[0].cell(0,0).paragraphs
    assert p[0].text == "ڤنديديقن اسلام"
    assert p[1].text == "تاهون ٣"
    assert p[0].runs[0].bold
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    assert doc.tables[0].cell(0,0).vertical_alignment == WD_CELL_VERTICAL_ALIGNMENT.CENTER
    assert p[2].text == before.tables[0].cell(0,0).paragraphs[2].text
    assert doc.tables[0].cell(0,1).text == before.tables[0].cell(0,1).text
    for a,b in zip(doc.tables[1:],before.tables[1:]):
        assert [[c.text for c in r.cells] for r in a.rows] == [[c.text for c in r.cells] for r in b.rows]
    with ZipFile(BytesIO(result)) as z:
        root=etree.fromstring(z.read("word/document.xml"))
        W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        first=root.find(W+"body").find(W+"tbl").find(W+"tr").find(W+"tc").find(W+"p")
        assert all(r.find(W+"rPr/"+W+"bCs").get(W+"val")=="1" for r in first.findall(W+"r"))

def test_pi_pdf_compact_identity_removes_only_two_labels():
    original=_pi_story()
    style=getSampleStyleSheet()["Normal"]
    original[2]._cellvalues[0][0]=Paragraph("ڤنديديقن اسلام",style)
    original[2]._cellvalues[1][0]=Paragraph("تاهون ٢",style)
    result=reflow_verified_pi_header({"task":"rph","subject":"Pendidikan Islam","year":"Tahun 2"},original)
    teacher, identity = result[2]._cellvalues[0]
    assert identity._cellvalues[0][0].getPlainText()=="ڤنديديقن اسلام"
    assert "<b>" in identity._cellvalues[0][0].text
    assert identity._cellvalues[1][0].text=="تاهون ٢"
    assert identity._cellvalues[0][1]==identity._cellvalues[1][1]==""
    assert identity._cellvalues[2]==original[2]._cellvalues[7]
    assert result[-3] is original[4] and result[-1] is original[6]

def test_pi_topic_duration_display_only():
    from web.rph_pi_topic_display_20261124 import clean_pi_topic
    samples = {
        "عقيدة ١ جم": "عقيدة",
        "القرءان ٣٠ مينيت": "القرءان",
        "القرءان ١ جم ٣٠ مينيت": "القرءان",
        "القرءان (تجويد) ٣٠ مينيت (اولڠن حكوم إظهار شفوي)": "القرءان (تجويد) (اولڠن حكوم إظهار شفوي)",
        "Jawi 1 jam setengah": "Jawi",
        "Jawi setengah jam": "Jawi",
        "Jawi 1 jam": "Jawi",
        "Surah ١": "Surah ١",
    }
    for source, expected in samples.items():
        assert clean_pi_topic(source)==expected
        assert clean_pi_topic(expected)==expected

def test_pi_pdf_topic_duration_and_vertical_center():
    original=_pi_story()
    style=getSampleStyleSheet()["Normal"]
    original[2]._cellvalues[0][0]=Paragraph("ڤنديديقن اسلام",style)
    original[2]._cellvalues[1][0]=Paragraph("تاهون ٢",style)
    original[2]._cellvalues[7][0]=Paragraph("القرءان ١ جم ٣٠ مينيت (اولڠن)",style)
    result=reflow_verified_pi_header({"task":"rph","subject":"Pendidikan Islam","year":"Tahun 2"},original)
    banner=result[2]
    identity=banner._cellvalues[0][1]
    assert identity._cellvalues[2][0].getPlainText()=="القرءان (اولڠن)"
    assert banner._cellStyles[0][1].valign=="MIDDLE"
    assert original[2]._cellvalues[7][0].getPlainText()=="القرءان ١ جم ٣٠ مينيت (اولڠن)"
    assert result[-3] is original[4] and result[-1] is original[6]
