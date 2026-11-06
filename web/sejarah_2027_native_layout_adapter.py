"""Staging-only Sejarah 2027 adapter to the *existing* Telegram native RPH layout.

Internal preview constructs the proposed RPH layout for offline tests. Public
payload creation MUST obtain an independently approved source via lesson().
No document generation, payment, user DB or live endpoint is defined here.
"""
from __future__ import annotations

from datetime import date
from web.sejarah_2027_staging_source import lesson, preview_only
from web.rph_shared_source_identity import source_fingerprint

def _teacher(teacher):
    if not isinstance(teacher, dict) or set(teacher) != {"class", "date", "time"}:
        raise ValueError("Teacher fields must be class/date/time")
    if any(not isinstance(x, str) or len(x)>60 for x in teacher.values()):
        raise ValueError("Invalid teacher field")
    return dict(teacher)

def _layout(row, teacher):
    """Only shapes a layout; it DOES NOT approve or export a draft."""
    t=_teacher(teacher)
    r=row["rph"]
    y=r["year"]
    sp=", ".join(r["sp_codes"])
    # Show the per-PdP *text reference*, not the broad unit contents range.
    # The cited pages have text-level crosswalk; no exercise/visual signoff
    # is implied, and the original lesson JSON/approval ledger is unchanged.
    focus=r["textbook_reference"]["checked_focus_pages"]["printed_page_range"]
    original_bbm=r["bbm"]
    if ", hlm. " not in original_bbm or not isinstance(focus,str) or not focus.strip():
        raise ValueError("Missing printed textbook page evidence")
    intro,separator,tail=original_bbm.partition(";")
    bbm=intro.split(", hlm. ",1)[0]+", fokus PdP hlm. "+focus+" (rujukan isi pelajaran)"
    if separator:
        bbm+=";"+tail
    date_str=t["date"]
    entered_date=date.fromisoformat(date_str) if date_str else None
    day=("Isnin","Selasa","Rabu","Khamis","Jumaat","Sabtu","Ahad")[
        entered_date.weekday()] if entered_date else ""
    header=[
        ("MATA PELAJARAN","Sejarah"),
        ("TAHUN/TINGKATAN","Tahun "+str(y)),
        ("TARIKH",entered_date.strftime("%d/%m/%Y") if entered_date else ""),
        ("HARI",day),
        ("MASA",t["time"]),
        ("KELAS",t["class"]),
        ("BILANGAN MURID",""),
        ("Tajuk",r["title"]),
        ("Standard Kandungan",r["sk"]+" — "+r["sk_title"]),
        ("Standard Pembelajaran",sp),
        ("OBJEKTIF PEMBELAJARAN","; ".join(r["objective"])),
        ("KRITERIA KEJAYAAN",r["success_criteria"]),
        ("PENGETAHUAN SEDIA ADA","Pengetahuan sedia ada murid tentang "+r["textbook_reference"]["unit_title"]),
        ("BAHAN BANTU MENGAJAR",r["bbm"]),
        ("EMK / NILAI","; ".join(x["text"] for x in r["values_sp"]) or "Patriotisme; hormat"),
        ("KBAT / PAK21","Kemahiran Pemikiran Sejarah; menilai bukti dan membuat inferens"),
        ("PENTAKSIRAN",r["pengukuhan_pbd"]["activity"]),
    ]
    phases=[
        {"label":"Set Induksi (5 min)","activity":r["set_induksi"]["activity"],"notes":"BBM / soal jawab"},
        {"label":"Aktiviti Utama (50 min)","activity":"Aktiviti 1 (20 min) — "+r["aktiviti_1"]["activity"]+"\nAktiviti 2 (20 min) — "+r["aktiviti_2"]["activity"]+"\nPengukuhan dan PBD (10 min) — "+r["pengukuhan_pbd"]["activity"],"notes":"Pentaksiran formatif mengikut SP"},
        {"label":"Penutup (5 min)","activity":r["penutup"]["activity"],"notes":"Rumusan dan iktibar"},
    ]
    footer=[
        {"label":"Pemulihan / Pengayaan","value":"Guru bimbing murid yang belum mencapai kriteria; murid menguasai meluaskan bukti sejarah."},
        {"label":"Refleksi","value":r["reflection"]},
    ]
    return {
        "style":"telegram-native-rph-v1",
        "header":[{"label":k,"value":v} for k,v in header],
        "activity_header":["Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"],
        "phases":phases,"footer":footer,
    }

def internal_preview_layout(year,pdp,teacher):
    """Read-only INTERNAL QA layout: never returned through a public endpoint."""
    row=preview_only(year,pdp)
    return _layout(row,teacher)

def approved_native_payload(year,pdp,teacher,fmt):
    """Fail closed until teacher, textbook and parity checks all pass in lesson()."""
    if fmt not in ("word","pdf"):
        raise ValueError("Unsupported format")
    row=lesson(year,pdp)
    r=row["rph"]
    digest=source_fingerprint(year,"SEJARAH",pdp)
    if digest is None or not isinstance(digest,str) or len(digest)!=64:
        raise ValueError("Sejarah source identity unavailable")
    return {
        "subject":"SEJARAH", "component":None,"year":year,"lesson":pdp,
        "unit":r["textbook_reference"]["unit_title"],
        "teacher":_teacher(teacher),"layout":_layout(row,teacher),
        "format":fmt,"source_digest":digest,
    }
