"""Authoritative repaired Get Smart Plus 3 Student's Book source.

This 135-page PDF replaces the incomplete/duplicated older Y3 SB source.
Page numbers in approved standalone RPH must be preserved as written.
Do not apply a global +1/-1 offset.
The Drive file must be accessible to the bot's configured credentials before
using it for PDF-page extraction or Telegram download delivery.
"""
YEAR3_SB_DRIVE_FILE_ID = "1buPmX2jFFEboBp-_whSt9vhRGkuR-HP2"
YEAR3_SB_FILENAME = "Get_Smart_Plus_3_Students_Book_REPAIRED_135p.pdf"
YEAR3_SB_PAGE_COUNT = 135
YEAR3_SB_SOURCE = "google_drive"
YEAR3_SB_REPLACES = (
    "books/english/y3_student_001_060.pdf",
    "books/english/y3_student_061_120.pdf",
    "books/english/y3_student_121_136.pdf",
)

# Printed pages in the Materials / References column of the Primary Year 3
# SK Scheme of Work for the 36 Lessons in paired sessions. Inspected in the
# repaired PDF, where each printed number is also its physical page number.
YEAR3_SB_PAIRED_PAGES = {
    1: (5,), 2: (5,),
    6: (7,), 7: (7,),
    13: (11,), 14: (11,),
    17: (15,), 18: (15,),
    22: (17,), 23: (17,),
    33: (25,), 34: (25,),
    38: (27,), 39: (27,),
    49: (35,), 50: (35,),
    54: (37,), 55: (37,),
    65: (45,), 66: (45, 47),
    70: (47,), 71: (47,),
    81: (55,), 82: (55,),
    86: (57,), 87: (57,),
    91: (59,), 92: (59,),
    102: (67,), 103: (67,),
    113: (75,), 114: (75,),
    118: (77,), 119: (77,),
    145: (95,), 146: (95,),
}
