"""Stage-only proof: render representative Music RPH with *unmodified base*
Telegram writer functions, isolated from app.py bootstrap and live DB.

This is NOT the complete layered production runtime or source-parity approval.
Writes only disposable /tmp files and a CI-only audit JSON report.
"""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import shutil
import subprocess
from unittest.mock import patch
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "staging" / "pendidikan_muzik" / "rpt_rph_2027"
NATIVE = ROOT / "web" / "native_rph_telegram_api.py"
BOT = ROOT / "app.py"
SELECTED = [(2, 1), (3, 20), (4, 21), (5, 34), (6, 35)]


def _compile_functions(source_file, wanted, *, last=()):
    # Never import app.py; it bootstraps the main curriculum DB.
    # Independently parse chosen functions to tolerate unrelated Python 3.12 syntax.
    contents = source_file.read_text(encoding='utf-8')
    if source_file == NATIVE:
        tree = ast.parse(contents, filename=str(source_file))
        entries = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                entries.setdefault(node.name, []).append(node)
        if set(entries) != set(wanted):
            raise RuntimeError('Web parser source changed')
        nodes = [entries[n][-1] if n in last else entries[n][0] for n in wanted]
        return compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(source_file), 'exec'), tree
    lines = contents.splitlines(keepends=True)
    entries = {}
    for i, line in enumerate(lines):
        if not line.startswith('def '):
            continue
        name = line.split('(', 1)[0][4:].strip()
        if name not in wanted:
            continue
        j = i + 1
        while j < len(lines):
            item = lines[j]
            if item.strip() and not item[0].isspace() and not item.lstrip().startswith('#'):
                break
            j += 1
        snippet = ''.join(lines[i:j])
        node = ast.parse(snippet, filename=str(source_file)).body[0]
        if not isinstance(node, ast.FunctionDef) or node.name != name:
            raise RuntimeError('Unexpected function snippet')
        entries.setdefault(name, []).append(node)
    if set(entries) != set(wanted):
        raise RuntimeError('Missing RPH native functions: ' + str(set(wanted) - set(entries)))
    nodes = [entries[n][-1] if n in last else entries[n][0] for n in wanted]
    return compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(source_file), 'exec'), None

def _preview_module():
    spec = importlib.util.spec_from_file_location("music_preview_for_base_smoke", SOURCE / "native_layout_preview_staging.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _web_parser():
    funcs = ("_require_text", "_metadata_dict", "_extract", "build_native_input")
    code, tree = _compile_functions(NATIVE, funcs)
    namespace = {"os": os, "re": re, "date": __import__("datetime").date,
                 "hmac": __import__("hmac")}
    for entry in tree.body:
        if isinstance(entry, ast.Assign):
            for target in entry.targets:
                if isinstance(target, ast.Name) and target.id in ("MIMES", "SUBJECTS", "LAYOUT_STYLE", "HEADINGS"):
                    namespace[target.id] = ast.literal_eval(entry.value)
    if "MUZIK" in namespace["SUBJECTS"]:
        raise RuntimeError("STOP: production whitelist changed; audit conditions invalid")
    exec(code, namespace)
    namespace["SUBJECTS"] = dict(namespace["SUBJECTS"], MUZIK="Pendidikan Muzik")  # isolated test only
    return namespace["build_native_input"]


def _native_base():
    functions = {
        "safe_filename", "clean_doc_text", "_word_set_cell_border",
        "_word_page_number", "_rph_session_meta", "_rph_blank_or_value",
        "_rph_attendance_value", "_parse_rph_sections", "_rph_rows",
        "_rph_format_activity_lines", "_rph_phase_time_v25179",
        "_create_rph_word", "create_word_file", "_is_english_subject",
        "_pdf_header_footer", "create_pdf_file",
    }
    code, _ = _compile_functions(BOT, functions, last={"_rph_format_activity_lines"})
    namespace = {
        "os": os, "tempfile": tempfile, "re": re, "Document": Document,
        "Pt": Pt, "Cm": Cm, "WD_ALIGN_PARAGRAPH": WD_ALIGN_PARAGRAPH,
        "WD_TABLE_ALIGNMENT": WD_TABLE_ALIGNMENT, "OxmlElement": OxmlElement,
        "qn": qn, "A4": A4, "mm": mm, "colors": colors,
        "TA_CENTER": TA_CENTER, "TA_LEFT": TA_LEFT,
        "getSampleStyleSheet": getSampleStyleSheet, "ParagraphStyle": ParagraphStyle,
        "SimpleDocTemplate": SimpleDocTemplate, "Paragraph": Paragraph,
        "Spacer": Spacer, "Table": Table, "TableStyle": TableStyle,
        "escape": escape,
    }
    exec(code, namespace)
    return namespace


def audit_one(year, pdp, fmt, preview, parse_input, writer, word_output_dir=None):
    meta = {item["label"]: item["value"] for item in preview["layout"]["header"]}
    payload = {
        "subject": "MUZIK", "component": None,
        "year": year, "lesson": pdp, "unit": meta["Tajuk"],
        "teacher": {"class": "", "date": "", "time": ""},
        "layout": preview["layout"], "format": fmt,
    }
    with patch.dict(os.environ, {"CIKGULAJU_WEB_RPH_SOURCE_PARITY_REQUIRED": "0"}):
        state, ai_text, fmt2 = parse_input(payload)
    if fmt2 != fmt:
        raise RuntimeError("Format mismatch")
    fn = writer["create_word_file"] if fmt == "word" else writer["create_pdf_file"]
    path = None
    try:
        path = Path(fn(state, ai_text, f"music_smoke_{year}_{pdp}_{fmt}"))
        if not path.is_file() or path.stat().st_size < 1000:
            raise RuntimeError("Empty RPH output")
        if fmt == "word":
            document = Document(path)
            if len(document.tables) != 3:
                raise RuntimeError(f"Expected 3 native Word tables, got {len(document.tables)}")
            activity = document.tables[1].cell(2, 1).text
            if not all(marker in activity for marker in ("Aktiviti 1", "Aktiviti 2", "Pengukuhan")):
                raise RuntimeError("Missing activity/pentaksiran in Word native table")
            sp_text = document.tables[0].cell(9, 1).text
            if not all(v in sp_text for v in meta["Standard Pembelajaran"].split("; ")):
                raise RuntimeError("Word SP source text lost")
            section = document.sections[0]
            a4 = abs(section.page_width.cm - 21.0) < 0.15 and abs(section.page_height.cm - 29.7) < 0.15
            if not a4:
                raise RuntimeError("Word section is not A4")
            if word_output_dir is not None:
                shutil.copy2(path, word_output_dir / f"MZ-Y{year}-{pdp:02d}.docx")
            return {"type": fmt, "bytes": path.stat().st_size, "tables": 3, "a4_section": a4,
                    "page_count": None}
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        if pages < 1:
            raise RuntimeError("PDF has no pages")
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        if "RANCANGAN PENGAJARAN HARIAN" not in text:
            raise RuntimeError("PDF main heading lost")
        box = reader.pages[0].mediabox
        if abs(float(box.width) - 595.28) > 3 or abs(float(box.height) - 841.89) > 3:
            raise RuntimeError("PDF size not A4")
        return {"type": fmt, "bytes": path.stat().st_size, "pages": pages,
                "single_page": pages == 1, "a4": True}
    finally:
        if path is not None and path.exists():
            path.unlink()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true", help="Render all 175, otherwise 5 representative lessons")
    args = p.parse_args()
    cases = [(year, pdp) for year in range(2, 7) for pdp in range(1, 36)] if args.all else SELECTED
    preview_mod = _preview_module()
    parser = _web_parser()
    native = _native_base()
    converter = shutil.which("libreoffice") or shutil.which("soffice")
    scratch = tempfile.TemporaryDirectory(prefix="music_word_pages_staging_")
    word_source = Path(scratch.name) / "docx"
    word_pdf = Path(scratch.name) / "pdf"
    if converter:
        word_source.mkdir()
        word_pdf.mkdir()
    results = []
    for year, pdp in cases:
        preview = preview_mod.build_staging_preview(SOURCE, year, pdp)
        record = {"year": year, "pdp": pdp, "source_id": preview["source_pdp_id"],
                  "approved_for_live": False, "render_kind": "BASE_FUNCTION_AST_ONLY"}
        for fmt in ("word", "pdf"):
            try:
                record[fmt] = audit_one(year, pdp, fmt, preview, parser, native, word_source if converter else None)
            except Exception as error:
                record[fmt] = {"error": type(error).__name__ + ": " + str(error)}
        results.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    failed = [r for r in results if "error" in r["word"] or "error" in r["pdf"]]
    word_page_report = {"measured": False, "converter_available": bool(converter),
                        "single_page_count": None, "multi_page": [],
                        "reason": "LibreOffice/soffice not installed"}
    if converter and not failed:
        sources = sorted(word_source.glob("*.docx"))
        try:
            cmd = [converter, "-env:UserInstallation=file://" + str(Path(scratch.name) / "lo_profile"),
                   "--headless", "--convert-to", "pdf", "--outdir", str(word_pdf)]
            proc = subprocess.run(cmd + [str(x) for x in sources],
                                  capture_output=True, text=True, timeout=240, check=False)
            if proc.returncode != 0:
                raise RuntimeError("LibreOffice conversion failed: " + (proc.stderr or proc.stdout)[-500:])
            overs = []
            converted = 0
            for source in sources:
                result = word_pdf / (source.stem + ".pdf")
                if not result.is_file():
                    raise RuntimeError("Word conversion missing: " + source.name)
                count = len(PdfReader(str(result)).pages)
                converted += 1
                if count != 1:
                    overs.append({"source": source.stem, "pages": count})
            word_page_report = {"measured": True, "converter_available": True,
                                "converted": converted, "single_page_count": converted-len(overs),
                                "multi_page": overs, "reason": None}
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            word_page_report = {"measured": False, "converter_available": True,
                                "single_page_count": None, "multi_page": [],
                                "reason": type(error).__name__ + ": " + str(error)}
    scratch.cleanup()
    report = {
        "scope": "STAGING_BASE_NATIVE_RENDER_SMOKE_NOT_LIVE",
        "fully_covered": args.all,
        "cases": len(results), "docx_ok": sum("error" not in r["word"] for r in results),
        "pdf_ok": sum("error" not in r["pdf"] for r in results),
        "single_page_pdf": sum(r["pdf"].get("single_page") is True for r in results),
        "word_page_audit": word_page_report,
        "errors": failed,
        "disclaimer": "AST-extracted base RPH functions are not the full Telegram production wrapper chain; LibreOffice Word-page measurements when present are staging-only and cross-platform release remains unverified.",
    }
    path = Path(os.getenv("MUSIC_SMOKE_REPORT", "/tmp/music_native_base_render_smoke.json"))
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("AUDIT SUMMARY " + json.dumps({k: v for k, v in report.items() if k != "errors"}, ensure_ascii=False))
    if failed:
        raise SystemExit(f"BASE_RENDER_SMOKE FAILED: {len(failed)} case(s)")


if __name__ == "__main__":
    main()
