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
    'bidang / tajuk':'title','bidang/tajuk':'title','unit / tajuk':'title',
    'standard kandungan':'standard_content','kandungan pembelajaran':'standard_content',
    'content standard':'standard_content','standard pembelajaran':'standard_learning',
    'learning standard':'standard_learning','objektif':'objectives',
    'objektif pembelajaran':'objectives','learning objectives':'objectives',
    'refleksi':'reflection','reflection':'reflection',
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
    other=[]
    for row in root.findall('.//w:tbl/w:tr',NS):
        cells=[text_of(c) for c in row.findall('w:tc',NS)]
        if len(cells)<2:continue
        label=' '.join(cells[0].lower().strip().rstrip(':').split())
        value='\n'.join(c for c in cells[1:] if c).strip()
        if not value:continue
        target=LABELS.get(label)
        if target:
            fields[target]=(fields[target]+'\n'+value).strip()
        elif any(x in label for x in ('aktiviti','activity','activities','set induksi','penutup','kriteria kejayaan','success criteria','bbm','pak21','emk','pemulihan','pengayaan','penilaian','pentaksiran')):
            other.append((cells[0]+'\n'+value).strip())
        elif not label and other:
            # Continuation of a vertically merged phase label.
            other.append(value)
    fields['activities']='\n\n'.join(other)
    if not fields['objectives'] or not fields['activities']:
        raise ValueError('Susun atur Word belum disokong. Isi secara manual.')
    limits=dict(title=200,standard_content=4000,standard_learning=4000,objectives=4000,activities=12000,reflection=4000)
    if any(len(fields[k])>limit for k,limit in limits.items()):
        raise ValueError('Kandungan melebihi ruang e-RPH. Import tidak dipendekkan.')
    return fields
