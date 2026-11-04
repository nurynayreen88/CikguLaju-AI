"""Offline Word A4 QA for nine English Y5 teacher-choice proposals.

Uses AST-matched active Word table builder (isolated copy, never app import);
converts with LibreOffice, checks all 9 one-page A4 and content retention.
This is not a claim of live Telegram delivery or native ReportLab PDF.
"""
import json
from pathlib import Path
import subprocess
import sys

from docx import Document
from docx.shared import Cm, Pt
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.audit_english_rph_word_a4_layout import validate_word_function_snapshot
from qa.english_word_builder_snapshot import _create_rph_word
from web.english_y5_teacher_choice_runtime import adapt_rows
from web.english_y5_standalone_runtime import CHOICE_LESSONS
from web.english_y6_word_a4_runtime import compact_word_file

OUT = ROOT / "output" / "english_y5_teacher_choice_a4_review"


def collect_text(path):
    doc = Document(str(path))
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                lines.extend(p.text for p in cell.paragraphs)
    return "\n".join(lines)


def create_word(n, path):
    state = {"subject":"English", "year":"Year 5",
             "task":"rph", "lesson_no":n}
    base = {
        "MATA PELAJARAN":"English", "TAHUN/TINGKATAN":"Year 5",
        "TARIKH":"04/11/2026", "HARI":"Wednesday",
        "MASA":"09:00 - 10:00", "KELAS":"5 Amanah",
        "BILANGAN MURID":"30",
        "TAJUK":"Old generic RPH",
        "MAIN CONTENT STANDARD":"OLD",
        "MAIN LEARNING STANDARD":"OLD",
        "COMPLEMENTARY CONTENT STANDARD":"OLD",
        "COMPLEMENTARY LEARNING STANDARD":"OLD",
        "OBJEKTIF PEMBELAJARAN":"Old generic objective",
        "KRITERIA KEJAYAAN":"Old generic criteria",
        "PENGETAHUAN SEDIA ADA":"Familiar unit vocabulary",
        "BAHAN BANTU MENGAJAR":"Old generic materials",
        "EMK / NILAI":"Communication; collaboration",
        "KBAT / PAK21":"Pair work and group reasoning",
        "PENTAKSIRAN":"Old assessment",
        "SET INDUKSI":"Old induction",
        "AKTIVITI UTAMA":"Old activities",
        "PENUTUP":"Old closure",
        "PEMULIHAN / PENGAYAAN":"Support and extension",
        "REFLEKSI":"___/___ achieved; ___/___ need support",
    }
    rows = adapt_rows(state, base)
    if rows is base:
        raise RuntimeError(f"Y5 L{n}: proposal not mapped")
    doc = Document()
    section = doc.sections[0]
    section.top_margin=Cm(1.35)
    section.bottom_margin=Cm(1.4)
    section.left_margin=Cm(1.55)
    section.right_margin=Cm(1.55)
    doc.styles["Normal"].font.name="Arial"
    doc.styles["Normal"].font.size=Pt(10.5)
    _create_rph_word(doc, section, state, rows, str(path))
    return rows


def main():
    validate_word_function_snapshot()
    word = OUT / "word"
    pdf = OUT / "pdf"
    word.mkdir(parents=True, exist_ok=True)
    pdf.mkdir(parents=True, exist_ok=True)
    files = []
    records = []
    for n in sorted(CHOICE_LESSONS):
        path = word / ("English_Y5_L%03d_Proposal.docx" % n)
        rows = create_word(n, path)
        before = collect_text(path)
        if not compact_word_file(path):
            raise RuntimeError("Word A4 compaction failed for Lesson " + str(n))
        after = collect_text(path)
        if before != after:
            raise RuntimeError("Compactor lost source text for Lesson " + str(n))
        if "CADANGAN CIKGULAJU (DRAF)" not in after:
            raise RuntimeError("Draft label absent from document for Lesson " + str(n))
        if "Teacher to choose Year 5 DSKP standard" not in after:
            raise RuntimeError("Teacher-choice standard notice missing for Lesson " + str(n))
        if "Teacher:" not in after or "Pupils:" not in after:
            raise RuntimeError("Missing distinct teacher/pupil actions for Lesson " + str(n))
        if "Generic RPH" in after:
            raise RuntimeError("Legacy generic RPH leaked for Lesson " + str(n))
        files.append(path)
        records.append({"lesson":n,"word":path.name,"chars":len(after),
                        "phase_chars":sum(len(rows[k]) for k in
                            ("SET INDUKSI","AKTIVITI UTAMA","PENTAKSIRAN","PENUTUP"))})
    profile = OUT / "lo-profile"
    cmd=["libreoffice", "-env:UserInstallation=file://"+str(profile),
         "--headless","--convert-to","pdf","--outdir",str(pdf),
         *[str(p) for p in files]]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
    if run.returncode:
        raise RuntimeError("LibreOffice export failed: " + run.stderr[-1000:])
    for r in records:
        path=pdf / r["word"].replace(".docx", ".pdf")
        if not path.is_file():
            raise RuntimeError("PDF conversion missing: "+str(path))
        pages=PdfReader(str(path)).pages
        r["pages"]=len(pages)
        r["a4"]=all(abs(float(x.mediabox.width)-595.28)<1.5 and
                    abs(float(x.mediabox.height)-841.89)<1.5 for x in pages)
        text_content="\n".join(page.extract_text() or "" for page in pages)
        r["pdf_contains_draft_notice"]="CADANGAN CIKGULAJU" in text_content
        r["pdf_contains_teacher_actions"]="Teacher:" in text_content
        r["pdf_contains_pupil_actions"]="Pupils:" in text_content
    OUT.joinpath("report.json").write_text(
        json.dumps({"status":"offline Word one-page A4 only",
                    "lesson_count":len(records),"lessons":records},
                   ensure_ascii=False,indent=2),encoding="utf-8")
    print("Y5_TEACHER_CHOICE_A4_AUDIT",json.dumps(records),flush=True)
    if any(not (r["pages"]==1 and r["a4"] and
                r["pdf_contains_draft_notice"] and
                r["pdf_contains_teacher_actions"] and
                r["pdf_contains_pupil_actions"]) for r in records):
        raise SystemExit("One or more Year5 teacher-choice RPH did not fit 1-page A4 or lost text")


if __name__=="__main__":
    main()
