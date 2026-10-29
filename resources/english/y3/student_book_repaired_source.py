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
