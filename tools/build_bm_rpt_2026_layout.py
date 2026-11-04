#!/usr/bin/env python3
"""Bina lima RPT BM 2027 ala jadual RPT BM SK 2026. Format sahaja, kandungan asal kekal."""
from pathlib import Path
from html import escape as e
import re,json
from bs4 import BeautifulSoup as Soup
from weasyprint import HTML
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'rpt_2027/bahasa_melayu/keluaran_format_english'
OUT=ROOT/'rpt_2027/bahasa_melayu'
COUNTS={2:164,3:165,4:165,5:166,6:165}
STYLE='''@page{size:A4 landscape;margin:13mm 11mm 15mm 11mm;
@top-right{content:"RPT BAHASA MELAYU (SK) TAHUN YR | 2027";font:8pt "DejaVu Sans";color:#405569}
@bottom-left{content:"CIKGULAJU AI • DRAF SEMAKAN";font:7pt "DejaVu Sans";color:#566b7d}
@bottom-right{content:"Halaman " counter(page) " / " counter(pages);font:7pt "DejaVu Sans";color:#566b7d}}
body{font:8pt/1.32 "DejaVu Sans",Arial,sans-serif;color:#1d2834;margin:0}
h1{text-align:center;font-size:15pt;margin:0 0 3px}h2{text-align:center;font-size:10pt;margin:0 0 7px}
.info{border:1px solid #8b9eae;background:#f4f8fa;padding:7px 9px;margin-bottom:7px;line-height:1.6}
.status{color:#76551a;font-weight:bold;font-size:7.5pt}
table{border-collapse:collapse;table-layout:fixed;width:100%;margin:0 0 7px}
col.a{width:11%}col.b{width:19%}col.c{width:19%}col.d{width:26%}col.f{width:25%}
th{background:#bed6eb;font-size:8pt;text-align:center;padding:6px 4px;border:1px solid #4a5a68;line-height:1.2}
td{border:1px solid #4a5a68;font-size:7.5pt;line-height:1.42;vertical-align:top;padding:5px 6px;overflow-wrap:anywhere}
tr{break-inside:avoid}
.week{background:#eaf1e3;vertical-align:middle;text-align:center;font-size:7.4pt;line-height:1.6}
.wn{display:block;font-weight:bold;font-size:13pt;margin-bottom:7px}
.date{display:block;margin-top:7px}.theme{line-height:1.6}
.ref-title{font-size:7.85pt;font-weight:bold;margin-bottom:5px}.pd{color:#244b69}.code{font-size:6.5pt;color:#677786;font-weight:normal}
.refs{font-size:7.25pt;font-weight:600;display:block;margin-top:4px}.detail{color:#53606c;font-size:7.05pt;display:block;margin-top:4px}
.pkjr td:not(.week){background:#fff2ca}.unallocated td:not(.week){background:#f4f6f8;color:#657381}
.foot{font-size:7.2pt;color:#687785;margin-top:9px}'''

def build(year,total):
    path=SRC/f'RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.html'
    soup=Soup(path.read_text(encoding='utf-8'),'html.parser')
    weeks=soup.select('section.week')
    assert len(weeks)==44,(year,len(weeks))
    html=[f'''<!doctype html><html lang="ms"><head><meta charset="utf-8"><title>RPT BM Tahun {year} 2027 DRAF - gaya RPT 2026</title><style>{STYLE.replace('YR',str(year))}</style></head><body>
<h1>RANCANGAN PENGAJARAN TAHUNAN 2027</h1><h2>BAHASA MELAYU (SK) · TAHUN {year} · KSSR SEMAKAN</h2>
<div class="info"><b>SEKOLAH</b>: _____________________ &nbsp; <b>GURU</b>: _____________________ &nbsp; <b>KELAS</b>: ________<br>
<b>KUMPULAN A + B</b> &nbsp; | &nbsp; 44 minggu &nbsp; | &nbsp; {total} PdP &nbsp; | &nbsp; Format jadual RPT BM SK 2026<br>
<span class="status">DRAF UNTUK SEMAKAN: cuti negeri/gantian, SK/SP, aktiviti dan BT/BA masih memerlukan pengesahan menyeluruh.</span></div>''']
    seen=[]
    for ix,section in enumerate(weeks,1):
        title=section.select_one('.weektitle').get_text(' ',strip=True)
        parts=[s.strip() for s in title.split('|')]
        assert len(parts)>=3 and re.search(r'M(\d\d)',parts[0]),(year,title)
        w=int(re.search(r'M(\d\d)',parts[0]).group(1))
        assert w==ix,(year,w,ix)
        rows=section.select('tbody > tr')
        assert rows,(year,w)
        weekcell=f'<td class="week" rowspan="{len(rows)}"><span class="wn">{w:02d}</span><span class="date">{e(parts[1])}</span><span class="date">{e(parts[2])}</span></td>'
        html.append('<table><colgroup><col class="a"><col class="b"><col class="c"><col class="d"><col class="f"></colgroup><thead><tr><th>MINGGU</th><th>TEMA / UNIT</th><th>STANDARD<br>KANDUNGAN</th><th>STANDARD<br>PEMBELAJARAN</th><th>CATATAN /<br>RUJUKAN</th></tr></thead><tbody>')
        for j,row in enumerate(rows):
            cells=row.find_all('td',recursive=False)
            lead=weekcell if j==0 else ''
            idtag=row.select_one('td.id')
            if idtag is None:
                line=' '.join(c.get_text(' ',strip=True) for c in cells)
                html.append(f'<tr class="unallocated">{lead}<td colspan="4">{e(line)}</td></tr>')
                continue
            assert len(cells)==7,(year,w,len(cells))
            vals=[c.get_text(' ',strip=True) for c in cells]
            m=re.search(r'PdP\s+(\d{3})',vals[0]);assert m,(year,w,vals[0])
            n=int(m.group(1));seen.append(n)
            _,theme,topic,sk,sp,refs,notes=vals
            theme_html=e(theme).replace('; ',';<br>')
            id_suffix=e(vals[0].replace(f'PdP {n:03d}','').strip())
            end=(f'<div class="ref-title"><span class="pd">PdP {n:03d}</span> · {e(topic)} <span class="code">{id_suffix}</span></div>'
                 f'<span class="refs">{e(refs)}</span><span class="detail">{e(notes)}</span>')
            special=' class="pkjr"' if re.search(r'\bPKJR\b',topic+' '+notes,re.I) else ''
            html.append(f'<tr{special}>{lead}<td class="theme">{theme_html}</td><td>{e(sk)}</td><td>{e(sp)}</td><td>{end}</td></tr>')
        html.append('</tbody></table>')
    assert seen==list(range(1,total+1)),(year,seen[:10],seen[-10:],len(seen))
    html.append('<p class="foot">Rujukan: RPT BM SK 2026, DSKP dan Kalendar Induk 2027. Status DRAF — tidak menandakan kelulusan READY.</p></body></html>')
    combined='\n'.join(html)
    (OUT/f'RPT_BM_Tahun_{year}_2027_Format_2026_DRAF.html').write_text(combined,encoding='utf-8')
    target=OUT/f'RPT_Bahasa_Melayu_Tahun_{year}_2027_DRAF.pdf'
    HTML(string=combined,base_url=str(SRC)).write_pdf(str(target))
    pdf=PdfReader(str(target))
    assert all(float(p.mediabox.width)>float(p.mediabox.height) for p in pdf.pages),(year,'not landscape')
    ids={int(v) for v in re.findall(r'\bPdP\s+(\d{3})\b','\n'.join(p.extract_text() or '' for p in pdf.pages))}
    assert ids==set(range(1,total+1)),(year,sorted(set(range(1,total+1))-ids))
    result=dict(year=year,pdp=total,weeks=44,pages=len(pdf.pages),bytes=target.stat().st_size,
                status='DRAF_BELUM_READY',layout='RPT BM SK 2026 five-column style',filename=target.name)
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    results=[build(y,n) for y,n in COUNTS.items()]
    assert sum(x['pdp'] for x in results)==825
    (OUT/'PDF_DRAF_MANIFEST_2027.json').write_text(json.dumps(dict(subject='Bahasa Melayu SK',year=2027,ready=False,records=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
