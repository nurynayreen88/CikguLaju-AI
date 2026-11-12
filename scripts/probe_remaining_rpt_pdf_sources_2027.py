"""RPT 2027 source-format probe in isolated CI; no new PDF release is implied."""
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
sources={
 "english":"RPT_ENGLISH_TAHUN_{y}_2027_UNTUK_GURU.pdf",
 "bahasa_melayu":"RPT_Bahasa_Melayu_Tahun_{y}_2027_DRAF.pdf",
 "matematik":"RPT_Matematik_Tahun_{y}_2027_v28_SEMENTARA.pdf",
 "pendidikan_islam":"RPT_Pendidikan_Islam_Tahun_{y}_2027_CikguLaju.pdf",
}
for subject, pattern in sources.items():
    for y in (2,4,6):
        path=ROOT/f"rpt_2027/{subject}/{pattern.format(y=y)}"
        with fitz.open(path) as pdf:
            print(f"\n=== RPT_PROBE {subject} Tahun {y} pages={pdf.page_count} size={path.stat().st_size} ===")
            for i in sorted(set([0,1,2,pdf.page_count-1])):
                pg=pdf[i]
                text=pg.get_text("text",sort=True).strip()
                if len(text)>4900:text=text[:4900]+"...TRUNCATED..."
                print(f"\n--- page={i+1} {pg.rect.width:.0f}x{pg.rect.height:.0f} chars={len(pg.get_text('text'))} ---\n{text}")

print("\\n=== PDF GRID COORD PROBE ===")
for sub,name,page_num in (
    ("english","RPT_ENGLISH_TAHUN_2_2027_UNTUK_GURU.pdf",1),
    ("matematik","RPT_Matematik_Tahun_2_2027_v28_SEMENTARA.pdf",0),
):
    pdf=fitz.open(ROOT/"rpt_2027"/sub/name)
    pg=pdf[page_num]
    print(f"=== GRID {sub}, page {page_num+1} ===")
    for key in (("LESSON: 1","LESSON: 2","LESSON: 3","LESSON: 4") if sub=="english" else
                ("Lesson 001","Lesson 002","Lesson 003","Lesson 004")):
        print(key, [tuple(round(v,1) for v in rect) for rect in pg.search_for(key)])
    words=pg.get_text("words")
    for word in sorted(words,key=lambda z:(round(z[1]/8)*8,z[0])):
        x0,y0,x1,y1,t,*_=word
        if 66<y0<290 and (y0<145 or t in ("MAIN","COMPLEMENTARY","LESSON:","Lesson","001","002","UNIT","FOCUS:")):
            print(f"XY x={x0:5.1f} y={y0:5.1f} {t!r}")
    pdf.close()

p=fitz.open(ROOT/"rpt_2027/matematik/RPT_Matematik_Tahun_2_2027_v28_SEMENTARA.pdf")
pg=p[0]
print("\\n=== MATH COLUMN GRID ===")
for token in ("LESSON", "UNIT / TAJUK", "SK", "SP", "AKTIVITI PdP", "MINGGU 01","MINGGU 02"):
    print(token, [tuple(round(v,1) for v in r) for r in pg.search_for(token)][:6])
for x0,y0,x1,y1,t,*_ in sorted(pg.get_text("words"),key=lambda x:(round(x[1]/8)*8,x[0])):
    if 210<y0<243:
        print(f"GRID_MATH x={x0:5.1f} y={y0:5.1f} word={t!r}")
p.close()
