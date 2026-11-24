"""Non-destructive pastel RPH Word contract: protect Sains, DLP and PPKI."""
import io
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn

from web.rph_reference_style_20261121 import (
    _preserves_source_content, color_for_state, install,
    style_three_table_word_bytes, style_word_path,
)


def _fixture(title="RANCANGAN PENGAJARAN HARIAN"):
    doc = Document()
    doc.add_paragraph(title)
    header = doc.add_table(rows=5, cols=2)
    for index, label in enumerate(("Subjek", "Kelas", "Tarikh", "Masa", "Bilangan Murid")):
        header.cell(index, 0).text = label
        header.cell(index, 1).text = ["Bahasa Melayu", "", "", "", ""][index]
    phases = doc.add_table(rows=4, cols=3)
    for index, (label, activity) in enumerate((
        ("Fasa", "Aktiviti Pengajaran dan Pembelajaran"),
        ("Set Induksi", "Guru menerangkan."),
        ("Aktiviti 1", "Murid mengenal pasti maklumat."),
        ("Penutup", "Murid merumuskan hasil."),
    )):
        phases.cell(index, 0).text = label
        phases.cell(index, 1).text = activity
        phases.cell(index, 2).text = "Nota" if index == 0 else ""
    foot = doc.add_table(rows=2, cols=2)
    foot.cell(0, 0).text = "SK / SP"
    foot.cell(0, 1).text = "1.1 Memahami, 1.1.1 Mengenal pasti."
    foot.cell(1, 0).text = "Refleksi"
    foot.cell(1, 1).text = ""
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def _visible(data):
    from lxml import etree
    with ZipFile(io.BytesIO(data)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    return tuple(element.text for element in root.iter(qn("w:t")))


def test_ten_sk_subjects_only_change_word_presentation():
    before = _fixture()
    for subject in (
        "Bahasa Melayu", "English", "Matematik", "Pendidikan Islam",
        "Sejarah", "Pendidikan Muzik", "Pendidikan Jasmani dan Pendidikan Kesihatan",
        "Pendidikan Jasmani", "Pendidikan Kesihatan",
        "Pendidikan Moral", "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi",
    ):
        fill = color_for_state({"task": "rph", "subject": subject})
        assert fill
        after = style_three_table_word_bytes(before, fill)
        assert after != before, subject
        assert _visible(after) == _visible(before), subject
        doc = Document(io.BytesIO(after))
        assert len(doc.tables) == 3
        assert len(doc.tables[0].rows) == 5
        assert len(doc.tables[1].columns) == 3
        assert doc.tables[0].cell(1, 1).text == ""  # teacher box stays genuinely blank
        assert doc.tables[1].cell(2, 1).text == "Murid mengenal pasti maklumat."
        with ZipFile(io.BytesIO(after)) as archive:
            content = archive.read("word/document.xml")
            assert b"w:pBdr" in content
            assert fill.encode() in content


def test_reference_subjects_and_non_rph_are_unchanged():
    for state in (
        {"task": "rph", "subject": "Science"},
        {"task": "rph", "subject": "Matematik", "curriculum_version": "DLP"},
        {"task": "rph", "subject": "English", "programme": "PPKI"},
        {"task": "rph", "subject": "Bahasa Arab"},
        {"task": "rpt", "subject": "Bahasa Melayu"},
    ):
        assert color_for_state(state) is None, state


def test_native_sains_pastel_only_without_other_specialty_subjects():
    assert color_for_state({"task": "rph", "subject": "Sains"}) == "E7F3EA"
    assert color_for_state({"task": "rph", "subject": "Sains", "curriculum": "DLP"}) is None


def test_three_table_contract_prevents_unexpected_rph_mutation():
    original = _fixture()
    doc = Document(io.BytesIO(original))
    doc.add_table(rows=1, cols=2)
    out = io.BytesIO()
    doc.save(out)
    after = style_three_table_word_bytes(out.getvalue(), "F0EBFA")
    assert after == out.getvalue()


def test_preserves_untouched_zip_parts():
    before = _fixture()
    after = style_three_table_word_bytes(before, "EAF1FB")
    with ZipFile(io.BytesIO(before)) as a, ZipFile(io.BytesIO(after)) as b:
        assert a.namelist() == b.namelist()
        for name in a.namelist():
            if name != "word/document.xml":
                assert a.read(name) == b.read(name)


def test_install_keeps_original_on_nonreference_and_double_install():
    class Runtime:
        def __init__(self):
            self.calls = []
        def create_word_file(self, state, source_text, chat_id):
            self.calls.append(state["subject"])
            return "/nonexistent.docx"
    runtime = Runtime()
    assert install(runtime)
    first = runtime.create_word_file
    assert install(runtime)
    assert runtime.create_word_file is first
    assert runtime.create_word_file({"task":"rph","subject":"Sains"}, "", "test") == "/nonexistent.docx"
    assert runtime.calls == ["Sains"]


def test_final_guard_accepts_presentation_but_preserves_full_source_package(tmp_path):
    original = _fixture()
    styled = style_three_table_word_bytes(original, "EAF1FB")
    assert styled != original
    assert _preserves_source_content(original, styled)
    word = tmp_path / "original_rph.docx"
    word.write_bytes(original)
    assert style_word_path(word, "EAF1FB")
    assert word.read_bytes() == styled
    assert _visible(word.read_bytes()) == _visible(original)


def test_final_guard_rejects_missing_or_changed_sk_sp_even_if_zip_is_valid(
    monkeypatch, tmp_path,
):
    import web.rph_reference_style_20261121 as presentation

    original = _fixture()
    doc = Document(io.BytesIO(original))
    doc.tables[2].cell(0, 1).text = "1.1.2 Standard telah diubah."
    modified = io.BytesIO()
    doc.save(modified)
    tampered = modified.getvalue()
    assert not _preserves_source_content(original, tampered)

    word = tmp_path / "original_rph.docx"
    word.write_bytes(original)
    # Simulate a faulty future presentation adapter: do not let it replace Word.
    monkeypatch.setattr(presentation, "style_three_table_word_bytes",
                        lambda document, fill: tampered)
    assert not style_word_path(word, "EAF1FB")
    assert word.read_bytes() == original


def test_final_guard_refuses_changes_to_fonts_styles_and_attachments():
    original = _fixture()
    with ZipFile(io.BytesIO(original)) as archive:
        updated = io.BytesIO()
        with ZipFile(updated, "w") as target:
            for member in archive.infolist():
                content = archive.read(member.filename)
                if member.filename == "word/styles.xml":
                    content += b" "
                target.writestr(member, content)
    assert not _preserves_source_content(original, updated.getvalue())


def test_final_guard_fails_closed_for_broken_word_zip():
    original = _fixture()
    assert not _preserves_source_content(original, b"not a Word file")
    assert not _preserves_source_content(original, original[:130])
