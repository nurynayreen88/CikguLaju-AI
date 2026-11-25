"""QA only: detect impossible Quran verse references in current PI objectives.
Standard Madani numbering. Never infer a corrected range from a bad source.
Unparsed and unknown references must be reviewed rather than silently approved.
"""
import re
import unicodedata

# Named surahs in the standard 114-surah order; counts are verse limits.
NAMES = """الفاتحة البقرة آل_عمران النساء المائدة الأنعام الأعراف الأنفال التوبة يونس هود يوسف الرعد إبراهيم الحجر النحل الإسراء الكهف مريم طه الأنبياء الحج المؤمنون النور الفرقان الشعراء النمل القصص العنكبوت الروم لقمان السجدة الأحزاب سبأ فاطر يس الصافات ص الزمر غافر فصلت الشورى الزخرف الدخان الجاثية الأحقاف محمد الفتح الحجرات ق الذاريات الطور النجم القمر الرحمن الواقعة الحديد المجادلة الحشر الممتحنة الصف الجمعة المنافقون التغابن الطلاق التحريم الملك القلم الحاقة المعارج نوح الجن المزمل المدثر القيامة الإنسان المرسلات النبأ النازعات عبس التكوير الانفطار المطففين الانشقاق البروج الطارق الأعلى الغاشية الفجر البلد الشمس الليل الضحى الشرح التين العلق القدر البينة الزلزلة العاديات القارعة التكاثر العصر الهمزة الفيل قريش الماعون الكوثر الكافرون النصر المسد الإخلاص الفلق الناس""".split()
COUNTS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
assert len(NAMES)==len(COUNTS)==114
def norm(s):
    s=unicodedata.normalize("NFKC",str(s or ""))
    s="".join(c for c in s if not unicodedata.combining(c))
    return s.translate(str.maketrans("أإآٱىـ٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹","ااااي 01234567890123456789")).replace("ـ","")
LIMITS={norm(n.replace("_"," ")):c for n,c in zip(NAMES,COUNTS)}
LIMITS.update({norm("الانشراح"):8,norm("تبت"):5,norm("بني اسرائيل"):111,norm("الم نشرح"):8,norm("التوحيد"):4})
# Read named surah followed immediately by an explicit verse marker/range.
ALIASES="|".join(re.escape(n) for n in sorted(LIMITS,key=len,reverse=True))
TARGET=re.compile(r"(?<!\w)(?P<name>"+ALIASES+r")\s*(?:اية|ايات)\s*(?P<start>\d{1,3})(?:\s*[-–—]\s*(?P<end>\d{1,3}))?")
MARKERS=re.compile(r"(?:اية|ايات)\s*\d{1,3}")
def inspect_verse_ranges(objective):
    value=norm(objective)
    matches=list(TARGET.finditer(value))
    records=[]
    for m in matches:
        name=m["name"]; start=int(m["start"]); end=int(m["end"] or start); limit=LIMITS[name]
        records.append({"surah":name,"start":start,"end":end,"limit":limit,"valid":1<=start<=end<=limit})
    marker_count=len(list(MARKERS.finditer(value)))
    return {"references":records,"unparsed_markers":max(0,marker_count-len(matches)),
            "status":"INVALID_RANGE" if any(not x["valid"] for x in records) else "UNPARSED_REFERENCE" if marker_count>len(matches) else "IN_RANGE_ONLY" if records else "NO_EXPLICIT_RANGE"}
def self_test():
    assert inspect_verse_ranges("ممباچ الشورى اية ٣٣-٧٧")["status"]=="INVALID_RANGE"
    assert inspect_verse_ranges("سورة المائدة أية ١١٤-١٢٠ دان سورة الأنعام أية ١-١٨")["status"]=="IN_RANGE_ONLY"
    assert inspect_verse_ranges("سورة البقرة أية ٢٨٦-٢٨٧")["status"]=="INVALID_RANGE"
    assert inspect_verse_ranges("سورة مجهول اية ١-٣")["status"]=="UNPARSED_REFERENCE"
    assert inspect_verse_ranges("سورة البقرة اية ٢-١")["status"]=="INVALID_RANGE"
    assert inspect_verse_ranges("سورة البقرة اية ٠-١")["status"]=="INVALID_RANGE"
if __name__=="__main__":
    self_test()
