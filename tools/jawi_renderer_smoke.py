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
# The final class may inherit through multiple prior patches. Never claim this\n# smoke test validates the live renderer unless the complete class chain is used.\nassert len(classes)==2, (\n    f"Renderer has {len(classes)} definitions: isolated base/final test is NOT production-equivalent. "\n    "Build a complete patch-chain harness before accepting a PDF."\n)
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

# Representative A4 RPH table stress test: same renderer in narrow columns,
# with repeated activity text. This is not a DB-backed production RPH.
from reportlab.platypus import KeepTogether
from reportlab.lib.pagesizes import A4
rph=Path("jawi_renderer_a4_table_stress.pdf")
head=ParagraphStyle("jawi-heading",fontSize=10,leading=14)
body=ParagraphStyle("jawi-body",fontSize=9.5,leading=13)
long_activity=("ݢورو ممباچ دان موريد منوليس. موريد ممباچ ڤرکاتاءن جاوي. "*4).strip()
sections=[
    ("معلومت ڤڠاجرن", "ڤنديديقن اسلام"),
    ("ست ايندوکسي", "ݢورو ممباچ دان موريد مندڠر."),
    ("اکتيۏيتي 1", long_activity),
    ("اکتيۏيتي 2", long_activity),
    ("اکتيۏيتي 3", long_activity),
    ("ڤنتکسيرن", "موريد ممباچ ڤرکاتاءن جاوي."),
    ("ڤنوتوڤ", "ݢورو دان موريد مرو موسکن ڤمبلاجرن."),
]
rows=[[Renderer(a,head),Renderer(b,body)] for a,b in sections]
t=Table(rows,colWidths=[120,350],repeatRows=0,hAlign="CENTER")
t.setStyle(TableStyle([
    ("GRID",(0,0),(-1,-1),0.5,colors.grey),
    ("VALIGN",(0,0),(-1,-1),"TOP"),
    ("LEFTPADDING",(0,0),(-1,-1),7),
    ("RIGHTPADDING",(0,0),(-1,-1),7),
    ("TOPPADDING",(0,0),(-1,-1),5),
    ("BOTTOMPADDING",(0,0),(-1,-1),5),
]))
SimpleDocTemplate(str(rph),pagesize=A4,topMargin=32,bottomMargin=32).build([t])
pdf=fitz.open(rph)
assert len(pdf)==1, f"A4 RPH table overflowed to {len(pdf)} pages"
images=pdf[0].get_image_info()
assert len(images)>=14
assert all(i["bbox"][0]>=0 and i["bbox"][2]<=pdf[0].rect.width for i in images)
assert all(i["bbox"][1]>=0 and i["bbox"][3]<=pdf[0].rect.height for i in images)
print("Created",rph,"pages",len(pdf),"images",len(images))
