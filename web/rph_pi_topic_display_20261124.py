"""Remove exact timetable duration tokens from the printed PI topic only."""
import re

# Actual native source includes ١ جم, ٣٠ مينيت, ١ جم ٣٠ مينيت.
# Preserve parenthetical topic qualifiers and revision notes.
_DURATION = re.compile(
    r"\s+(?:"
    r"[1١۱]\s*جم(?:\s*[3٣۳][0٠۰]\s*مينيت)?"
    r"|[3٣۳][0٠۰]\s*مينيت"
    r"|[1١۱]\s*jam(?:\s+setengah|\s+[3٣۳][0٠۰]\s*minit)?"
    r"|setengah\s+jam"
    r"|[3٣۳][0٠۰]\s*minit"
    r")(?=\s*(?:\(|$))", re.IGNORECASE
)

def duration_span(value):
    match = _DURATION.search(value)
    if match is None or not value[:match.start()].strip():
        return None
    return match.span()

def clean_pi_topic(value):
    span = duration_span(value)
    if span is None:
        return value
    start,end=span
    return value[:start]+value[end:]
