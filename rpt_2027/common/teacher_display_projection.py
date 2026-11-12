"""Presentation-only protection against internal RPT audit text in PDF tables.

Original sourced rows and provenance are NEVER mutated. The returned strings are
for staging review PDFs only; they do NOT certify DSKP, textbook, calendar or RPH
accuracy. Releasing a PDF to teachers requires separate academic signoff.
"""
from __future__ import annotations
import re

# The unit is a text clause, not a word: dropping a contaminated clause avoids
# leaving a dangling imperative such as "rujuk DSKP sebelum READY".
_INTERNAL = re.compile(
    r"(?i)"
    r"\b(?:DRAF(?=\s*[:/_—–-]|\s+(?:SEMAK(?:AN)?|TERKAWAL|UNTUK\s+SEMAKAN))|STAGING|HOLD(?=\s*:)|SEBELUM\s+READY|PRA[\s-]?READY|PRE[\s-]?READY|"
    r"REKOD DITAHAN|PENGESAHAN (?:GURU|INSTRUMEN)|"
    r"BELUM (?:DISAH(?:KAN)?|DISEMAK|DIPADANKAN|DIPERUNTUKKAN)|"
    r"KELULUSAN GURU|SEMAK TAJUK PENUH|"
    r"CALON TEKS DIGITAL|PADANAN TEKS DIGITAL|"
    r"RUJUK BUKU DAN DSKP SEBELUM READY|"
    r"RPH V5 ASAL TIDAK LENGKAP|KOD DIS[AE]MAK|"
    r"BUKAN UNTUK GURU|BUKAN (?:SEMAKAN|HALAMAN AKTIVITI)|"
    r"JANGAN (?:MERGE|DEPLOY|ANJAK AUTOMATIK)|"
    r"BELUM LULUS|BELUM SELESAI|BELUM DIBUAT|"
    r"SEMAKAN KURIKULUM|SEMAKAN DSKP DIPERLUKAN|CALON PEMBETULAN|CALON BUKAN VISUAL|MASIH DRAF|RPT MASIH DRAF|KONFLIK SUMBER|"
    r"BUKU TEKS.*?BELUM SAH|"
    r"TEKS.*?BELUM SAH|"
    r"TIADA JANAAN AUTOMATIK)\b"
)
# Some note fragments are internal even without a status word.
_AUDIT_CLAUSE = re.compile(
    r"(?i)(?:\b(?:SEMAK JUDUL AKTIVITI PENUH|JANGAN DAKWA KEDUA-DUANYA SETARA)\b|\bMain/Complementary codes from source SOW\b|\bSumber\s*:|\bRujukan\s*:\s*Rujuk\s+DSKP\b|\b(?:sumber|semakan)\s*:\s*(?:v\d|legacy|draft)|"
    r"\bRPT\s+2026\s+(?:salah|mengulangi)|"
    r"\b(?:TARIKH|MINGGU)\s+(?:A/B\s+)?(?:BELUM|(?:IALAH|ADALAH)\s+CADANGAN)|"
    r"\b(?:HALAMAN|AKTIVITI|BUKU|TEKS|KOD)\b.{0,80}\b(?:belum|draf|calon|sebelum READY)|"
    r"\b(?:Simbol\s*/\s*skor\s+tidak\s+penuh\s+dalam\s+teks|"
    r"Pengukuhan\s+pilihan,\s*bukan\s+projek\s+rasmi\s*;\s*DRAF)\b|"
    r"\b(?:audit|developer|release|signoff)\b)"
)
_SEPARATOR = re.compile(r"\s*(?:\s+[|•]\s+|(?<=[.!?])\s+)")
_ALTERNATIVE = re.compile(r"(?i)^(?:PROGRAM TASMI PILIHAN GURU|BACAAN TASMI / PBD)")


def is_internal(text: str) -> bool:
    return bool(_INTERNAL.search(text) or _AUDIT_CLAUSE.search(text))


def public_note(row: dict) -> str:
    """Keep pedagogical clauses, not their audit commentary.

    No note is shown for any held/unverified-standard source or known legacy
    Sains dataset: a clean-looking *note* cannot make those standards safe.
    Their original notes remain available for source checks.
    """
    if (row.get("source_held") or
        row.get("source_sp_dskp_text_signoff") is False or
        row.get("week_allocation") == "PROPOSED_2027_WEEK_NOT_TIMETABLE"):
        return ""
    source = str(row.get("note") or "")
    # Source crosswalk IDs belong in the audit ledger, never on a teacher RPT.
    source = re.sub(r"(?i)\bBM[2-6]-P\d{3}\b", "", source)
    source = re.sub(r"(?i)\bdalam\s+RPT\s+sumber\b", "", source)
    source = re.sub(r"[ \t]{2,}", " ", source)
    # Remove reviewer qualifiers without deleting genuine teaching/PBD guidance.
    # Do not change the source dict or its source_status fields.
    source = re.sub(r"(?i)\bPBD\s*\(draf\)\s*:", "PBD:", source)
    source = re.sub(r"(?i)\bPBD\s*\(sumber\)\s*:", "PBD:", source)
    source = re.sub(r"(?i)\bAktiviti\s*\(sumber\)\s*:", "Aktiviti:", source)
    source = re.sub(r"(?i)\s*\(bukan halaman aktiviti disahkan\)", "", source)
    # Never consume a trailing ' | Penilaian:' field on the same source line.
    # PI standalone source contains standalone developer-review lines in the
    # original Bahan field (Year 3 lessons 006/050 and Year 6 lesson 087).
    # Strip only those lines, preserving Mushaf, tasmi' and assessment text.
    source = re.sub(
        r"(?im)^[ \t]*(?:SEMAKAN KURIKULUM|SEMAKAN DSKP DIPERLUKAN)\s*:[^\r\n|]*",
        "", source,
    )
    source = re.sub(
        r"(?im)^[ \t]*Pemetaan buku teks terdahulu masih memerlukan "
        r"semakan visual; belum sahkan halaman\.?[ \t]*$", "", source,
    )
    # This is a developer instruction, not a teaching material. Keep the
    # original Mushaf/ayat reference and remove only the review qualifier.
    source = re.sub(r"(?i);\s*tidak mereka halaman buku teks\.?","",source)
    # Remove only explicitly editorial qualifiers. A genuine teaching step
    # such as "menulis draf karangan" is never changed or rejected.
    source = re.sub(r"(?i)\s*\(\s*draf\s*\)", "", source)
    # Split compound notes conservatively. Keep sourced PKJR activity/page
    # guidance while stripping the publisher-only "DRAF PKJR" prefix.
    safe = []
    for part in _SEPARATOR.split(source):
        part = part.strip(" ;,|")
        if re.match(r"(?i)^DRAF\s+PKJR\s*[:—–-]", part):
            part = re.sub(r"(?i)^DRAF\s+PKJR\s*[:—–-]\s*", "", part)
            part = re.sub(r"(?i)\s*[;,]\s*belum\s+READY\b\.?", "", part)
            part = part.strip(" ;,|")
        if part and part.casefold() != "draf" and not is_internal(part):
            safe.append(part)
    return re.sub(r"\.{2,}", ".", " | ".join(safe))


def public_standard(row: dict, field: str) -> str:
    """Keep original SK/SP identity if an expanded label is only a placeholder."""
    if field not in ("sk", "sp"):
        raise ValueError("Unsupported SK/SP field")
    source = str(row[field]).strip()
    expanded = str(row.get(field + "_display") or source).strip()
    if not source:
        raise ValueError("Empty original SK/SP")
    # Proposed tasmi/PBD sessions have no official SK/SP; say so in teacher
    # language without inventing a standard or exposing release-check jargon.
    if field == "sk" and re.search(r"(?i)BUKAN KOD SK RASMI", expanded):
        return "Aktiviti pilihan guru (tiada SK rasmi)"
    if field == "sp" and re.search(r"(?i)TIADA KOD SP RASMI", expanded):
        return "Aktiviti pilihan guru (tiada SP rasmi)"
    # Only a demonstrably absent official statement may fall back to its
    # original code. Words such as "menulis draf" are legitimate DSKP text.
    if re.search(r"(?i)pernyataan penuh\s+(?:SK|SP)\s+belum dipadankan", expanded):
        return source
    return expanded


def public_topic(row: dict) -> str:
    """Hide explicitly developer-only held-topic text, not the source record."""
    text = str(row.get("topic") or "").strip()
    if row.get("source_held") and is_internal(text):
        return ""
    return re.sub(r"(?i)\bBM[2-6]-P\d{3}\b", "", text).strip()


def public_lesson_identity(subject: str, row: dict) -> str:
    """Teacher-readable label; source crosswalk IDs remain unchanged."""
    internal = str(row.get("display_id") or "").strip()
    if subject == "sains" and re.fullmatch(r"SCI-Y[2-6]-PDP-\d{3}", internal):
        return f"PdP {row['id']}"
    return internal or f"PdP {row['id']}"
