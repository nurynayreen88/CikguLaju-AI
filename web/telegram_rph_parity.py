"""Mirror Telegram _create_rph_word's three-table Word/PDF/HTML structure.

Uses source-specific RPH fields. Never imports the Telegram webhook or invents
curriculum standards. One contract powers print preview and Word downloads.
"""
from datetime import date
import re

COMMON = ("MATA PELAJARAN","TAHUN/TINGKATAN","TARIKH","HARI","MASA","KELAS",
          "BILANGAN MURID","TAJUK")
ENDING = ("OBJEKTIF PEMBELAJARAN","KRITERIA KEJAYAAN","PENGETAHUAN SEDIA ADA",
          "BAHAN BANTU MENGAJAR","EMK / NILAI","KBAT / PAK21","PENTAKSIRAN")
MALAY_META = COMMON + ("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN") + ENDING
ENGLISH_META = COMMON + ("MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
    "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD") + ENDING
ENGLISH_LABELS = {
    "MATA PELAJARAN":"Subject","TAHUN/TINGKATAN":"Year / Form",
    "TARIKH":"Date","HARI":"Day","MASA":"Time","KELAS":"Class",
    "BILANGAN MURID":"Number of Pupils","TAJUK":"Topic",
    "OBJEKTIF PEMBELAJARAN":"Learning Objectives","KRITERIA KEJAYAAN":"Success Criteria",
    "PENGETAHUAN SEDIA ADA":"Prior Knowledge",
    "BAHAN BANTU MENGAJAR":"Teaching and Learning Materials",
    "EMK / NILAI":"CCE / Values","KBAT / PAK21":"HOTS / 21st Century Skills",
    "PENTAKSIRAN":"Assessment",
}
AUDIT_PREFIXES = ("qa","status","source classification","resource status",
    "resource gate","bukti audit","jejak audit","audit notes","bukti visual",
    "rujukan","source qa","verified mapping","original source","original book",
    "resource access")
BOLD = re.compile(r"\*\*([^*\n]{1,155})\*\*")
TIME = re.compile(r"\(\s*(\d{1,3})\s*(?:min|minutes|minute|minit)\b[^)]*\)",re.I)

def clean(value):
    value = str(value or "").strip()
    value = re.sub(r"\[([^]\n]+)\]\([^)]+\)",r"\1",value)
    value = re.sub(r"\*\*([^*]+)\*\*",r"\1",value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)",r"\1",value)
    value = re.sub(r"\x60([^\x60]+)\x60",r"\1",value)
    value = re.sub(r"(?m)^\s*[-*]\s+","• ",value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    return value.strip()

def norm(label):
    return " ".join(re.sub(r"[^a-z0-9/]+"," ",str(label).casefold()).split())

def _source_items(fields):
    for field in fields:
        heading=str(field.get("label") or "").strip()
        raw=str(field.get("value") or "").strip()
        if not heading or not raw or heading.casefold().startswith(AUDIT_PREFIXES):
            continue
        if norm(heading) in ("maklumat rph","langkah pdp","lesson information","lesson details"):
            matches=list(BOLD.finditer(raw))
            for i,match in enumerate(matches):
                label=match.group(1).strip().rstrip(":")
                if ":" not in match.group(1):
                    continue
                text=raw[match.end():matches[i+1].start() if i+1<len(matches) else len(raw)]
                if text.strip() and not label.casefold().startswith(AUDIT_PREFIXES):
                    yield label,clean(text)
        else:
            yield heading,clean(raw)

def classify(label):
    s=norm(label)
    rules=(
        (r"^(set induksi|set induction)","induction"),
        (r"^(closure|penutup|rumusan)","closure"),
        (r"^(activity|aktiviti|main activities|main activity|langkah [1-9]|reinforcement|pengukuhan|assessment / pbd|pbd / reinforcement|pentaksiran pbd)","main"),
        (r"^(main sk/sp|main content standard|main cs)","main_standard"),
        (r"^(complementary sk/sp|complementary content standard|complementary cs)","comp_standard"),
        (r"^(main ls|main learning standard)","main_ls"),
        (r"^(complementary ls|complementary learning standard)","comp_ls"),
        (r"^(standard kandungan|sk)$","sk"),
        (r"^(standard pembelajaran|sp)$","sp"),
        (r"^(learning objective|learning objectives|objectives|objective|objektif)","objectives"),
        (r"^(success criteria|kriteria kejayaan)","success"),
        (r"^(materials|teaching and learning materials|teaching aids|bbm|bahan bantu mengajar)","materials"),
        (r"^(pbd|assessment|pentaksiran|penilaian)","assessment"),
        (r"^(differentiation|pembezaan|pemulihan|pengayaan|remedial|enrichment)","support"),
        (r"^(reflection|refleksi)","reflection"),
        (r"^(prior knowledge|pengetahuan sedia ada)","knowledge"),
        (r"^(emk|nilai)","values"),(r"^(kbat|pak21|hots)","hots"),
        (r"^(topic|tajuk|unit)","topic"),
    )
    for pattern,category in rules:
        if re.search(pattern,s):
            return category
    return "extra"

def _standard_pair(value):
    match=re.search(r"((?:\d{1,2}\.){1,3}\d*)\s*/\s*((?:\d{1,2}\.){1,3}\d*)",value)
    if not match:
        return value,""
    before=value[:match.start()].strip()
    after=value[match.end():].strip()
    return ((before+" " if before else "")+match.group(1)).strip(), (
        match.group(2)+(" "+after if after else "")).strip()

def _phase_label(name,kind,english):
    base=({"induction":"Set Induction","closure":"Closure"} if english else
          {"induction":"Set Induksi","closure":"Penutup"})[kind]
    found=TIME.search(name)
    return base+(" ("+found.group(1)+" min)" if found else "")

def build_layout(data,subject_labels):
    if not isinstance(data,dict) or not isinstance(data.get("fields"),list):
        raise ValueError("Verified RPH fields missing")
    english=data["subject"]=="ENGLISH"
    labels=ENGLISH_META if english else MALAY_META
    meta={label:"—" for label in labels}
    teacher=data.get("teacher") or {}
    meta.update({
        "MATA PELAJARAN":subject_labels[data["subject"]],
        "TAHUN/TINGKATAN":("Year " if english else "Tahun ")+str(data["year"]),
        "TARIKH":clean(teacher.get("date")) or "________________",
        "MASA":clean(teacher.get("time")) or "________________",
        "KELAS":clean(teacher.get("class")) or "________________",
        "BILANGAN MURID":"________________",
        "TAJUK":clean(data.get("unit") or data.get("title")) or "—",
    })
    if teacher.get("date"):
        weekday=date.fromisoformat(teacher["date"]).weekday()
        meta["HARI"]=(
            ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday") if english else
            ("Isnin","Selasa","Rabu","Khamis","Jumaat","Sabtu","Ahad"))[weekday]
    else:
        meta["HARI"]="________________"
    phases={"induction":[],"main":[],"closure":[]}
    labels_for={}
    supports=[];reflection=[];extra=[]
    for label,value in _source_items(data["fields"]):
        if not value or len(value)>18000:
            continue
        category=classify(label)
        if category in phases:
            if category!="main":
                labels_for.setdefault(category,_phase_label(label,category,english))
            text=clean(label)+":\n"+value if category=="main" else value
            phases[category].append(text)
        elif category=="main_standard":
            cs,ls=_standard_pair(value)
            meta["MAIN CONTENT STANDARD"]=cs
            if ls: meta["MAIN LEARNING STANDARD"]=ls
        elif category=="comp_standard":
            cs,ls=_standard_pair(value)
            meta["COMPLEMENTARY CONTENT STANDARD"]=cs
            if ls: meta["COMPLEMENTARY LEARNING STANDARD"]=ls
        elif category in ("main_ls","comp_ls"):
            meta["MAIN LEARNING STANDARD" if category=="main_ls" else "COMPLEMENTARY LEARNING STANDARD"]=value
        elif category=="sk": meta["STANDARD KANDUNGAN"]=value
        elif category=="sp": meta["STANDARD PEMBELAJARAN"]=value
        elif category=="objectives":
            meta["OBJEKTIF PEMBELAJARAN"]=value
            split=re.search(r"\bKriteria kejayaan\s*:\s*",value,re.I)
            if split:
                meta["OBJEKTIF PEMBELAJARAN"]=value[:split.start()].strip()
                meta["KRITERIA KEJAYAAN"]=value[split.end():].strip()
        elif category=="success":meta["KRITERIA KEJAYAAN"]=value
        elif category=="materials":meta["BAHAN BANTU MENGAJAR"]=value
        elif category=="assessment":meta["PENTAKSIRAN"]=value
        elif category=="support":supports.append(value)
        elif category=="reflection":reflection.append(value)
        elif category=="knowledge":meta["PENGETAHUAN SEDIA ADA"]=value
        elif category=="values":meta["EMK / NILAI"]=value
        elif category=="hots":meta["KBAT / PAK21"]=value
        elif category=="topic" and norm(label) in ("topic","tajuk"):
            meta["TAJUK"]=value
        elif category=="extra" or category=="topic":
            if not norm(label).startswith(AUDIT_PREFIXES):
                extra.append(clean(label)+": "+value)
    if not any(phases.values()):
        raise ValueError("No lesson-specific activity available")
    if extra:
        meta["PENGETAHUAN SEDIA ADA"]=(
            ("" if meta["PENGETAHUAN SEDIA ADA"]=="—" else meta["PENGETAHUAN SEDIA ADA"]+"\n")+
            "\n".join(extra))
    return {
        "style":"telegram-native-rph-v1",
        "title":"DAILY LESSON PLAN" if english else "RANCANGAN PENGAJARAN HARIAN",
        "header":[{"label":ENGLISH_LABELS.get(k,k.title()) if english else k.title(),
                   "value":meta[k]} for k in labels],
        "activity_header":(
            ["Phase / Time","Teaching and Learning Activities","Notes"] if english else
            ["Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"]),
        "phases":[
            {"label":labels_for.get("induction","Set Induction" if english else "Set Induksi"),
             "activity":"\n\n".join(phases["induction"]) or "—","notes":""},
            {"label":"Main Activities" if english else "Aktiviti Utama",
             "activity":"\n\n".join(phases["main"]) or "—","notes":""},
            {"label":labels_for.get("closure","Closure" if english else "Penutup"),
             "activity":"\n\n".join(phases["closure"]) or "—","notes":""},
        ],
        "footer":[
            {"label":"Remedial / Enrichment" if english else "Pemulihan / Pengayaan",
             "value":"\n".join(supports) or "—"},
            {"label":"Reflection" if english else "Refleksi",
             "value":"\n".join(reflection) or (
                 "____ / ____ pupils achieved the lesson objectives.\n"
                 "____ / ____ pupils require further support.\n"
                 "Follow-up action: ______________________________" if english else
                 "____ / ____ murid mencapai objektif.\n"
                 "____ / ____ murid belum mencapai objektif.\n"
                 "Tindakan susulan: ______________________________")},
        ],
    }
