"""Read-only integrity check for Matematik T4 v17 crosswalk vs 83 DOCX package.

No database, Flask import, network call, file extraction, or runtime activation.
Requires package.zip and v17 JSON manifest. Returns 0 for matching *PRA-READY*
files, not permission to deploy them.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

FILE_RE = re.compile(r'^RPH_T4_(\d{2}|11[A-C])_PRA_READY\.docx$')


def check(package_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    records = manifest['rph']
    errors = []
    ids = [r['rph_id'] for r in records]
    if len(records) != 83 or len(set(ids)) != 83:
        errors.append('Expected 83 unique records')
    if sorted(set(r['rpt2027_block'] for r in records)) != list(range(1, 43)):
        errors.append('Missing RPT content block')
    if any(r['runtime_approved'] or r['source_status'] != 'PRA-READY' for r in records):
        errors.append('Unexpected READY/approved status')
    if manifest.get('release_allowed') is not False:
        errors.append('Guard must keep release_allowed=false')
    with zipfile.ZipFile(package_path) as archive:
        found = {}
        for item in archive.infolist():
            if item.is_dir():
                continue
            m = FILE_RE.fullmatch(Path(item.filename).name)
            if not m:
                continue
            key = m.group(1)
            if key in found:
                errors.append('Duplicate RPH '+key)
                continue
            if item.file_size > 2_000_000:
                errors.append('Oversized Word '+key)
                continue
            found[key] = hashlib.sha256(archive.read(item)).hexdigest()
    if set(ids) != set(found):
        errors.append('Manifest/ZIP ID mismatch')
    for entry in records:
        if found.get(entry['rph_id']) != entry['sha256_docx']:
            errors.append('SHA mismatch '+entry['rph_id'])
    return {'checked':len(found),'release_allowed':False,'integrity_ok':not errors,'errors':errors}


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=2:
        print('Usage: python tools/check_matematik_t4_crosswalk.py package.zip manifest.json', file=sys.stderr)
        return 64
    try:
        result=check(*args)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile,json.JSONDecodeError) as e:
        result={'integrity_ok':False,'release_allowed':False,'errors':[str(e)]}
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['integrity_ok'] else 2

if __name__=='__main__':
    raise SystemExit(main())