"""Read-only bridge to the existing Telegram English Year 2/3 RPH row adapters.

No HTTP endpoint, no document download, no credit debit. This preserves the
production row selection and fallback behavior without importing app.py.
"""
from english_y2_standalone_render import apply as apply_y2
from english_y3_standalone_render import apply as apply_y3


def apply_telegram_english_rows(year, lesson_no, base_rows):
    """Return the same English standalone row overlays used by Telegram.

    Caller must provide genuine base rows from the Telegram curriculum engine;
    this function does not fabricate curriculum metadata or bypass access checks.
    Year 1 and other years return base rows unchanged until a matching production
    adapter has been identified and verified.
    """
    if type(year) is not int or type(lesson_no) is not int:
        raise ValueError('year and lesson_no must be integers')
    if year not in range(1, 7) or not 1 <= lesson_no <= 160:
        raise ValueError('invalid year or lesson number')
    if not isinstance(base_rows, dict):
        raise TypeError('base_rows must be a dictionary')
    st = {'year': f'Tahun {year}', 'subject': 'English', 'lesson_no': lesson_no}
    if year == 2:
        return apply_y2(st, base_rows)
    if year == 3:
        return apply_y3(st, base_rows)
    return dict(base_rows)
