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
