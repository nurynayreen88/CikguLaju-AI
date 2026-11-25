"""QA-only source-grounded differentiation of PI recitation activity targets.

Do not generate Quran text or infer tajwid rules. Only exact surah and verse
range stated in the current verified objective can enter the proposed steps.
"""
import re
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits

# Source objective commonly contains e.g. سورة المائدة أية ٧٧-٩٥.
_TARGET = re.compile(r"سورة\s+[\u0621-\u064a]+(?:\s+[\u0621-\u064a]+){0,2}\s+[اأآ]ية\s*[0-9٠-٩۰-۹]{1,3}\s*[-–—]\s*[0-9٠-٩۰-۹]{1,3}")
_GENERIC_READ = ("ممباچ اية سچارا تلقي دان مشافهة",
                 "ممباچ اية سچارا تلقي دان مشافهة.")
def specialize_recitation(item):
    if not isinstance(item,dict) or item.get("unit")!="Al-Quran" or item.get("ready") is not False:
        return None
    objective=str(item.get("objective") or "")
    targets=list(dict.fromkeys(m.group() for m in _TARGET.finditer(objective)))
    if len(targets)!=1:
        return None
    target=targets[0]
    main=str(item.get("candidate_main") or "")
    # Only a complete exact known source reading instruction is transformed.
    # Preserve subsequent specific correction, paired practice and record steps.
    old="ممباچ اية سچارا تلقي دان مشافهة"
    if main.count(old)!=1 or target in main:
        return None
    new="موريد ممباچ "+target+" سچارا تلقي دان مشافهة دڠن بيمبيڠن ݢورو"
    result=main.replace(old,new,1)
    result=jawi_display_digits(result)
    if result==main:
        return None
    return {**item,"specific_main":result,"specific_target":target,
            "specific_source_phrase":old,"specific_replacement":new,
            "status":"QA_HOLD_DSKP_MUSHAF_AND_EDITORIAL_REVIEW","ready":False}
