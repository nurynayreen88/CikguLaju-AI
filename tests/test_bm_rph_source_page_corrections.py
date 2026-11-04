#!/usr/bin/env python3
"""Regression gate for page-level BM textbook corrections (DRAF only).

Grounding: BM SK Buku Teks Year 4 printed pp 7, 10, 11, 14;
Year 5 pp 26, 28, 42; DSKP BM Year 4/5 from the original PDF.
This checks synchronized RPT Markdown/HTML and RPH and does not
automatically approve any lesson.
"""
from pathlib import Path
import re, json
from html import unescape
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rpt_2027/bahasa_melayu/keluaran_format_english"
RPH=ROOT/"rph_standalone/bahasa_melayu"
CORRECTIONS={
 (4,8):{"sp":"1.1.2","bt":7},
 (4,10):{"sp":"3.2.1","bt":10,"title":"Bina Ayat: Kemudahan di Lapangan Terbang"},
 (4,11):{"sp":"4.2.1","bt":11,"title":"Istimewanya Kita"},
 (4,14):{"sp":"2.3.1","bt":14},
 (4,42):{"sp":"5.1.3","bt":49},
 (4,43):{"sp":"5.1.3","bt":50},
 (4,58):{"sp":"1.1.1","bt":66},
 (4,67):{"sp":"5.1.4","bt":71},
 (4,68):{"sp":"5.1.4","bt":72},
 (4,76):{"sp":"3.3.2","bt":86},
 (4,81):{"sp":"5.2.2","bt":"92–93"},
 (4,92):{"sp":"5.2.2","bt":"105–106"},
 (4,108):{"sp":"1.1.1","bt":121},
 (4,109):{"sp":"2.3.2","bt":122},
 (4,113):{"sp":"2.3.1","bt":127},
 (4,138):{"sp":"1.2.2","bt":159},
 (4,139):{"sp":"2.3.2","bt":161},
 (4,140):{"sp":"3.3.1","bt":162},
 (4,143):{"sp":"1.2.3","bt":165},
 (4,159):{"sp":"5.3.4","bt":"184–185"},
 (4,160):{"sp":"5.1.2","bt":186},
 (5,21):{"sp":"2.1.2","bt":26},
 (5,35):{"sp":"4.3.3","bt":42},
 (5,36):{"sp":"4.3.1","bt":28},
}
for year in (4,5):
    markdown=(SRC/f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.md").read_text(encoding="utf-8")
    html=(SRC/f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.html").read_text(encoding="utf-8")
    for (y,n),req in CORRECTIONS.items():
        if y!=year:continue
        code=f"PdP {n:03d}"
        row=next(x for x in markdown.splitlines() if x.startswith(f"| **{code}** (BM{y}-P{n:03d})"))
        parts=[a.strip() for a in row.strip("|").split("|")]
        assert len(parts)==7,(y,n,len(parts))
        assert parts[4].startswith(req["sp"]+" "), (y,n,"wrong RPT SP",parts[4])
        assert f"BT m/s {req['bt']}" in parts[5],(y,n,"wrong RPT BT",parts[5])
        if "title" in req:assert req["title"]==parts[2],(y,n,"RPT title mismatch")
        key=f'<td class="id">{code}<div class="sub">BM{y}-P{n:03d}</div></td>'
        a=html.index(key);b=html.index("</tr>",a)
        snippet=unescape(html[a:b])
        assert f"{req['sp']} —" in snippet,(y,n,"HTML SP not updated")
        assert f"BT m/s {req['bt']}" in snippet,(y,n,"HTML BT not updated")
        if "title" in req:assert req["title"] in snippet,(y,n,"HTML title not updated")
        file=RPH/f"year{y}/lesson_{n:03d}.md"
        txt=file.read_text(encoding="utf-8")
        assert f"**Standard Pembelajaran (SP):** {req['sp']} —" in txt,(y,n,"RPH SP")
        assert f"BT m/s {req['bt']}" in txt,(y,n,"RPH BT")
        if "title" in req:assert f"**Tajuk aktiviti:** {req['title']}" in txt,(y,n,"RPH title")
        assert all(t in txt for t in ("## Set induksi","## Aktiviti 1","## Aktiviti 2","## Pengukuhan","## Penutup"))
        assert txt.count("**Guru:**")>=5 and txt.count("**Murid:**")>=5
        assert "HOLD_SEMAKAN_SUMBER" in txt and "Bukan READY" in txt
        print("PASS",y,n,req["sp"],f"BT p{req['bt']}")
gate=json.loads((ROOT/"rpt_2027/bahasa_melayu/READY_GATE.json").read_text())
assert gate["status"]=="DRAFT_NOT_PUBLISHED" and gate["verified_strict_ready"] is False
print("All 7 source-aligned RPT/RPH fixes passed; READY remains fail-closed")
