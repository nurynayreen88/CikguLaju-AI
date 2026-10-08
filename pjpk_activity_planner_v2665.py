"""PJPK v26.68: topic-sensitive, verified SK/SP anchored activity planner.

Read-only pure functions. Does not infer textbook pages, standards or lesson IDs.
"""
import re

def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

PJ_DOMAINS = (
    (("imbangan", "keseimbangan", "gimnastik"), ("laluan imbangan bertanda", "mengekalkan kedudukan badan dan mendarat secara terkawal")),
    (("baling", "lontar", "tangkap", "hantar", "bola"), ("stesen baling dan tangkap menggunakan bola lembut", "arah sasaran, koordinasi tangan-mata dan jarak selamat")),
    (("lari", "pecut", "lompat", "olahraga"), ("laluan kon dan penanda jarak", "teknik pergerakan, ruang dan pendaratan selamat")),
    (("tarian", "irama", "pergerakan kreatif"), ("rangkaian pergerakan mengikut kiraan", "turutan, irama dan koordinasi")),
    (("regangan", "kecergasan", "daya tahan"), ("litar kecergasan mengikut kemampuan", "teknik senaman dan pemantauan tahap keletihan")),
)
PK_DOMAINS = (
    (("pemakanan", "makanan", "nutrisi"), ("kad menu harian", "memilih pilihan makanan dan menjelaskan sebabnya")),
    (("kebersihan", "penjagaan diri", "gigi", "tangan"), ("kad urutan amalan kebersihan", "menyusun langkah penjagaan diri yang betul")),
    (("emosi", "perasaan", "stres", "mental"), ("kad situasi emosi", "mengenal pasti emosi dan memilih strategi mengurusnya")),
    (("keselamatan", "sentuhan", "bahaya", "kecemasan"), ("kad situasi keselamatan", "mengenal pasti risiko, tindakan selamat dan orang dewasa dipercayai")),
    (("penyakit", "jangkitan", "pencegahan"), ("kad situasi pencegahan penyakit", "membezakan amalan yang mengurangkan risiko jangkitan")),
)

def _focus(topic, sp, subject):
    s = (topic + " " + sp).casefold()
    domains = PJ_DOMAINS if subject == "Pendidikan Jasmani" else PK_DOMAINS
    for keywords, pair in domains:
        if any(word in s for word in keywords):
            return pair
    if subject == "Pendidikan Jasmani":
        return ("stesen kemahiran dengan ruang dan peralatan yang sesuai", "teknik pergerakan dan keselamatan")
    return ("kad situasi kehidupan seharian", "memilih tindakan sihat serta memberikan alasan")

def build_pjpk_activities(selection):
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
    material, focus = _focus(topic, sp, subject)
    if subject == "Pendidikan Jasmani":
        return [
            ("Set Induksi", f"Guru memperkenalkan {topic} melalui demonstrasi ringkas, menyemak ruang aktiviti dan menerangkan peraturan keselamatan."),
            ("Aktiviti 1 – Tunjuk cara dan latihan", f"Guru menunjukkan pelaksanaan {sp}. Murid mencuba kemahiran secara berperingkat menggunakan {material}; guru memberi pembetulan segera tentang {focus}."),
            ("Aktiviti 2 – Aplikasi kemahiran", f"Murid bergilir menjalankan {material} secara berpasangan atau kumpulan kecil. Rakan memerhati {focus} menggunakan senarai semak mudah; murid mengulangi cubaan selepas maklum balas."),
            ("Pengukuhan, Pentaksiran dan Penutup", f"Murid mempersembahkan kemahiran {topic}; guru merekod pemerhatian terhadap {sp}, memberi latihan sokongan atau cabaran sesuai, diikuti aktiviti menyejukkan badan."),
        ]
    return [
        ("Set Induksi", f"Guru memperkenalkan situasi berkaitan {topic} dan mengaktifkan pengetahuan awal murid tanpa meminta pendedahan maklumat peribadi."),
        ("Aktiviti 1 – Teroka situasi", f"Murid meneliti {material}; guru membimbing murid mengenal pasti fakta penting bagi {sp} dan membetulkan salah faham."),
        ("Aktiviti 2 – Buat keputusan", f"Dalam kumpulan kecil, murid menggunakan {material} untuk {focus}, kemudian membentangkan alasan dan menilai pilihan tindakan secara hormat."),
        ("Pengukuhan, Pentaksiran dan Penutup", f"Murid menjawab satu soalan aplikasi tentang {topic}; guru menilai kefahaman berdasarkan {sp}, menyediakan bimbingan susulan dan merumuskan amalan yang betul."),
    ]

def format_pjpk_activities(selection):
    phases = build_pjpk_activities(selection)
    if phases is None:
        return None
    return "\n".join(f"{heading}\n{description}" for heading, description in phases)
