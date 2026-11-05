"""Full *Word-rendered*, A4, one-page PSV RPH QA (210 offline drafts).

LibreOffice converts generated Word files to PDF for visual pagination inspection.
This is an isolated QA simulation, not an active Telegram RPH renderer.
Does not write to main or database; staged RPH always loaded with preview=True.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rph_standalone.psv.preview_a4 import load, word  # noqa: E402


def run(output_path: Path, *, batch_size: int = 25) -> dict:
    if batch_size < 1 or batch_size > 50:
        raise ValueError('batch_size must be 1..50')
    result = {
        'scope': '210 staged PSV RPH Word previews, LibreOffice A4 pagination; NOT Telegram LIVE',
        'status': 'STAGING QA ONLY / NOT FINAL READY',
        'years': [2, 3, 4, 5, 6],
        'tested': 0, 'one_page_a4': 0, 'not_one_page': [],
        'errors': [], 'batch_conversion': []
    }
    with tempfile.TemporaryDirectory(prefix='psv-word-qa-') as tmp:
        root = Path(tmp)
        docs_dir = root / 'docx'
        pdfs_dir = root / 'converted'
        docs_dir.mkdir()
        pdfs_dir.mkdir()
        files = []
        for year in range(2, 7):
            for pdp in range(1, 43):
                name = f'PSV_Y{year}_PdP{pdp:03d}'
                doc_file = docs_dir / (name + '.docx')
                try:
                    data = load(year, pdp, preview=True)
                    word(data, doc_file)
                    d = Document(doc_file)
                    page = d.sections[0]
                    if abs(page.page_width.cm - 21) > .1 or abs(page.page_height.cm - 29.7) > .1:
                        raise RuntimeError('DOCX paper is not A4')
                    if 'DRAF' not in data['metadata']['Status'].upper():
                        raise RuntimeError('Staging source lost draft status')
                    files.append((year, pdp, doc_file))
                except Exception as exc:
                    result['errors'].append({'year': year, 'pdp': pdp, 'stage': 'Word generation', 'error': repr(exc)})
        for start in range(0, len(files), batch_size):
            selected = files[start:start + batch_size]
            argv = [
                'libreoffice',
                '-env:UserInstallation=file://' + str(root / 'lo-profile'),
                '--headless', '--convert-to', 'pdf',
                '--outdir', str(pdfs_dir),
                *[str(f) for _, _, f in selected]
            ]
            run_out = subprocess.run(argv, capture_output=True, text=True, timeout=240)
            result['batch_conversion'].append({
                'start': start, 'count': len(selected),
                'returncode': run_out.returncode, 'stderr_tail': run_out.stderr[-350:]
            })
        for year, pdp, doc_file in files:
            result['tested'] += 1
            pdf_path = pdfs_dir / (doc_file.stem + '.pdf')
            if not pdf_path.is_file():
                result['errors'].append({'year': year, 'pdp': pdp, 'stage': 'Word to PDF', 'error': 'No output'})
                continue
            try:
                pages = PdfReader(str(pdf_path)).pages
                a4 = bool(pages) and all(
                    abs(float(p.mediabox.width) - 595.28) < 1.5 and
                    abs(float(p.mediabox.height) - 841.89) < 1.5 for p in pages
                )
                if len(pages) == 1 and a4:
                    result['one_page_a4'] += 1
                else:
                    result['not_one_page'].append({'year': year, 'pdp': pdp, 'pages': len(pages), 'A4': a4})
                text = '\n'.join(p.extract_text() or '' for p in pages)
                if f'PdP {pdp:03d}' not in text or f'TAHUN {year}' not in text:
                    result['errors'].append({'year': year, 'pdp': pdp, 'stage': 'Text fidelity', 'error': 'Title lost'})
                if 'DRAF SEMAK' in text:
                    result['errors'].append({'year': year, 'pdp': pdp, 'stage': 'Internal status leakage', 'error': 'DRAF label'})
            except Exception as exc:
                result['errors'].append({'year': year, 'pdp': pdp, 'stage': 'PDF inspection', 'error': repr(exc)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'tested': result['tested'],
        'one_page_a4': result['one_page_a4'],
        'not_one_page': result['not_one_page'],
        'errors': result['errors'],
    }, ensure_ascii=False))
    if result['tested'] != 210 or result['one_page_a4'] != 210 or result['not_one_page'] or result['errors']:
        raise RuntimeError('PSV staged Word one-page A4 gate FAILED; see report JSON')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=ROOT / 'output' / 'psv_word_a4_20261105' / 'report.json')
    p.add_argument('--batch-size', type=int, default=25)
    args = p.parse_args()
    run(args.output, batch_size=args.batch_size)
