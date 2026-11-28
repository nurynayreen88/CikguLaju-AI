"""Bounded, text-only import of a teacher-supplied DOCX. Never generate source RPH."""
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET
import re

MAX_FILE = 2_000_000
MAX_XML = 2_000_000
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'
LABELS = {
    'tajuk':'title','tema / tajuk':'title','tema/tajuk':'title',
    'bidang / tajuk':'title','bidang/tajuk':'title','unit / tajuk':'title','kandungan / tajuk':'title','kandungan/tajuk':'title',
    'standard kandungan':'standard_content','standard kandungan (sk)':'standard_content','kandungan pembelajaran':'standard_content',
    'content standard':'standard_content','standard pembelajaran':'standard_learning','standard pembelajaran (sp)':'standard_learning',
    'learning standard':'standard_learning','objektif':'objectives',
    'objektif pembelajaran':'objectives','learning objectives':'objectives','learning objective':'objectives',
    'theme / topic':'title','theme/topic':'title','topic':'title',
    'refleksi':'reflection','refleksi (auto / manual)':'reflection','refleksi (auto/manual)':'reflection','reflection':'reflection',
}
def text_of(cell):
    paras=[]
    for p in cell.findall('.//w:p',NS):
        line=''.join(n.text or '' if n.tag==W+'t' else '\n' if n.tag==W+'br' else '\t' if n.tag==W+'tab' else '' for n in p.iter())
        if line.strip():paras.append(line.strip())
    return '\n'.join(paras)

def extract_docx(raw):
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_FILE:
        raise ValueError('Saiz Word tidak sah.')
    try:
        with ZipFile(BytesIO(raw)) as z:
            matches=[x for x in z.infolist() if x.filename=='word/document.xml']
            if len(matches)!=1 or matches[0].file_size>MAX_XML or len(z.infolist())>250:
                raise ValueError('Struktur Word tidak disokong.')
            with z.open(matches[0]) as src:xml=src.read(MAX_XML+1)
        if len(xml)>MAX_XML or re.search(br'<!\s*(?:DOCTYPE|ENTITY)',xml,re.I) or b'\x00' in xml:
            raise ValueError('XML tidak disokong.')
        root=ET.fromstring(xml)
    except (BadZipFile,ET.ParseError,RuntimeError,KeyError,OSError) as exc:
        raise ValueError('Fail Word tidak dapat dibaca.') from exc
    fields={key:'' for key in ('title','standard_content','standard_learning','objectives','activities','reflection')}
    # The module's own single-record Word export is paragraph based. Import
    # its six content sections only, never infer slot or entitlement.
    body=root.find('w:body',NS)
    if body is None:
        raise ValueError('Struktur Word tidak disokong.')
    paragraphs=[text_of(p) if p.tag!=W+'p' else ''.join(
        n.text or '' if n.tag==W+'t' else '\n' if n.tag==W+'br' else '\t' if n.tag==W+'tab' else ''
        for n in p.iter()) for p in body.findall('w:p',NS)]
    if paragraphs and paragraphs[0]=='REKOD e-RPH':
        if body.findall('w:tbl',NS) or paragraphs.count('REKOD e-RPH')!=1:
            raise ValueError('Import satu rekod e-RPH sahaja pada satu masa.')
        labels=('Tajuk','Standard Kandungan / Kandungan Pembelajaran',
                'Standard Pembelajaran','Objektif Pembelajaran','Aktiviti PdP','Refleksi')
        keys=('title','standard_content','standard_learning','objectives','activities','reflection')
        # Export contract: title, subject, slot metadata, status metadata,
        # followed by exactly six label/value pairs. No heuristic splitting.
        if len(paragraphs)!=16 or tuple(paragraphs[4::2])!=labels:
            raise ValueError('Susun atur eksport e-RPH telah berubah. Isi secara manual.')
        fields.update(zip(keys,paragraphs[5::2]))
        return checked_fields(fields)
    other=[]
    phase=False
    for row in root.findall('.//w:tbl/w:tr',NS):
        cells=[text_of(c) for c in row.findall('w:tc',NS)]
        if len(cells)<2:continue
        label=' '.join(cells[0].lower().strip().rstrip(':').split())
        value='\n'.join(c for c in cells[1:] if c).strip()
        # Some premium source tables embed the title in the teacher-information header.
        if ('maklumat pdp' in value.casefold() or 'kelas:' in value.casefold() or 'class:' in value.casefold()) and not fields['title']:
            match=re.search(r'(?im)^(?:tajuk|topic)\s*:\s*(.+)$',cells[0])
            if match:fields['title']=match.group(1).strip()
            continue
        if ('kelas:' in label or 'class:' in label) and ('tarikh:' in label or 'date:' in label):
            # Standard header: teacher fields left, subject/title right.
            if not fields['title']:
                match=re.search(r'(?im)^(?:tajuk|topic)\s*:\s*(.+)$',value)
                if match:fields['title']=match.group(1).strip()
            continue
        if not value:continue
        target=LABELS.get(label)
        if target:
            if target=='title':
                value=re.sub(r'(?im)^(?:tajuk|topic)\s*:\s*','',value)
                # Never treat internal scheduling labels or a QA marker as the title.
                value='\n'.join(line for line in value.splitlines() if not re.match(r'(?i)^\s*(?:RPT Kumpulan|Kumpulan [AB]\b|Lesson\s+\d|PdP\s+\d|Draf QA\b)',line)).strip()
            fields[target]=value if target=='title' and label in ('kandungan / tajuk','kandungan/tajuk') else (fields[target]+'\n'+value).strip()
            phase=False
        elif any(x in label for x in ('aktiviti','activity','activities','set induksi','penutup','kriteria kejayaan','success criteria','bbm','pak21','emk','pemulihan','pengayaan','penilaian','pentaksiran','pengukuhan','pbd','bahan','teaching aids','closure','remedial','enrichment','assessment','values','induction','evaluation')):
            other.append((cells[0]+'\n'+value).strip())
            phase=('aktiviti' in label or 'activities' in label)
        elif not label and phase:
            # Continuation of a vertically merged activity / 5P phase label.
            other.append(value)
        else:
            # Fail closed on unknown populated rows. Do not silently drop content.
            raise ValueError('Susun atur Word belum disokong sepenuhnya. Isi secara manual.')
    fields['activities']='\n\n'.join(other)
    return checked_fields(fields)

def checked_fields(fields):
    if not all(fields[k] for k in ('title','standard_learning','objectives','activities')):
        raise ValueError('Susun atur Word belum disokong. Isi secara manual.')
    limits=dict(title=200,standard_content=4000,standard_learning=4000,objectives=4000,activities=12000,reflection=4000)
    if any(len(fields[k])>limit for k,limit in limits.items()):
        raise ValueError('Kandungan melebihi ruang e-RPH. Import tidak dipendekkan.')
    return fields
