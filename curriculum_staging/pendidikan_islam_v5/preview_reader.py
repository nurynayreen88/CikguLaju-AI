"""Read 696 draft RPH PDF previews from a separate V5 staging-only ZIP.

No Telegram handler or DB write occurs here. Use in staging previews only.
"""
from __future__ import annotations
import hashlib
import json
import re
import zipfile
from pathlib import Path

class PreviewBundleError(ValueError):
    pass

class PIPreviewBundleV5:
    def __init__(self, archive_path: str | Path, *, staging: bool = False):
        if staging is not True:
            raise PermissionError('Draft PDF previews require staging=True')
        self.path=Path(archive_path).resolve(strict=True)
        with zipfile.ZipFile(self.path) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or z.testzip() is not None:
                raise PreviewBundleError('Bad/duplicate ZIP entries')
            try:
                manifest=json.loads(z.read('KATALOG/preview_manifest.json'))
                records=json.loads(z.read('KATALOG/preview_catalog.json'))
            except (KeyError,ValueError) as exc:
                raise PreviewBundleError('Missing or invalid PDF preview manifest') from exc
            if manifest.get('status')!='STAGING_ONLY_NOT_PUBLISHED' or manifest.get('pdf_total')!=696 or len(records)!=696:
                raise PreviewBundleError('Unexpected preview release state/count')
            index={}
            for r in records:
                y,l=r.get('tahun'),r.get('lesson')
                if type(y) is not int or y not in range(2,7) or type(l) is not int or not (1<=l<=200):
                    raise PreviewBundleError('Invalid year/lesson')
                if r.get('lesson_id')!=f'T{y}-L{l:03d}' or (y,l) in index:
                    raise PreviewBundleError('Duplicate or invalid lesson identity')
                p=r.get('pdf_path','')
                if not isinstance(p,str) or not re.fullmatch(rf'RPH_PRATONTON/Tahun_{y}/PI_T{y}_LESSON_{l:03d}_RPH_PRATONTON_STAGING\.pdf',p) or p not in names:
                    raise PreviewBundleError('Unexpected PDF preview path')
                sha=r.get('pdf_sha256','')
                if not isinstance(sha,str) or re.fullmatch(r'[0-9a-f]{64}',sha) is None:
                    raise PreviewBundleError('Missing PDF SHA')
                if r.get('publish')!='STAGING_ONLY' or r.get('pages')!=1 or r.get('paper')!='A4':
                    raise PreviewBundleError('Unexpected approval or format')
                index[y,l]=r
            if len(index)!=696:
                raise PreviewBundleError('Incomplete PDF preview catalog')
            self._index=index

    def read_preview_pdf(self, year: int, lesson: int, *, allow_teacher_draft: bool = False) -> bytes:
        if allow_teacher_draft is not True:
            raise PermissionError('Draft preview cannot be served as published RPH')
        record=self._index[year,lesson]
        with zipfile.ZipFile(self.path) as z:
            data=z.read(record['pdf_path'])
        if not data.startswith(b'%PDF-') or hashlib.sha256(data).hexdigest()!=record['pdf_sha256']:
            raise PreviewBundleError('PDF corruption or checksum mismatch')
        return data

    def get_record(self, year: int, lesson: int):
        return dict(self._index[year,lesson])