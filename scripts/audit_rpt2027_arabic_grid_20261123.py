"""Read-only visual geometry audit for existing Bahasa Arab RPT Year2–6 PDFs.

NO file modification, teacher data, user credits, or publications.
"""
from pathlib import Path
from collections import Counter
import json
import fitz

ROOT=Path("rpt_2027/web_2027_pdfs")
OUT=Path("qa_rpt_arab_grid")
OUT.mkdir(exist_ok=True)
report={}
for y in range(2,7):
    src=ROOT/"bahasa_arab"/f"tahun_{y}.pdf"
    with fitz.open(src) as pdf:
        pages=[]
        for page in pdf:
            paths=page.get_drawings()
            rules=[]
            for p in paths:
                for kind,*rest in p["items"]:
                    if kind == "l":
                        a,b=rest[:2]
                        horizontal=abs(a.y-b.y)<0.7 and abs(a.x-b.x)>10
                        vertical=abs(a.x-b.x)<0.7 and abs(a.y-b.y)>10
                        if horizontal or vertical:
                            rules.append({"k":"h" if horizontal else "v",
                                          "x1":round(a.x,1),"y1":round(a.y,1),
                                          "x2":round(b.x,1),"y2":round(b.y,1),
                                          "color":p.get("color"),"width":p.get("width")})
                    elif kind=="re":
                        r=rest[0]
                        rules.extend([
                            {"k":"rect","x":round(r.x0,1),"y":round(r.y0,1),
                             "w":round(r.width,1),"h":round(r.height,1),
                             "color":p.get("color"),"fill":p.get("fill")}
                        ])
            spans=[]
            for block in page.get_text("dict").get("blocks",[]):
                for line in block.get("lines",[]):
                    for sp in line.get("spans",[]):
                        t=sp["text"].strip()
                        if t:
                            spans.append({"t":t[:55],"b":[round(v,1) for v in sp["bbox"]]})
            pages.append({
                "page":page.number+1,"bounds":list(map(float,page.rect)),
                "rule_counts":dict(Counter(x["k"] for x in rules)),
                "rules":rules[:120],
                "span_count":len(spans),
                "spans":spans[:100],
                "links":len(page.get_links())
            })
            if page.number in (1,2) and y in (2,4,6):
                pix=page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False)
                pix.save(str(OUT/f"arabic_y{y}_page{page.number+1}.png"))
        report[str(y)]={"page_count":len(pdf),"pages":pages[:3],
                        "link_total":sum(len(p.get_links()) for p in pdf)}
(OUT/"geometry.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
for y,item in report.items():
    pg=item["pages"][1]
    print("ARAB_RPT",y,"pages",item["page_count"],"links",item["link_total"],
          "rules",pg["rule_counts"],"rows",pg["span_count"])
print("READ_ONLY_GEOMETRY_AUDIT")
