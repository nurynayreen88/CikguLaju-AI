"""Render a PARTIAL app.py Jawi Flowable smoke sample (not production-equivalent)."""
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
assert len(classes)>=2, "Expected multiple Jawi renderer overrides"
print(f"PARTIAL SMOKE ONLY: exercising 2 of {len(classes)} renderer class definitions; not a production-equivalent PDF")
# This is a limited visual smoke test only; the separate chain audit checks
# all definitions. Never label this test production-equivalent.
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
    raw=str(text).replace("<br/>","\
").replace("<br>","\
")
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
print("Created PARTIAL smoke",out,"bytes",out.stat().st_size,"embedded images",len(pdf[0].get_image_info()))

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

# Exercise every inherited renderer constructor in source order, rather than
# only the first and last versions. Helpers below remain isolated substitutes;
# this is a full CLASS-chain smoke, NOT a production-runtime integration test.
def clean_text(value):
    return plain(value)[0]
def compat_text(value, _path):
    return str(value)
chain_scope={
    "Flowable": Flowable, "re": re,
    "_jawi_font_path_v25213": lambda bold=False: font_path("",bold),
    "_repair_jawi_text_v25224": clean_text,
    "_trace_and_repair_jawi_v25225": clean_text,
    "_font_supports_v25224": lambda path,ch: ord(ch) in font_cmap(path),
    "_best_jawi_font_v25226": font_path,
    "_font_cmap_v25226": font_cmap,
    "_pi_clean_tofu_v2598": clean_text,
    "_pi_jawi_font_v2598": lambda bold=False: font_path("",bold),
    "_pi_clean_text_v2599": clean_text,
    "_pi_term_cleanup_v2601": lambda t: str(t),
    "_pi_safe_unicode_v2602": lambda t: str(t),
    "_pi_runtime_glyph_compat_v2603": compat_text,
    "_pi_exact_jawi_font_v2604": font_path,
    "_pi_markup_to_plain_v2605": plain,
    "_pi_jawi_font_v2606": font_path,
}
count=0
for node in tree.body:
    if isinstance(node,ast.Assign) and isinstance(node.value,ast.Name) and node.value.id=="_JawiRasterParagraph_v25213" and any(isinstance(t,ast.Name) and t.id.startswith("_JawiRasterParagraph_") for t in node.targets):
        if "_JawiRasterParagraph_v25213" in chain_scope:
            exec(compile(ast.Module(body=[node],type_ignores=[]),"<renderer-alias>","exec"),chain_scope)
    elif isinstance(node,ast.ClassDef) and node.name=="_JawiRasterParagraph_v25213":
        exec(compile(ast.Module(body=[node],type_ignores=[]),"<renderer-chain>","exec"),chain_scope)
        count+=1
assert count==len(classes)==12, f"Unexpected Jawi renderer class count: {count}"
FullChainRenderer=chain_scope["_JawiRasterParagraph_v25213"]
assert len([c for c in FullChainRenderer.__mro__ if c.__name__=="_JawiRasterParagraph_v25213"])==12
full_pdf=Path("jawi_renderer_full_class_chain_smoke.pdf")
full_rows=[[FullChainRenderer("<b>"+samples[0]+"</b>",style)]]+[[FullChainRenderer(t,style)] for t in samples[1:]]
full_table=Table(full_rows,colWidths=[470])
full_table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey)]))
SimpleDocTemplate(str(full_pdf),pagesize=(595.28,841.89)).build([full_table])
full_doc=fitz.open(full_pdf)
assert len(full_doc)==1 and len(full_doc[0].get_image_info())>=4
print("FULL 12-CLASS CHAIN smoke with SUBSTITUTE HELPERS",full_pdf,full_pdf.stat().st_size)

# Full renderer class chain with actual v26.39 resolver body, using
# controlled dependencies for font discovery and text cleanup.
def effective_font(text,bold=False):
    return font_path(text,bold)
# Use the real final v26.39 function body with deterministic installed-font
# dependencies. This tests its production control flow in the 12-class chain.
resolver_nodes=[node for node in tree.body
                if isinstance(node,ast.FunctionDef)
                and node.name=="_pi_exact_jawi_font_v2604"]
assert len(resolver_nodes)>=2
chain_scope["_pi2639_exact_font"]=lambda text,bold=False:font_path(text,bold)
chain_scope["_pi2638_best_nonfatal_font"]=lambda text,bold=False:font_path(text,bold)
chain_scope["_pi2637_required_cps"]=lambda text:{
    ord(ch) for ch in str(text) if 0x0600<=ord(ch)<=0x08FF
}
chain_scope["_pi2639_prev_exact"]=effective_font
exec(compile(ast.Module(body=[resolver_nodes[-1]],type_ignores=[]),
             "<real-v2639-resolver>","exec"),chain_scope)
# Record calls to the actual resolver while rendering the full chain.
actual_resolver=chain_scope["_pi_exact_jawi_font_v2604"]
resolver_calls=[]
def observed_resolver(text,bold=False):
    resolver_calls.append((str(text),bool(bold)))
    return actual_resolver(text,bold)
chain_scope["_pi_jawi_font_v2606"]=observed_resolver
# Preserve the extracted production resolver; never overwrite it with the substitute.
assert chain_scope["_pi_exact_jawi_font_v2604"] is actual_resolver
production_font_pdf=Path("jawi_renderer_12class_v2639_resolver_smoke.pdf")
real_rows=[[FullChainRenderer("<b>"+samples[0]+"</b>",style)]]+[[FullChainRenderer(t,style)] for t in samples[1:]]
real_table=Table(real_rows,colWidths=[470])
real_table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey)]))
SimpleDocTemplate(str(production_font_pdf),pagesize=(595.28,841.89)).build([real_table])
real_doc=fitz.open(production_font_pdf)
assert len(real_doc)==1 and len(real_doc[0].get_image_info())>=4
assert len(resolver_calls)>=len(samples), f"Expected real resolver for each sample, got {len(resolver_calls)}"
print("12-CLASS CHAIN + real v26.39 resolver body (controlled font dependencies)",production_font_pdf)


# Representative full RPH layout using the 12-class chain and the actual
# v26.39 resolver body. Synthetic content: NOT an approved curriculum RPH.
rph_sections=[
    ("معلومت ڤڠاجرن", "ڤنديديقن اسلام | تاهون ٢ | ٦٠ مينيت"),
    ("ستندرد کاندوڠن", "ممباچ دان ممهامي ڤرکاتاءن جاوي"),
    ("ستندرد ڤمبلاجرن", "موريد ممباچ دان منوليس ڤرکاتاءن جاوي"),
    ("اوبيکتيف ڤمبلاجرن", "موريد داڤت ممباچ دان منوليس تيݢ ڤرکاتاءن"),
    ("ست ايندوکسي", "ݢورو منونجوقکن کد ڤرکاتاءن. موريد ممريهاتي دان منجاوب سوالن."),
    ("اکتيۏيتي ١", "ݢورو ممباچ ڤرکاتاءن دان موريد مڠيکوت سبوتن. موريد منونجوقکن حروف."),
    ("اکتيۏيتي ٢", "موريد مميليه کد ڤرکاتاءن دان ممادنکن دڠن ݢمبر. ݢورو ممبري بيمبيڠن."),
    ("اکتيۏيتي ٣", "موريد منوليس ڤرکاتاءن جاوي دالم بوکو. ݢورو ممريکسا توليسن."),
    ("اکتيۏيتي ٤", "موريد ممباچ سمولا ڤرکاتاءن دهادڤن راکن. راکن ممبري مقلوم بالس."),
    ("ڤنتکسيرن", "ݢورو منيلاي باچاءن دان توليسن موريد برساسرکن سناراي سماق."),
    ("ڤنوتوڤ", "موريد مڽاتاکن ڤرکاتاءن يڠ دڤلاجري. ݢورو مروبوموسکن ڤمبلاجرن."),
]
rph_style=ParagraphStyle("full-rph-jawi",fontSize=9.5,leading=13)
full_rph_pdf=Path("jawi_renderer_12class_v2639_full_rph_layout.pdf")
rph_rows=[[FullChainRenderer(label,rph_style),FullChainRenderer(value,rph_style)]
          for label,value in rph_sections]
rph_table=Table(rph_rows,colWidths=[125,345],hAlign="CENTER")
rph_table.setStyle(TableStyle([
    ("GRID",(0,0),(-1,-1),0.5,colors.grey),
    ("VALIGN",(0,0),(-1,-1),"TOP"),
    ("LEFTPADDING",(0,0),(-1,-1),6),
    ("RIGHTPADDING",(0,0),(-1,-1),6),
    ("TOPPADDING",(0,0),(-1,-1),4),
    ("BOTTOMPADDING",(0,0),(-1,-1),4),
]))
before=len(resolver_calls)
SimpleDocTemplate(str(full_rph_pdf),pagesize=A4,topMargin=28,bottomMargin=28).build([rph_table])
full_rph_doc=fitz.open(full_rph_pdf)
assert len(full_rph_doc)==1, "Full RPH layout must fit one A4 page"
assert len(resolver_calls)-before>=len(rph_sections), (\n    f"Expected at least {len(rph_sections)} actual resolver calls in full RPH; "\n    f"observed {len(resolver_calls)-before}"\n)
full_rph_images=full_rph_doc[0].get_image_info()
assert len(full_rph_images)>=2*len(rph_sections)
assert all(0<=i["bbox"][0]<i["bbox"][2]<=full_rph_doc[0].rect.width for i in full_rph_images)
assert all(0<=i["bbox"][1]<i["bbox"][3]<=full_rph_doc[0].rect.height for i in full_rph_images)
print("Full RPH synthetic layout with v26.39 resolver",full_rph_pdf,"images",len(full_rph_images))
