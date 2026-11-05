"""Physically render two source-backed Year5 draft RPH Word docs to A4 PDFs.

AST-matched production Word document builder, LibreOffice PDF conversion;
read-only draft QA. No Telegram requests, user DB/credit mutations or audio.
LibreOffice conversions do not certify the native Telegram PDF runtime.
"""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from pypdf import PdfReader
from tools.audit_english_rph_word_a4_layout import (
    from_source, write_word, validate_word_function_snapshot
)
from tools.verify_english_800_word_a4 import all_text

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output/english_y5_l029_l030_physical_word_a4_20261105"
DOCS=OUT/"docx"
PDFS=OUT/"pdf"

def main():
    validate_word_function_snapshot()
    DOCS.mkdir(parents=True,exist_ok=True)
    PDFS.mkdir(parents=True,exist_ok=True)
    docs=[]
    checks=[]
    for lesson,required in [(29,("Tobias","1.2.5","4.3.2")),
                            (30,("Eriko","2.2.1","1.2.5"))]:
        source=ROOT/f"rph_standalone/english/year5/lesson_{lesson:03}.md"
        fields=from_source(5,lesson)
        document=DOCS/f"Y5_L{lesson:03}.docx"
        write_word(5,lesson,fields,document)
        word_text=all_text(document)
        for token in required:
            if token not in word_text:
                raise AssertionError(f"Year5 L{lesson}: missing {token} from Word text")
        docs.append(document)
        checks.append({"lesson":lesson,"source_sha256":sha256(source.read_bytes()).hexdigest(),
                       "docx_sha256":sha256(document.read_bytes()).hexdigest(),
                       "word_chars":len(word_text),"source_field_count":len(fields)})
    cmd=["libreoffice","-env:UserInstallation=file://"+str(OUT/"lo-profile"),
         "--headless","--convert-to","pdf","--outdir",str(PDFS),
         *[str(x) for x in docs]]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=120,check=False)
    if proc.returncode!=0:
        raise RuntimeError("LibreOffice conversion failed: "+proc.stderr[-1000:])
    for record in checks:
        lesson=record["lesson"]
        path=PDFS/f"Y5_L{lesson:03}.pdf"
        if not path.exists():
            raise AssertionError(f"Year5 L{lesson} PDF was not created")
        pages=PdfReader(str(path)).pages
        text="\n".join((page.extract_text() or "") for page in pages)
        a4=len(pages)==1 and all(
            abs(float(page.mediabox.width)-595.28)<1.5 and
            abs(float(page.mediabox.height)-841.89)<1.5 for page in pages)
        record.update({"pages":len(pages),"one_page_a4":a4,
                       "pdf_chars":len(text),
                       "pdf_content_ratio":round(len(text)/max(1,record["word_chars"]),3),
                       "pdf_sha256":sha256(path.read_bytes()).hexdigest()})
        if not a4 or len(text)<0.60*record["word_chars"]:
            raise AssertionError(f"Year5 L{lesson} Word/PDF render A4 or text error: {record}")
    report={"method":"AST-locked active Word renderer + LibreOffice PDF approximate print",
            "validated_lessons":[29,30],"source_verified_audio_content":False,
            "telegram_sent":False,"teacher_approved":False,
            "native_telegram_pdf_verified":False,"per_lesson_word_a4_verified":True,
            "results":checks}
    (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("ENGLISH_Y5_L029_L030_WORD_PHYSICAL_A4",json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
