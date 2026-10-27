"""Render an actual app.py Jawi Flowable in isolation (no bot/DB import)."""
import ast
from pathlib import Path
import re
import html
from types import SimpleNamespace
from fontTools.ttLib import TTFont
from reportlab.platypus import Flowable, SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from PIL import ImageFont

source=Path("app.py").read_text(encoding="utf-8")
tree=ast.parse(source)
classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="_JawiRasterParagraph_v25213"]
assert len(classes)>=2, "Expected base and final Jawi renderer"
base=classes[0]
final=classes[-1]
def font_cmap(path):
    ft=TTFont(path)
    try: return {cp for t in ft["cmap"].tables if t.isUnicode() for cp in t.cmap}
    finally: ft.close()
def font_path(text,bold=False):
    candidates=[
        "/usr/share/fonts/truetype/noto/NotoSansArabic-"+("Bold" if bold else "Regular")+".ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-"+("Bold" if bold else "Regular")+".ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabicUI-"+("Bold" if bold else "Regular")+".ttf",
        "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-"+("Bold" if bold else "Regular")+".ttf",
    ]
    need={ord(c) for c in text if c.isprintable() and not c.isspace()}
    for p in candidates:
        if Path(p).is_file() and need.issubset(font_cmap(p)): return p
    raise RuntimeError("No installed font covers the complete smoke sample; checked: "+str([(p,Path(p).is_file()) for p in candidates]))
def plain(text):
    raw=str(text).replace("<br/>","\\n").replace("<br>","\\n")
    return html.unescape(re.sub(r"<[^>]+>","",raw)),bool(re.fullmatch(r"\\s*<b>.*</b>\\s*",raw,re.S))
scope={"Flowable":Flowable,"_pi_markup_to_plain_v2605":plain,"_pi_jawi_font_v2606":font_path,"_font_cmap_v25226":font_cmap}
exec(compile(ast.Module(body=[base],type_ignores=[]),"<app-base>","exec"),scope)
scope["_JawiRasterParagraph_v2606_stable"]=scope["_JawiRasterParagraph_v25213"]
exec(compile(ast.Module(body=[final],type_ignores=[]),"<app-final>","exec"),scope)
Renderer=scope["_JawiRasterParagraph_v25213"]
assert ImageFont.core.HAVE_RAQM
style=ParagraphStyle("jawi",fontSize=10,leading=14)
samples=[
    "اکتيۏيتي 1 – ممباچ",
    "ݢورو ممباچ دان موريد منوليس.",
    "موريد ممباچ ڤرکاتاءن جاوي.",
    "Jawi 2027: ڤنديديقن اسلام",
]
out=Path("jawi_renderer_actual_flowable_smoke.pdf")
doc=SimpleDocTemplate(str(out),pagesize=(595.28,841.89))
rows=[[Renderer("<b>"+samples[0]+"</b>",style)]]+[[Renderer(t,style)] for t in samples[1:]]
table=Table(rows,colWidths=[470])
table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8)]))
doc.build([table])
import fitz
pdf=fitz.open(out)
assert len(pdf)==1
assert len(pdf[0].get_image_info())>=4
print("Created",out,"bytes",out.stat().st_size,"embedded images",len(pdf[0].get_image_info()))
