#!/usr/bin/env python3
"""CikguLaju worksheet renderer v1 — reference-locked, direct PDF only.
Use the approved Batch 03 student PDF as the reference, not Google Docs.
This is a reconstruction; the original local generator was not recoverable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
from pathlib import Path

import fitz
from fontTools.ttLib import TTFont
import fontTools

VERSION = "1.0.1-draft"
EXPECTED_REF = "Tukar Pecahan dan Nombor Bercampur"
WHITE = (1, 1, 1)
NAVY = (0.13, 0.21, 0.32)
BROWN = (0.47, 0.32, 0.17)
PALE = (0.92, 0.90, 0.84)
LINE = (0.65, 0.70, 0.75)
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")


def fail(message):
    raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(name):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^[A-Z]{6}\+", "", name).lower())


def locate(page, text):
    hits = page.search_for(text)
    if len(hits) != 1:
        fail(f"Reference page {page.number+1}: expected one occurrence of {text!r}, found {len(hits)}")
    rect = hits[0]
    spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b
             for line in b["lines"] for s in line["spans"]]
    candidates = [s for s in spans if fitz.Rect(s["bbox"]).intersects(rect)]
    if not candidates:
        fail(f"Could not extract reference font for {text!r}")
    # Choose the span with the greatest overlap with the requested phrase.
    s = max(candidates, key=lambda x: (fitz.Rect(x["bbox"]) & rect).get_area())
    color = s["color"]
    return {
        "rect": list(rect), "font": s["font"], "size": s["size"],
        "baseline": s["origin"][1],
        "color": [(color >> 16 & 255)/255, (color >> 8 & 255)/255, (color & 255)/255],
    }


def font_index(dirs):
    """Only full installed fonts; no silent fallback or font redistribution."""
    result = {}
    for root in dirs:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() not in (".ttf", ".otf") or not p.is_file():
                continue
            try:
                with TTFont(p, lazy=True) as f:
                    for record in f["name"].names:
                        if record.nameID in (4, 6):
                            result.setdefault(normalized(record.toUnicode()), []).append(p)
            except Exception:
                continue
    return result


def find_fonts(styles, dirs, locked=None):
    indexed = font_index(dirs)
    chosen = {}
    for name in sorted({s["font"] for s in styles.values()}):
        options = sorted(set(indexed.get(normalized(name), [])), key=str)
        if locked:
            options = [p for p in options if sha(p) == locked.get(name)]
        if not options:
            fail(f"Exact full font not found: {name}. Supply original installed font with --font-dir; no substitution.")
        chosen[name] = options[0]
    return chosen


class Template:
    def __init__(self, source, font_dirs, lockfile, init_lock):
        self.source = Path(source)
        self.ref = fitz.open(self.source)
        if len(self.ref) != 28:
            fail("Expected the approved 28-page T4 Batch 03 student PDF.")
        p0, p1, p12, p13 = self.ref[0], self.ref[1], self.ref[12], self.ref[13]
        if EXPECTED_REF not in p0.get_text():
            fail("Wrong reference PDF. Use approved Batch 03 student file.")
        self.w, self.h = p0.rect.width, p0.rect.height
        if any(abs(p.rect.width-self.w) > .1 or abs(p.rect.height-self.h) > .1
               or p.rotation for p in (p0, p1, p12, p13)):
            fail("Reference pages must have identical unrotated page dimensions.")
        self.styles = {}
        self.fields = {}
        for i, page in enumerate((p0, p1)):
            d = {
                "subject": locate(page, "MATEMATIK SK • TAHUN 4"),
                "sp": locate(page, "SP 2.1.1"),
                "page": locate(page, f"{i+1}/2"),
            }
            if i == 0:
                d.update(theme=locate(page, "PECAHAN, PERPULUHAN DAN PERATUS"),
                         title=locate(page, EXPECTED_REF))
            self.fields[i] = d
            self.styles.update({f"{i}_{k}": v for k, v in d.items()})
        self.styles["section"] = locate(p12, "Kira dalam bentuk lazim.")
        self.styles["body"] = locate(p13, "8.7 + 4.085 + 2.63 =")
        self.styles["bold"] = self.styles["section"]
        self.styles["small"] = locate(p13, "Kira:") if len(p13.search_for("Kira:")) == 1 else self.styles["body"]
        lockfile = Path(lockfile)
        expected = json.loads(lockfile.read_text(encoding="utf-8")) if lockfile.exists() else None
        if not expected and not init_lock:
            fail("Missing design lock. First calibration must explicitly use --init-lock.")
        if expected and init_lock:
            fail("Existing lock must never be overwritten. Use a new version for approved redesign.")
        self.paths = find_fonts(self.styles, font_dirs, expected.get("fonts") if expected else None)
        snapshot = {
            "renderer": VERSION, "renderer_sha256": sha(__file__),
            "reference_sha256": sha(self.source),
            "pymupdf": fitz.VersionBind, "fonttools": fontTools.__version__,
            "page_size": [self.w, self.h],
            "fonts": {n: sha(p) for n, p in self.paths.items()},
            "styles": self.styles, "fields": self.fields_as_json(),
        }
        if expected and expected != snapshot:
            fail("Design lock mismatch. Do not silently change PDF, fonts, code, dimensions or library versions.")
        self.pending_lock = (lockfile, snapshot) if init_lock else None
        self.names = {n: f"CLFont{i}" for i,n in enumerate(sorted(self.paths))}
        self.fonts = {n: fitz.Font(fontfile=str(p)) for n,p in self.paths.items()}
        self.templates = {}
        for i in (0, 1):
            # Copy only the header/footer raster after removing changing text.
            # This avoids exposing old question/answer text in clipped PDF forms.
            with fitz.open() as temp:
                temp.insert_pdf(self.ref, from_page=i, to_page=i)
                page = temp[0]
                for field in self.fields[i].values():
                    page.add_redact_annot(fitz.Rect(field["rect"]), fill=False, cross_out=False)
                page.apply_redactions(images=0, graphics=0, text=0)
                for field in self.fields[i].values():
                    # Changing fields must be fully removed from the template.
                    if page.get_textbox(fitz.Rect(field["rect"])).strip():
                        fail("Reference text could not be removed cleanly.")
                top = self.h * (.222 if i == 0 else .078)
                bottom = self.h * .962
                self.templates[i] = []
                for clip in (fitz.Rect(0, 0, self.w, top), fitz.Rect(0, bottom, self.w, self.h)):
                    pix = page.get_pixmap(matrix=fitz.Matrix(4,4), clip=clip, alpha=False)
                    self.templates[i].append((clip, pix.tobytes("png")))

    def fields_as_json(self):
        return {str(k): v for k,v in self.fields.items()}

    def font(self, style):
        return self.fonts[style["font"]]

    def width(self, text, style, size=None):
        return self.font(style).text_length(text, fontsize=size or style["size"])

    def text(self, page, x, y, value, style="body", size=None, align="left", maxwidth=None, color=None):
        s = self.styles[style] if isinstance(style, str) else style
        value = str(value)
        size = size or s["size"]
        if any(self.font(s).has_glyph(ord(c)) == 0 for c in value if not c.isspace()):
            fail(f"Missing glyph in exact font: {value!r}")
        width = self.width(value, s, size)
        if maxwidth is not None and width > maxwidth + .05:
            fail(f"Text exceeds fixed space: {value!r} ({width:.1f} > {maxwidth:.1f} pt)")
        if align == "right":
            x -= width
        elif align == "center":
            x -= width/2
        page.insert_font(fontname=self.names[s["font"]], fontfile=str(self.paths[s["font"]]))
        page.insert_text((x,y), value, fontsize=size, fontname=self.names[s["font"]],
                         color=color or tuple(s["color"]))

    def wrap(self, page, x, y, text, width, style="body", max_lines=3, size=None):
        s = self.styles[style]
        size = size or s["size"]
        lines = []
        for part in str(text).splitlines():
            line = ""
            for word in part.split():
                if self.width(word, s, size) > width:
                    fail(f"Unbreakable word too wide: {word!r}")
                candidate = (line+" "+word).strip()
                if line and self.width(candidate,s,size) > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        if len(lines) > max_lines:
            fail(f"Too many lines ({len(lines)}>{max_lines}): {text!r}")
        for i,line in enumerate(lines):
            self.text(page,x,y+i*size*1.38,line,style,size,maxwidth=width)
        return y + len(lines)*size*1.38

    def base(self, doc, sheet, index, total, key=False):
        page = doc.new_page(width=self.w, height=self.h)
        # Answer keys use same top strip on page 2, no student metadata.
        i = 1 if key or index else 0
        for rect, png in self.templates[i]:
            page.insert_image(rect, stream=png)
        values = {
            "subject": sheet["subject"],
            "sp": "SP " + sheet["sp"],
            "page": f"{index+1}/{total}",
            "theme": sheet["theme"],
            "title": sheet["title"],
        }
        for k,s in self.fields[i].items():
            r = fitz.Rect(s["rect"])
            if k in ("sp","page"):
                x, align, maxw = r.x1, "right", self.w*.24
            elif k == "subject":
                x, align, maxw = (r.x0+r.x1)/2, "center", self.w*.42
            else:
                x, align = r.x0, "left"
                maxw = self.w*(.64 if k=="theme" else .87)
            self.text(page,x,s["baseline"],values[k],s,align=align,maxwidth=maxw)
        if key:
            # The reference footer names the student worksheet, not the answer key.
            footer = fitz.Rect(0, self.h*.977, self.w*.7, self.h)
            page.draw_rect(footer, color=None, fill=WHITE, overlay=True)
            self.text(page,self.w*.064,self.h*.989,"CIKGULAJU / SKEMA JAWAPAN",
                      style="body",size=8,color=BROWN,maxwidth=self.w*.60)
        return page

    def save_pending_lock(self):
        if self.pending_lock:
            path, snapshot = self.pending_lock
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
                f.write("\n")


def require_keys(obj, required, allowed, where):
    if not isinstance(obj, dict):
        fail(f"{where}: expected object")
    missing = set(required)-obj.keys()
    unknown = obj.keys()-set(allowed)
    if missing or unknown:
        fail(f"{where}: missing={sorted(missing)}, unknown={sorted(unknown)}")


KINDS = {"vertical", "division", "work", "problem", "short", "choice", "matching", "table", "clock", "timeline"}
ITEM_KEYS = {"id","text","terms","op","dividend","divisor","options","left","right","cells","hour","minute","start","end"}
def validate(data):
    require_keys(data, ["worksheets"], ["worksheets"], "batch")
    if not isinstance(data["worksheets"],list) or not data["worksheets"]:
        fail("Empty batch.")
    seen_sheets = set()
    for s in data["worksheets"]:
        require_keys(s,["id","subject","sp","theme","title","source","pages","answers"],
                     ["id","subject","sp","theme","title","source","pages","answers"],"worksheet")
        if not isinstance(s["id"],str) or not ID_RE.fullmatch(s["id"]) or s["id"] in seen_sheets:
            fail("Invalid or duplicate worksheet ID.")
        seen_sheets.add(s["id"])
        for k in ("subject","sp","theme","title","source"):
            if not isinstance(s[k],str) or not s[k].strip():
                fail(f"Missing {k}: {s['id']}")
        if not isinstance(s["pages"],list) or len(s["pages"]) not in (1,2):
            fail("Each worksheet must have one or two student pages.")
        ids, labels, signatures, kinds = set(), set(), set(), set()
        for blocks in s["pages"]:
            if not isinstance(blocks,list) or not blocks:
                fail("Empty student page.")
            for b in blocks:
                require_keys(b,["label","kind","prompt","items"],
                             ["label","kind","prompt","items","headers"],"block")
                kind = b["kind"]
                if kind not in KINDS:
                    fail("Unsupported question layout: "+str(kind))
                kinds.add(kind)
                if not isinstance(b["label"],str) or not re.fullmatch("[A-Z]",b["label"]) or b["label"] in labels:
                    fail("Section letters must be unique A–Z.")
                labels.add(b["label"])
                if not isinstance(b["prompt"],str) or not b["prompt"].strip():
                    fail("Each section requires an instruction.")
                if not isinstance(b["items"],list) or not b["items"]:
                    fail("Empty section.")
                if kind=="table":
                    headers = b.get("headers")
                    if not isinstance(headers,list) or not 2<=len(headers)<=5 or any(not isinstance(h,str) or not h for h in headers):
                        fail("Table must have 2–5 named columns.")
                for it in b["items"]:
                    require_keys(it,["id"],ITEM_KEYS,"question")
                    k = it["id"]
                    if not isinstance(k,str) or not re.fullmatch(r"[1-9][0-9]{0,2}[a-z]?",k) or k in ids:
                        fail("Question IDs must be unique per worksheet.")
                    ids.add(k)
                    sig = json.dumps({a:v for a,v in it.items() if a!="id"},sort_keys=True,ensure_ascii=False)
                    if sig in signatures:
                        fail(f"Repeated question: {k}")
                    signatures.add(sig)
                    if kind=="vertical":
                        if it.get("op") not in ("+","−","×") or not isinstance(it.get("terms"),list) or not 2<=len(it["terms"])<=3:
                            fail("Vertical requires 2–3 terms and +, − or ×.")
                        if any(not isinstance(v,str) or not re.fullmatch(r"(?:RM)?[0-9][0-9 ]*(?:\.[0-9]{1,3})?",v) for v in it["terms"]):
                            fail("Vertical terms must be numeric strings, optional RM, up to 3 decimal places.")
                        if it["op"]=="×" and len(it["terms"])!=2:
                            fail("Vertical multiplication requires exactly two terms.")
                    elif kind=="division":
                        if type(it.get("divisor")) is not int or not 1<=it["divisor"]<=99 or not isinstance(it.get("dividend"),str) or not re.fullmatch(r"(?:RM)?[0-9][0-9 ]*(?:\.[0-9]{1,3})?",it["dividend"]):
                            fail("Invalid long division.")
                    elif kind=="clock":
                        if type(it.get("hour")) is not int or not 1<=it["hour"]<=12 or type(it.get("minute")) is not int or not 0<=it["minute"]<=59:
                            fail("Clock must have hour 1–12, minute 0–59.")
                    elif kind=="timeline":
                        parse_time(it.get("start"))
                        parse_time(it.get("end"))
                        if it["start"]==it["end"]:
                            fail("Timeline needs distinct times.")
                    elif kind=="matching":
                        if not it.get("left") or not it.get("right"):
                            fail("Matching needs left and right entries.")
                    elif kind=="table":
                        cells = it.get("cells")
                        if not isinstance(cells,list) or len(cells)!=len(b["headers"]) or None not in cells:
                            fail("Each table row needs matching columns and at least one blank.")
                    else:
                        if not isinstance(it.get("text"),str) or not it["text"].strip():
                            fail("Question text is required.")
                        if kind=="choice" and (not isinstance(it.get("options"),list) or not 2<=len(it["options"])<=4 or any(not isinstance(v,str) or not v.strip() for v in it["options"]) or len(set(it["options"]))!=len(it["options"])):
                            fail("Choice needs 2–4 options.")
        if len(kinds)<2:
            fail("Use at least two genuinely different question layouts per worksheet.")
        if not isinstance(s["answers"],dict) or set(s["answers"])!=ids:
            fail("Every question ID must have exactly one matching answer entry.")
        if any(not isinstance(v,str) or not v.strip() for v in s["answers"].values()):
            fail("Empty answer.")


def parse_time(value):
    if not isinstance(value,str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",value):
        fail(f"Invalid HH:MM: {value!r}")
    h,m = map(int,value.split(":"))
    return h*60+m


class Worksheet:
    def __init__(self, template, page, first):
        self.t, self.p = template, page
        self.w, self.h = template.w, template.h
        self.x, self.right = self.w*.064, self.w*.936
        self.width = self.right-self.x
        self.y = self.h*(.236 if first else .101)
        self.limit = self.h*.945
        self.gap = self.w*.026

    def reserve(self, height):
        start = self.y
        if start+height > self.limit + .1:
            fail(f"Page overflow: need {height:.1f} pt at y={start:.1f}; split into max two pages or reduce questions (never shrink font).")
        self.y += height
        return start

    def text(self,x,y,t,**kw):
        self.t.text(self.p,x,y,t,**kw)

    def line(self,x,y,x2):
        self.p.draw_line((x,y),(x2,y),color=NAVY,width=.65)

    def rect(self,x,y,w,h,fill=None):
        r=fitz.Rect(x,y,x+w,y+h)
        self.p.draw_rect(r,color=NAVY,fill=fill,width=.65)
        return r

    def section(self, b):
        y=self.reserve(self.h*.047)
        self.text(self.x,y+self.h*.014,b["label"],style="section",color=BROWN)
        self.text(self.x+self.w*.04,y+self.h*.014,b["prompt"],style="section",maxwidth=self.width-self.w*.04)
        kind=b["kind"]
        if kind in ("vertical","division","work","clock"):
            self.grid(kind,b["items"])
        elif kind=="table":
            self.table(b)
        elif kind=="matching":
            self.match(b["items"])
        else:
            for it in b["items"]:
                self.single(kind,it)
        self.reserve(self.h*.009)

    def grid(self,kind,items):
        height=self.h*({"vertical":.195,"division":.225,"work":.235,"clock":.235}[kind])
        cw=(self.width-self.gap)/2
        for j in range(0,len(items),2):
            y=self.reserve(height+self.h*.015)
            for col,it in enumerate(items[j:j+2]):
                x=self.x+col*(cw+self.gap)
                if kind!="clock":
                    self.rect(x,y,cw,height)
                self.text(x+12,y+22,it["id"]+".",style="section",color=BROWN,maxwidth=40)
                if kind=="vertical":
                    terms=it["terms"]
                    style = self.t.styles["bold"]
                    # Align all decimal points for addition/subtraction; not the
                    # final glyph when the number of fractional digits differs.
                    suffix_widths = [self.t.width("."+v.split(".",1)[1],style,17) if "." in v else 0 for v in terms]
                    anchor = x+cw-24-max(suffix_widths)
                    for k,v in enumerate(terms):
                        yy=y+44+k*23
                        right = x+cw-24 if it["op"]=="×" else anchor+suffix_widths[k]
                        self.text(right,yy,v,style="bold",size=17,align="right",maxwidth=right-x-44)
                        if k:
                            self.text(x+22,yy,it["op"],style="bold",size=16)
                    self.line(x+22,y+44+(len(terms)-1)*23+9,x+cw-22)
                elif kind=="division":
                    self.text(x+36,y+53,it["divisor"],style="bold",size=16,align="right",maxwidth=35)
                    self.text(x+48,y+53,it["dividend"],style="bold",size=16,maxwidth=cw-65)
                    self.p.draw_line((x+42,y+35),(x+cw-16,y+35),color=NAVY,width=.9)
                    self.p.draw_line((x+42,y+35),(x+42,y+61),color=NAVY,width=.9)
                elif kind=="work":
                    end=self.t.wrap(self.p,x+40,y+22,it["text"],cw-54,max_lines=4)
                    if end+38 > y+height-16:
                        fail("Work box leaves insufficient calculation space.")
                    self.text(x+12,end+10,"Kira:",style="body",size=10,color=BROWN)
                    self.line(x+14,y+height-16,x+cw-14)
                else:
                    self.clock(x+cw/2,y+height*.46,min(cw*.29,height*.33),it["hour"],it["minute"])
                    self.line(x+cw*.20,y+height-12,x+cw*.80)

    def clock(self,cx,cy,r,hour,minute):
        self.p.draw_circle((cx,cy),r,color=NAVY,width=1.1)
        for m in range(60):
            a=math.radians(m*6-90)
            inner=r*(.87 if m%5==0 else .95)
            self.p.draw_line((cx+inner*math.cos(a),cy+inner*math.sin(a)),
                             (cx+r*math.cos(a),cy+r*math.sin(a)),color=NAVY,width=.9 if m%5==0 else .4)
        for h in range(1,13):
            a=math.radians(h*30-90)
            self.text(cx+r*.73*math.cos(a),cy+r*.73*math.sin(a)+3,str(h),
                      style="body",size=10,align="center")
        for value,length,weight in (((hour%12+minute/60)*30,.48,2.5),(minute*6,.69,1.6)):
            a=math.radians(value-90)
            self.p.draw_line((cx,cy),(cx+r*length*math.cos(a),cy+r*length*math.sin(a)),color=NAVY,width=weight)
        self.p.draw_circle((cx,cy),2,color=NAVY,fill=NAVY)

    def table(self,b):
        headers=b["headers"]
        widths=[self.width/len(headers)]*len(headers)
        rh=self.h*.057
        y=self.reserve(rh*(len(b["items"])+1)+self.h*.008)
        # A real data table, not a grid of joined calculation boxes.
        for n, cells in enumerate([headers]+[it["cells"] for it in b["items"]]):
            x=self.x
            for j,v in enumerate(cells):
                self.rect(x,y+n*rh,widths[j],rh,PALE if n==0 else None)
                if v is None:
                    self.line(x+12,y+n*rh+rh*.73,x+widths[j]-12)
                else:
                    self.t.wrap(self.p,x+8,y+n*rh+17,str(v),widths[j]-16,
                                style="section" if n==0 else "body",max_lines=2,size=11)
                x+=widths[j]

    def match(self,items):
        y=self.reserve(self.h*.063*len(items))
        for i,it in enumerate(items):
            yy=y+i*self.h*.063
            self.text(self.x,yy+20,it["id"]+". "+it["left"],maxwidth=self.width*.43)
            self.p.draw_circle((self.x+self.width*.45,yy+16),2,color=NAVY,fill=NAVY)
            self.p.draw_circle((self.x+self.width*.57,yy+16),2,color=NAVY,fill=NAVY)
            self.text(self.x+self.width*.60,yy+20,f"{chr(65+i)}. {it['right']}",maxwidth=self.width*.39)

    def single(self,kind,it):
        if kind=="timeline":
            y=self.reserve(self.h*.15)
            start,end=parse_time(it["start"]),parse_time(it["end"])
            dur=(end-start)%1440
            self.text(self.x,y+13,it["id"]+".",style="section",color=BROWN)
            a,b=self.x+55,self.right-55
            yy=y+48
            self.line(a,yy,b)
            # Label real hourly boundaries; do not suggest unequal time gaps
            # with equally spaced arbitrary ticks.
            ticks = [(start, it["start"]), (start+dur, it["end"])]
            for absolute in range(((start//60)+1)*60,start+dur,60):
                if min(absolute-start,start+dur-absolute)>=20 and dur<=360:
                    ticks.append((absolute,f"{(absolute//60)%24:02d}:00"))
            for absolute,label in sorted(ticks):
                xx=a+(b-a)*(absolute-start)/dur
                self.p.draw_line((xx,yy-5),(xx,yy+5),color=NAVY,width=.8)
                self.text(xx,yy-12,label,align="center",size=10)
            self.text(a,yy+28,"Tempoh:",size=11)
            self.line(a+65,yy+30,b)
            return
        height=self.h*({"short":.082,"choice":.12,"problem":.225}[kind])
        y=self.reserve(height)
        end=self.t.wrap(self.p,self.x,y+16,it["id"]+". "+it["text"],self.width,max_lines=3)
        if kind=="choice":
            options="     ".join(f"{chr(65+j)}. {v}" for j,v in enumerate(it["options"]))
            bottom=self.t.wrap(self.p,self.x+18,end+8,options,self.width-18,max_lines=2,size=11)
            if bottom>y+height:
                fail("Choice options exceed reserved space.")
        elif kind=="problem":
            if end+38>y+height-15:
                fail("Problem leaves insufficient calculation space.")
            self.text(self.x+12,end+11,"Kira:",size=10,color=BROWN)
            self.line(self.x+10,y+height-15,self.right-10)
        elif "____" not in it["text"]:
            if end+8 > y+height:
                fail("Short question has no answer space.")
            self.line(self.x+18,end+5,self.right-16)


def render(template, data, out):
    validate(data)
    out=Path(out)
    if out.exists():
        fail("Output directory already exists. Choose a new directory; never overwrite approved batches.")
    out.mkdir(parents=True)
    combined=fitz.open()
    combined_key=fitz.open()
    manifest=[]
    try:
        for s in data["worksheets"]:
            n=len(s["pages"])
            doc=fitz.open()
            for i,blocks in enumerate(s["pages"]):
                p=template.base(doc,s,i,n)
                w=Worksheet(template,p,i==0)
                for block in blocks:
                    w.section(block)
            key=fitz.open()
            p=template.base(key,s,0,1,key=True)
            x=template.w*.064
            width=template.w*.87
            y=template.h*.12
            y=template.wrap(p,x,y,s["title"]+" — Skema Jawapan",width,style="section",max_lines=2)+14
            y=template.wrap(p,x,y,"Rujukan: "+s["source"],width,max_lines=3,size=10)+15
            for q,a in s["answers"].items():
                y=template.wrap(p,x,y,q+". "+a,width,max_lines=3,size=11)+7
                if y>template.h*.94:
                    fail("Answer key exceeds one page; revise answer wording or explicitly extend renderer.")
            for pdf,name in ((doc,s["id"]+".pdf"),(key,s["id"]+"_SKEMA.pdf")):
                pdf.set_metadata({"title":s["title"],"author":"CikguLaju","creator":VERSION})
                pdf.save(out/name,garbage=4,deflate=True)
            combined.insert_pdf(doc)
            combined_key.insert_pdf(key)
            manifest.append({"id":s["id"],"title":s["title"],"sp":s["sp"],"source":s["source"],
                             "student_pages":n,"questions":len(s["answers"]),"status":"DRAFT_VISUAL_QA_REQUIRED",
                             "pdf_sha256":sha(out/(s["id"]+".pdf")),"key_sha256":sha(out/(s["id"]+"_SKEMA.pdf"))})
            doc.close()
            key.close()
        combined.save(out/"MURID.pdf",garbage=4,deflate=True)
        combined_key.save(out/"SKEMA.pdf",garbage=4,deflate=True)
        qa=out/"preview"
        qa.mkdir()
        for label,pdf in (("murid",combined),("skema",combined_key)):
            for i,p in enumerate(pdf,1):
                p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(qa/f"{label}_{i:03}.png")
        (out/"manifest.json").write_text(json.dumps({"version":VERSION,"status":"DRAFT_VISUAL_QA_REQUIRED","worksheets":manifest},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        with zipfile.ZipFile(out/"BATCH.zip","w",zipfile.ZIP_DEFLATED) as z:
            for p in sorted(out.iterdir()):
                if p.is_file() and p.name!="BATCH.zip":
                    z.write(p,p.name)
        print(f"Generated {len(manifest)} worksheets. NOT READY: inspect every preview and verify answers/source/PdP.")
    except Exception:
        # Preserve partial outputs for diagnostics, clearly marked as failed.
        (out/"FAILED.txt").write_text("Batch incomplete. Do not publish any output.\n",encoding="utf-8")
        raise
    finally:
        combined.close()
        combined_key.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reference",required=True,type=Path)
    ap.add_argument("--input",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--lock",required=True,type=Path)
    ap.add_argument("--init-lock",action="store_true")
    ap.add_argument("--font-dir",action="append",type=Path,default=[])
    a=ap.parse_args()
    dirs=a.font_dir+[Path("/usr/share/fonts"),Path("/usr/local/share/fonts"),Path.home()/".local/share/fonts",Path("C:/Windows/Fonts")]
    try:
        t=Template(a.reference,dirs,a.lock,a.init_lock)
        render(t,json.loads(a.input.read_text(encoding="utf-8")),a.output)
        t.save_pending_lock()
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
