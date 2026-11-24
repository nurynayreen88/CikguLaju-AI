"""Offline-only SJKC Science RPH preparation. The existing RPT is immutable.
All output is QA, not a production route. Never infer official SP wording.
"""
from pathlib import Path
import json
import argparse
import hashlib
from io import BytesIO

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"rph_standalone/sjkc/sains"
COUNTS={2:48,3:48,4:64,5:64,6:64}
SOURCE_KEYS=("pdp","theme","unit_number","unit","topic","sk","sp","textbook_pages","focus")
# Supplemental evidence targets from the targeted DSKP review (24 Nov).
# Original RPT focus stays intact in every record.
TARGETED_ADDENDA={
    (3,40):"根据教材描述比较味觉和触觉特征，并以试纸证据判断；不品尝、不触摸未知样品，不记录未进行的感官测试。",
    (4,31):"指出光合作用产生的氧气及储存的淀粉，并解释植物制造的糖可转化为淀粉。",
    (4,53):"以安全材料制作一个简单物品并测试其用途，说明所选材料的性质及理由。",
    (4,56):"解释地心引力使地面物体保持在其位置，并用示意图表示其方向。",
    (5,43):"依据教师示范资料说明受热及散热时温度升降和材料膨胀收缩的变化。",
    (5,45):"辨认生锈物品的表面特征，并根据资料归纳铁制品会生锈。",
    (5,57):"根据农历资料排列完整月相周期，并用图示或口述表达观察结果。",
    (6,14):"根据教师提供的显微影片或观察记录辨认微生物的移动等生命活动；不培养未知微生物。",
    (6,26):"评价保护与复育措施对指定濒危物种的作用，并说明依据。",
    (6,30):"在同一表面用安全轻质模型比较不同质量的影响，并在另一组测试中保持质量相同以比较表面。",
    (6,42):"在教师监督下开展同一种食物的多种保存方法小课题，根据真实记录作总结；不食用实验样品。",
    (6,53):"预测日食及月食期间地球上的可观察情况，并以模型解释；禁止肉眼直视太阳。",
}

def load(path):return json.loads(path.read_text(encoding="utf-8"))
def source(year):
    r=load(ROOT/f"rpt_2027/sjkc/sains/year_{year}_kuala_lumpur.json")
    assert (r["year"],r["school_type"],r["subject"])==(year,"SJKC","Sains")
    assert [x["pdp"] for x in r["lessons"]]==list(range(1,COUNTS[year]+1))
    return r["lessons"]
def records(year):
    originals=source(year)
    if year==2:
        plans=[]
        for part in ("001_024","025_048"):
            plans+=load(DATA/f"year2_candidates_{part}_20261124.json")["records"]
        descriptions=load(DATA/"year2_standards_20261124.json")
        assert len(descriptions["sk"])==12 and len(descriptions["sp"])==64
        for original,r in zip(originals,plans,strict=True):
            assert all(r[k]==original[k] for k in SOURCE_KEYS) and not r["ready"]
            yield dict(r,year=year,sk_display=[k+" "+descriptions["sk"][k] for k in r["sk"]],
                       sp_display=[k+" "+descriptions["sp"][k]["description"] for k in r["sp"]],
                       standard_status="EDITORIAL_PARAPHRASE_PENDING_VERBATIM_CHECK")
        return
    bank=load(DATA/f"year{year}_activity_bank_20261124.json")
    assert bank["status"]=="QA_NOT_PUBLISHED" and bank["year"]==year
    descriptions=load(DATA/f"year{year}_standards_20261124.json")
    assert descriptions["status"]=="EDITORIAL_LABELS_QA_ONLY" and descriptions["year"]==year
    assert descriptions["source_git_blob"]==bank["source_git_blob"]
    assert set(descriptions["sk"])=={k for r in originals for k in r["sk"]}
    assert set(descriptions["sp"])=={k for r in originals for k in r["sp"]}
    assert all(v.strip() for v in descriptions["sk"].values())
    assert all(v["description"].strip() for v in descriptions["sp"].values())
    for original,b in zip(originals,bank["records"],strict=True):
        assert all(b[k]==original[k] for k in ("pdp","unit_number","topic"))
        assert b["source_focus"]==original["focus"] and not b["ready"]
        r={k:original[k] for k in SOURCE_KEYS}
        focus=r["focus"]
        extra=TARGETED_ADDENDA.get((year,r["pdp"]),"")
        focus=focus+(" "+extra if extra else "")
        # Retain the exact topic-specific source focus; only add scaffolding.
        r.update(year=year,ready=False,bbm=b["materials"],
          objective="完成以下学习任务："+focus,
          criteria=focus,
          induction="教师展示本课教具或图示，请学生根据观察提出一个问题。",
          activities=[
            {"title":"活动一：示范与引导","body":"教师引导学生"+b["teacher_guidance"]+"。"},
            {"title":"活动二：探究与实践","body":"学生在教师监督下完成本课任务："+focus},
            {"title":"活动三：汇报与评估","body":"学生展示本课任务的记录或作品，依据实际证据解释结果；同伴按学习重点核对，教师纠正误解。"}],
          pbd="根据实际观察记录、图表或作品，逐项评估："+focus,
          remedial="教师针对未掌握的步骤提供图示、示范或分步提示，再让学生重试。",
          extension="学生运用本课方法处理另一项教师选定的安全实例，并说明理由。",
          closure="学生分享本课发现，教师依据学习重点总结并给予反馈。",
          reflection="达到学习标准的学生人数：　尚未达到的学生人数：　后续教学按实际表现安排。",
          sk_display=[k+" "+descriptions["sk"][k] for k in r["sk"]],
          sp_display=[k+" "+descriptions["sp"][k]["description"] for k in r["sp"]],
          standard_status="EDITORIAL_LABELS_PENDING_INDEPENDENT_DSKP_CHECK")
        yield r

def rows(r):
    return [
      ("主题／单元",[r["theme"]+" · "+r["unit"]]),
      ("内容标准 SK",r["sk_display"]),
      ("学习标准 SP",r["sp_display"]),
      ("课本页码",[r["textbook_pages"]]),
      ("学习目标",[r["objective"]]),
      ("成功标准",[r["criteria"]]),
      ("教具",[r["bbm"]]),
      ("跨课程元素／价值",["科学思维、合作、诚实记录及安全。"]),
      ("二十一世纪学习",["沟通、合作、以证据说明。"]),
      ("导入",[r["induction"]]),
      ("主要活动",[(a["title"],a["body"]) for a in r["activities"]]),
      ("课堂评估 PBD",[r["pbd"]]),
      ("总结",[r["closure"]]),
      ("补救",[r["remedial"]]),
      ("增广",[r["extension"]]),
      ("教学反思",[r["reflection"]]),
    ]

def render_word(r):
    from docx import Document
    from docx.shared import Mm,Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from web.rph_document_style import style_word_table
    from web.rph_unified_engine import TEACHER_PANEL_FILL
    from dlp_year2_rph import _SCIENCE_FILL
    d=Document();s=d.sections[0]
    s.page_width,s.page_height=Mm(210),Mm(297)
    s.left_margin=s.right_margin=Mm(14)
    s.top_margin=s.bottom_margin=Mm(12)
    normal=d.styles["Normal"]
    normal.font.name="Noto Sans CJK SC";normal.font.size=Pt(9)
    normal.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"Noto Sans CJK SC")
    normal.paragraph_format.space_after=Pt(0)
    normal.paragraph_format.line_spacing=1.03
    def fill(cell,color):
        n=OxmlElement("w:shd");n.set(qn("w:fill"),color)
        cell._tc.get_or_add_tcPr().append(n)
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    t=p.add_run("每日教学计划 · RANCANGAN PENGAJARAN HARIAN");t.bold=True;t.font.size=Pt(13)
    p.paragraph_format.space_after=Pt(4)
    head=d.add_table(rows=1,cols=2)
    head.cell(0,0).text=f"科学 (SJKC) · Tahun {r['year']}\nPdP {r['pdp']:03d} · {r['topic']}"
    head.cell(0,1).text="班级 Kelas：\n日期 Tarikh：\n时间 Masa：\n学生人数 Bil. Murid："
    style_word_table(head,(118,64),padding=45)
    fill(head.cell(0,0),_SCIENCE_FILL);fill(head.cell(0,1),TEACHER_PANEL_FILL)
    p=d.add_paragraph();p.paragraph_format.line_spacing=Pt(3);p.add_run(" ").font.size=Pt(1)
    data=rows(r);table=d.add_table(rows=len(data),cols=2)
    for i,(key,values) in enumerate(data):
        left,right=table.rows[i].cells;left.text=key;fill(left,_SCIENCE_FILL)
        for n,value in enumerate(values):
            p=right.paragraphs[0] if n==0 else right.add_paragraph()
            if isinstance(value,tuple):
                p.add_run(value[0]).bold=True
                p.add_run("\n"+value[1])
            else:p.add_run(str(value))
        table.rows[i]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    style_word_table(table,(38,144),padding=35)
    # This is an unpublished QA document. No invented SK/SP descriptions.
    output=BytesIO();d.save(output);return output.getvalue()

def export(out,year):
    from docx import Document
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files=[]
    for r in records(year):
        payload=render_word(r)
        doc=Document(BytesIO(payload))
        assert len(doc.tables)==2
        text=" ".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
        assert all(k in text for k in r["sk_display"]+r["sp_display"])
        assert all(a["body"] in text for a in r["activities"])
        assert all(any(run.bold and run.text.startswith(a["title"]) for t in doc.tables for row in t.rows for c in row.cells for p in c.paragraphs for run in p.runs) for a in r["activities"])
        name=f"CIKGULAJU_SAINS_SJKC_T{year}_PDP{r['pdp']:03d}_QA.docx"
        (out/name).write_bytes(payload)
        files.append({"name":name,"sha256":hashlib.sha256(payload).hexdigest(),"standard_status":r["standard_status"]})
    assert len(files)==COUNTS[year]
    (out/"manifest.json").write_text(json.dumps({"status":"QA_NOT_PUBLISHED","ready":0,"files":files},ensure_ascii=False,indent=2),encoding="utf-8")
    print("Word QA:",year,len(files))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--year",type=int,required=True,choices=COUNTS)
    p.add_argument("--out",required=True);a=p.parse_args()
    export(a.out,a.year)
