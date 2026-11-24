"""Domain-specific *review proposals* for PI 2027 drafts.
Proposals are Malay explanatory notes for editor review, NEVER user-facing RPH,
never a substitute for DSKP, mushaf, book or Jawi validation.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from pi_quality_audit import ROOT, DOMAINS, COUNT, HELD

METHODS = {
    "al-Quran": (
        "Guru menunjukkan contoh bacaan daripada mushaf mengikut surah dan julat ayat SP (semak julat sebelum PdP). Murid mengikut bacaan secara talaqqi/musyafahah.",
        "Murid berlatih mengikut frasa pendek secara berpasangan; guru memberi maklum balas khusus kepada makhraj, sifat huruf dan hukum tajwid yang benar-benar terdapat pada petikan.",
        "Murid membaca petikan sasaran secara individu (tasmi'). Guru merekod penguasaan setiap murid menggunakan senarai semak dan mengulang bimbingan pada ayat yang belum lancar.",
    ),
    "Jawi": (
        "Guru memilih contoh perkataan atau ayat Jawi daripada halaman buku teks yang sudah disahkan selari dengan SP, kemudian membimbing murid mengecam pola huruf atau suku kata.",
        "Murid menyusun kad huruf/suku kata untuk membina contoh baharu dan menerangkan sebab susunan atau ejaannya, dengan bimbingan mengikut aras.",
        "Setiap murid membaca dan menulis sekurang-kurangnya dua contoh; guru menyemak padanan huruf, suku kata dan ejaan secara individu.",
    ),
    "Akidah": (
        "Guru mengemukakan dua pernyataan atau situasi yang merujuk tepat pada konsep dalam SP dan meminta murid mengenal pasti istilah yang betul.",
        "Murid bekerja berpasangan untuk menerangkan maksud istilah serta menghubungkannya dengan contoh yang sesuai; guru membetulkan salah faham berasaskan buku teks.",
        "Murid menjawab satu situasi baharu secara individu dan memberikan alasan ringkas; guru menilai ketepatan konsep dan alasan.",
    ),
    "Ibadah": (
        "Guru memperkenalkan situasi amalan yang berkaitan tepat dengan SP; murid mengenal pasti syarat, tertib atau hukum yang relevan daripada sumber disahkan.",
        "Guru menunjukkan prosedur menggunakan bahan simulasi yang sesuai, kemudian murid mempraktik atau menyusun urutan langkah dalam kumpulan mengikut kesesuaian tajuk.",
        "Murid menerangkan atau menunjukkan kaedah yang tepat secara individu; guru menyemak menggunakan kriteria langkah, tertib dan sebab.",
    ),
    "Sirah": (
        "Guru membaca atau menunjukkan petikan peristiwa daripada buku teks yang telah disahkan dan menyoal urutan serta watak yang disebut dalam SP.",
        "Murid membina garis masa atau peta cerita daripada petikan, kemudian menyemak ketepatan fakta dengan pasangan dan guru.",
        "Murid menceritakan semula peristiwa dan mengenal pasti pengajaran yang benar-benar disokong oleh sumber; guru menilai fakta dan huraian.",
    ),
    "Adab": (
        "Guru memperlihatkan dua contoh situasi harian yang mengandungi amalan selari atau tidak selari dengan adab yang dinyatakan dalam SP.",
        "Murid membandingkan tindakan, memberi alasan dan menjalankan lakonan ringkas dengan tindakan yang betul.",
        "Murid memilih tindak balas kepada situasi individu; guru menggunakan senarai semak untuk menilai penjelasan dan aplikasi adab, bukan hafalan semata-mata.",
    ),
    "Hadis": (
        "Guru merujuk teks hadis dan maksud yang disahkan dalam buku teks sebelum membimbing bacaan serta pengenalan istilah utama.",
        "Murid membaca dan menerangkan maksud berdasarkan teks sebenar; guru tidak menambah matan atau terjemahan yang tiada dalam sumber.",
        "Murid mengaitkan pengajaran hadis dengan satu situasi harian dan menerangkan tindakan yang sesuai; guru menilai bacaan, makna dan aplikasi.",
    ),
}


def generate(root=ROOT):
    proposals = []
    for year in COUNT:
        data = json.loads((Path(root) / f"year{year}.json").read_text(encoding="utf-8"))
        for r in data["records"]:
            key = (year, r["lesson"])
            if key in HELD:
                continue
            heading = " ".join(r.get("intro", []))
            match = re.search(r"Bidang:\s*([^\s•]+)", heading)
            domain = DOMAINS.get(match.group(1)) if match else None
            if domain not in METHODS:
                raise ValueError(f"Unexpected domain for {r['id']}")
            fields = r["fields"]
            proposals.append({
                "id": r["id"],
                "year": year,
                "lesson": r["lesson"],
                "domain": domain,
                "source_sp_jawi": fields["sp"],
                "source_objective_jawi": fields["objektif"],
                "existing_activity_jawi": fields["aktiviti_utama"],
                "proposed_teacher_actions_rumi": list(METHODS[domain]),
                "assessment_to_verify": "Semak kriteria PBD khusus berdasarkan objektif dan contoh sumber; rekod pencapaian murid secara individu.",
                "approval": "BELUM_DIUJI_BELUM_DILULUSKAN",
                "note": "DRAF editorial; contoh dan halaman mesti disahkan pada DSKP/buku teks/mushaf. Terjemah dan semak Jawi sebelum dimasukkan ke RPH; jangan terbit automatik.",
            })
    if len(proposals) != 690:
        raise ValueError("Incomplete editor proposal queue")
    return proposals


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    Path(args.output).write_text(json.dumps({
        "status": "EDITORIAL_DRAFT_ONLY", "ready": False,
        "count": 690, "proposals": generate()
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("690 editorial suggestions generated; zero approvals; six held excluded")
