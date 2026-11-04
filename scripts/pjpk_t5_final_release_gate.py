"""Final, read-only T5 PK release gate; source gate success alone is insufficient.

Run: python -m scripts.pjpk_t5_final_release_gate
Exit 2 means pending evidence; exit 1 means malformed/inconsistent evidence.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'pjpk'
FLAGS = ('dskp_verified', 'textbook_verified', 'rpt_exact_slot_verified',
         'rph_runtime_verified', 'a4_review_verified')


def read(name):
    with (ROOT / name).open(encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    result = {r['entry_id']: r for r in rows}
    if len(result) != len(rows) or set(result) != {'2259', '2260', '2261'}:
        raise ValueError(f'{name}: expected three distinct T5 PK IDs')
    return result


def audit():
    evidence = read('T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv')
    checklist = read('T5_PK_3_REMAINING_RELEASE_CHECKLIST_20261024.csv')
    queue = read('T5_PK_PRIORITY_3_SOURCE_QUEUE_20261024.csv')
    pending = []
    for ident, row in evidence.items():
        if row['year_label'] != 'Tahun 5' or row['subject'] != 'Pendidikan Kesihatan':
            raise ValueError(f'{ident}: wrong identity')
        for flag in (*FLAGS, 'production_ready'):
            if row[flag] not in ('0', '1') or checklist[ident][flag] != row[flag]:
                raise ValueError(f'{ident}: invalid or conflicting {flag}')
        if queue[ident]['book_exact_match'] != row['textbook_verified'] or queue[ident]['production_ready'] != row['production_ready']:
            raise ValueError(f'{ident}: source queue mismatch')
        missing = [flag for flag in FLAGS if row[flag] != '1']
        if row['production_ready'] == '1' and missing:
            raise ValueError(f'{ident}: premature production promotion: {missing}')
        if missing or row['production_ready'] != '1':
            pending.append((ident, missing or ['production_ready']))
    return pending


if __name__ == '__main__':
    try:
        blocked = audit()
    except (ValueError, KeyError) as exc:
        print(f'INVALID: {exc}', file=sys.stderr)
        raise SystemExit(1)
    for ident, missing in blocked:
        print(f'BLOCK {ident}: {", ".join(missing)}')
    if blocked:
        raise SystemExit(2)
    print('All three T5 PK entries passed final evidence gate; production deployment remains a separate action.')
