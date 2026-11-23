"""Read-only premium DLP/PPKI Word geometry and field verification.

This is also used by tests: tests must not mistake the new header
for the curriculum table, or silently accept a return to the old layout.
"""
from __future__ import annotations

import re


def premium_rph_details(document):
    """Return fields of a 4-table DLP/PPKI Word plan without duplicating labels."""
    tables = document.tables
    if len(tables) != 4:
        raise AssertionError(f"Expected 4 premium RPH tables, got {len(tables)}")
    header, details, activity, reflection = tables
    if len(header.columns) != 2:
        raise AssertionError("Premium header must contain exactly two outer panels")
    widths = [column.width.mm for column in header.columns]
    if not 117 <= widths[0] <= 119 or not 63 <= widths[1] <= 65:
        raise AssertionError(f"Identity-left / teacher-right geometry changed: {widths}")
    for table in tables:
        total = sum(column.width.mm for column in table.columns)
        if abs(total - 182) > 1:
            raise AssertionError(f"RPH outer table width not aligned: {total}")
    fields = {row.cells[0].text: row.cells[1].text for row in details.rows}
    for para in header.cell(0, 1).paragraphs:
        if ": " in para.text:
            label, value = para.text.split(": ", 1)
            fields[label] = value.strip("\t ")
        elif para.text.endswith(":"):
            fields[para.text[:-1]] = ""
    identity = header.cell(0, 0)
    if len(identity.paragraphs) < 3:
        raise AssertionError("Lesson identity lost subject, year or topic")
    # New approved layout: the true RPH heading is centred OUTSIDE the
    # header grid; its left panel contains exact source Subject, Year, Topic
    # with aligned label/value tab stops. Preserve the legacy readback as a
    # fail-safe for older teacher downloads.
    new_fields = [p.text.split(": ", 1) for p in identity.paragraphs]
    if (len(new_fields) == 3 and all(len(x) == 2 for x in new_fields)
            and new_fields[0][0] in ("Subject", "Mata Pelajaran")
            and new_fields[1][0] in ("Year", "Tahun/Tingkatan")
            and new_fields[2][0] in ("Topic", "Tajuk")):
        fields.update((label, value.strip("\t ")) for label, value in new_fields)
    else:
        external_title = (document.paragraphs[0].text.strip().casefold()
                          if document.paragraphs else "")
        english = (identity.paragraphs[0].text.casefold() == "daily lesson plan"
                   or external_title == "daily lesson plan")
        fields["Topic" if english else "Tajuk"] = identity.paragraphs[2].text
        match = re.search(r"\b(?:Year|Tahun) [1-6]\b", identity.paragraphs[1].text)
        if match:
            fields["Year" if english else "Tahun/Tingkatan"] = match.group(0)
        if external_title in ("daily lesson plan", "rancangan pengajaran harian"):
            fields["Subject" if english else "Mata Pelajaran"] = identity.paragraphs[0].text
    # The name of the subject appears in the identity panel, not in the
    # curriculum/standards rows. No duplicate subject or teacher metadata.
    forbidden = {"subject", "mata pelajaran", "date", "tarikh", "time", "masa",
                 "class", "kelas", "number of pupils", "bilangan murid"}
    if any(label.casefold().strip() in forbidden for label in
           (row.cells[0].text for row in details.rows)):
        raise AssertionError("Repeated subject or teacher field in curriculum table")
    return fields
