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
    HEADER_LABELS, reflow_verified_pi_header,
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
    assert revised[0] is original[0]
    assert revised[-3] is original[4]
    assert revised[-1] is original[6]
    banner=revised[2]
    left,right=banner._cellvalues[0]
    assert len(left._cellvalues)==3
    assert len(right._cellvalues)==5
    assert [row[1].text for row in left._cellvalues] == [
        HEADER_LABELS[i] for i in (0,1,7)]
    assert [row[1].text for row in right._cellvalues] == [
        HEADER_LABELS[i] for i in (5,2,3,4,6)]
    body=revised[4]
    assert len(body._cellvalues)==9
    after=Counter(id(v) for table in (left,right,body)
                  for row in table._cellvalues for v in row)
    assert before==after
    assert any(row[0]=="BACKGROUND" for row in banner._bkgrndcmds)
    assert reflow_verified_pi_header({"task":"rph","subject":"Bahasa Arab"},original) is original
    broken=_pi_story()
    broken[2]._cellvalues[0][1].text="Unknown"
    assert reflow_verified_pi_header(state,broken) is broken
