"""Fail-closed quality gate for CikguLaju Pendidikan Islam 2027.

Does not publish, mutate archives, change databases, or certify religious content.
The professional teacher sign-off is an independent requirement, not inferred
from ZIP integrity or PDF page count. Pure stdlib for GitHub CI.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

EXPECTED_COUNTS={2:112,3:147,4:151,5:143,6:143}
EXPECTED_TOTAL=sum(EXPECTED_COUNTS.values())
EXPECTED_HELD={(2,35),(6,6),(6,14),(6,18),(6,60),(6,117)}
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
DRAFT_LABEL=re.compile(r'(?:STATUS\s*:\s*DRAF|DRAF STAGING|DRAF GANTI|AUDIT SUMBER|NOTA PEMBETULAN|belum disahkan|TAHAN_SEMAKAN)',re.I)

class ReleaseValidationError(ValueError):
    pass


def read_word_text(raw:bytes)->str:
    if not raw.startswith(b'PK\x03\x04'):
        raise ReleaseValidationError('Invalid Word magic')
    try:
        with zipfile.ZipFile(BytesIO(raw)) as z:
            root=ET.fromstring(z.read('word/document.xml'))
    except (ET.ParseError,KeyError,zipfile.BadZipFile) as exc:
        raise ReleaseValidationError('Invalid Word XML') from exc
    return '\n'.join(n.text or '' for n in root.iter(W+'t'))


def analyze(candidate_archive,preview_archive,signoff=None):
    """Validate both staging source archives and human approval record.

    Returns a non-publishable result whenever any content or release gate fails.
    The lack of a signed approval file is by design a blocker.
    """
    with zipfile.ZipFile(candidate_archive) as a,zipfile.ZipFile(preview_archive) as b:
        if a.testzip() or b.testzip():
            raise ReleaseValidationError('Bad ZIP CRC')
        main_manifest=json.loads(a.read('KATALOG/manifest_v5.json'))
        preview_manifest=json.loads(b.read('KATALOG/preview_manifest.json'))
        if main_manifest.get('status')!='STAGING_NOT_READY' or preview_manifest.get('status')!='STAGING_ONLY_NOT_PUBLISHED':
            raise ReleaseValidationError('Unexpected draft source manifest')
        docs=json.loads(a.read('KATALOG/catalog.json'))
        pdfs=json.loads(b.read('KATALOG/preview_catalog.json'))
        if len(docs)!=EXPECTED_TOTAL or len(pdfs)!=EXPECTED_TOTAL:
            raise ReleaseValidationError('Unexpected inventory totals')
        doc_idx={(r['tahun'],r['lesson']):r for r in docs}
        pdf_idx={(r['tahun'],r['lesson']):r for r in pdfs}
        if len(doc_idx)!=EXPECTED_TOTAL or len(pdf_idx)!=EXPECTED_TOTAL or doc_idx.keys()!=pdf_idx.keys():
            raise ReleaseValidationError('Duplicate/missing/mismatched lesson')
        years=Counter(y for y,l in doc_idx)
        if dict(years)!=EXPECTED_COUNTS:raise ReleaseValidationError('Unexpected year distribution')
        approvals={}
        if signoff is not None:
            for r in signoff:
                pair=(int(r['tahun']),int(r['lesson']))
                if pair in approvals:raise ReleaseValidationError('Duplicate teacher approval')
                approvals[pair]=r
        result=[]
        for (y,l),r in sorted(doc_idx.items()):
            pdf=pdf_idx[(y,l)]
            if r.get('rph_state') not in {'CALON_UJIAN_GURU_DRAF','SEMAKAN_KEUTAMAAN','TAHAN_SEMAKAN_KANDUNGAN'}:
                raise ReleaseValidationError('Unknown source state')
            if (r.get('rph_state')=='TAHAN_SEMAKAN_KANDUNGAN') != ((y,l) in EXPECTED_HELD):
                raise ReleaseValidationError('Unexpected held lesson status')
            if pdf.get('publish')!='STAGING_ONLY':
                raise ReleaseValidationError('Source PDF unexpectedly marked published')
            word=a.read(r['rph_path'])
            image=b.read(pdf['pdf_path'])
            if hashlib.sha256(word).hexdigest()!=r['rph_sha256']:
                raise ReleaseValidationError(f'Word SHA differs: {y}-{l}')
            if hashlib.sha256(image).hexdigest()!=pdf['pdf_sha256'] or not image.startswith(b'%PDF-'):
                raise ReleaseValidationError(f'PDF SHA differs: {y}-{l}')
            txt=read_word_text(word)
            is_held=(y,l) in EXPECTED_HELD
            label=bool(DRAFT_LABEL.search(txt))
            approved=approvals.get((y,l)) or {}
            # Reject approvals without source-level record and matching exact bytes.
            signed=(approved.get('decision')=='LULUS'
                    and approved.get('rph_sha256')==r['rph_sha256']
                    and approved.get('pdf_sha256')==pdf['pdf_sha256']
                    and bool(str(approved.get('penyemak','')).strip())
                    and bool(str(approved.get('tarikh','')).strip())
                    and bool(str(approved.get('bukti_dskp','')).strip())
                    and bool(str(approved.get('bukti_buku_teks_atau_mushaf','')).strip())
                    and approved.get('semak_jawi_tasmi')=='YA'
                    and approved.get('semak_objektif_aktiviti_pbd')=='YA')
            issue=[]
            if is_held:issue.append('RPH_DITAHAN')
            if label:issue.append('NOTA_DRAF_DALAMAN_WORD')
            if not signed:issue.append('BELUM_SAH_GURU_INDVIDU')
            if pdf.get('publish')!='READY':issue.append('PDF_PRATONTON_DRAF')
            result.append({'tahun':y,'lesson':l,'id':r['lesson_id'],
               'status_sumber':r['rph_state'], 'ditahan':is_held,
               'nota_dalaman_word':label, 'guru_sahkan':bool(signed),
               'status_pdf':pdf.get('publish'), 'sha_word':r['rph_sha256'],
               'sha_pdf':pdf['pdf_sha256'], 'boleh_terbit':not issue,
               'halangan':';'.join(issue)})
    summaries=Counter(k for rr in result for k in rr['halangan'].split(';') if k)
    return {'rph_count':len(result),'year_counts':dict(years),
            'publish':all(x['boleh_terbit'] for x in result),
            'gate':'GO' if all(x['boleh_terbit'] for x in result) else 'NO_GO',
            'blocker_counts':dict(summaries),'records':result,
            'release_policy':'No automatic READY from PDF/ZIP checks, reviewer identity and documentary proof mandatory'}


def write_csv(audit,path):
    cols=['tahun','lesson','id','status_sumber','ditahan','nota_dalaman_word','guru_sahkan','status_pdf','sha_word','sha_pdf','boleh_terbit','halangan']
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(audit['records'])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('word_bundle');p.add_argument('pdf_bundle')
    p.add_argument('--out',default='pi_release_gate.json')
    args=p.parse_args()
    result=analyze(args.word_bundle,args.pdf_bundle)
    Path(args.out).write_text(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False,indent=2),encoding='utf-8')
    write_csv(result,Path(args.out).with_suffix('.csv'))
    print(result['gate'],result['rph_count'],result['blocker_counts'])
    # Nonzero exit deliberately prevents a CI release job from shipping drafts.
    raise SystemExit(0 if result['publish'] else 2)