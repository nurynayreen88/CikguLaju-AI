"""Presentation-only PI numbered learning objectives; never alter academic text."""
import re

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_MARKER = re.compile(r"(?<!\S)([0-9٠-٩۰-۹]{1,2})[.)](?=[ \t]+\S)")
def objective_lines(value):
    if not isinstance(value, str):return value
    matches=list(_MARKER.finditer(value))
    # Only genuine sequential numbered lists, not standard codes or isolated
    # numerals embedded in a sentence.
    if len(matches)<2 or [int(m[1].translate(_DIGITS)) for m in matches]!=list(range(1,len(matches)+1)):
        return value
    result=value
    for m in reversed(matches):
        start=m.start()
        left=start
        while left>0 and result[left-1] in " \t":left-=1
        if left==0 or result[left-1]=="\n":continue
        result=result[:left]+"\n"+result[start:]
    return result
