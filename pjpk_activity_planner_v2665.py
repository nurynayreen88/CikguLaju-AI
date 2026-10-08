"""PJPK activity planner v26.65. Pure, opt-in, no database writes.
Only accepts standards supplied by the verified RPT bridge.
"""
import re

def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def build_pjpk_activities(selection):
    """Return four concrete activity phases, or None when mapping is unverified."""
    if not isinstance(selection, dict):
        return None
    subject = _clean(selection.get("subject") or selection.get("subject_name"))
    if subject not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
        return None
    if not selection.get("_pjpk_standards_complete_v2659"):
        return None
    topic = _clean(selection.get("topic") or selection.get("topic_title"))
    sk = _clean(selection.get("sk_text"))
    sp = _clean(selection.get("sp_text"))
    if not all((topic, sk, sp, _clean(selection.get("sk_code")), _clean(selection.get("sp_code")))):
        return None
    year = _clean(selection.get("year_label") or selection.get("year"))
    if year.isdigit():
        year = "Tahun " + year
    if year not in {"Tahun 1", "Tahun 2", "Tahun 3", "Tahun 4", "Tahun 5", "Tahun 6"}:
        return None
    if subject == "Pendidikan Jasmani":
        return [
            ("Set Induksi", f"Guru menunjukkan demonstrasi ringkas berkaitan {topic}; murid menyatakan peraturan keselamatan dan ruang pergerakan."),
            ("Aktiviti 1 – Demonstrasi dan latihan", f"Guru memodelkan kemahiran: {sp}. Murid memerhati titik teknik penting dan mencuba secara individu dengan bimbingan."),
            ("Aktiviti 2 – Aplikasi berpasangan", f"Murid melakukan tugasan {topic} secara berpasangan atau stesen; rakan memberikan maklum balas berdasarkan teknik yang ditunjukkan. Guru membetulkan postur dan memastikan keselamatan."),
            ("Pengukuhan, Pentaksiran dan Penutup", f"Murid menunjukkan semula kemahiran {topic}; guru menilai pelaksanaan berdasarkan {sp}, memberi pemulihan atau cabaran mengikut penguasaan, kemudian menjalankan aktiviti menyejukkan badan."),
        ]
    return [
        ("Set Induksi", f"Guru memperkenalkan situasi harian berkaitan {topic}; murid berkongsi pengetahuan awal tanpa mendedahkan maklumat peribadi."),
        ("Aktiviti 1 – Kenal pasti dan fahami", f"Guru membimbing murid meneliti situasi atau kad kes untuk mengenal pasti prinsip {topic}, berpandukan hasil pembelajaran: {sp}."),
        ("Aktiviti 2 – Aplikasi dan keputusan", f"Secara kumpulan kecil, murid membincangkan pilihan tindakan bagi situasi {topic}, memberikan alasan, dan melakonkan respons yang selamat dan sesuai."),
        ("Pengukuhan, Pentaksiran dan Penutup", f"Murid melengkapkan tiket keluar: satu tindakan tepat serta alasannya berkaitan {topic}. Guru menyemak kefahaman terhadap {sp} dan merumuskan amalan yang boleh digunakan."),
    ]

def format_pjpk_activities(selection):
    """Plain text suitable for existing RPH layout; caller controls pagination."""
    phases = build_pjpk_activities(selection)
    if phases is None:
        return None
    return "\n".join(f"{heading}\n{description}" for heading, description in phases)
