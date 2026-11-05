#!/usr/bin/env python3
"""Revise all 270 educator-developed Moral supplementary RPH with SP-specific teaching tasks.

Safe, deterministic content refinement: ONLY phase lines in 54 supplementary
RPH per Year 2–6. No automatic source visual approval, release-status changes,
official SP rewrites, user databases, Telegram payments, or other subjects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT = ROOT / "rph_standalone/pendidikan_moral/pengukuhan"
AUDIT = ROOT / "audits/pendidikan_moral_supplement270_semantic_review_20261105.json"
YEARS = range(2, 7)

# Current-edition Year6 chapter scenes, NOT a claim that these are copied
# teaching instructions or certified visual page matches.
Y6_BOOK_CONTEXT = {
  1: "prinsip pertama Rukun Negara dan kepelbagaian kepercayaan dalam negara",
  2: "kempen kesedaran derma darah, sokongan kepada petugas dan peranan JKM",
  3: "tanggungjawab warganegara, maklumat sahih dan pengurusan e-waste",
  4: "keunikan masyarakat Baba dan Nyonya serta warisan budaya negara",
  5: "bahasa sopan, layanan berhemah dan imej rakyat Malaysia",
  6: "identiti kebangsaan, Jalur Gemilang dan penghormatan terhadap lambang negara",
  7: "pilihan melancong dalam negara dan menjaga nama baik Malaysia",
  8: "keadilan dalam perkhidmatan awam dan peranan institusi pengguna",
  9: "teguran yang berani, benar dan berhemah untuk menjaga maruah negara",
 10: "sikap jujur dan pantun kejujuran demi kesejahteraan negara",
 11: "usaha gigih rakyat serta suri teladan yang membawa kemajuan negara",
 12: "kerjasama komuniti dan tindakan selamat menjaga keharmonian negara",
 13: "amalan berjimat cermat air, kertas dan tenaga untuk kesejahteraan negara",
 14: "toleransi semasa perayaan dan perarakan serta penyediaan risalah perpaduan",
}

PHASES = ("Set induksi", "Aktiviti 1", "Aktiviti 2",
          "Pengukuhan/Pentaksiran PBD", "Penutup")
SOURCE_REGEX = re.compile(r"(?m)^\*\*SP:\*\* (.+?)\s*$")
UNIT_REGEX = re.compile(r"(?m)^\*\*Unit:\*\* (\d+)\.\s*(.+?)\s*$")
VALUE_REGEX = re.compile(r"(?m)^\*\*(?:Nilai|Tema/Nilai):\*\* (.+?)\s*$")
SCENE_REGEX = re.compile(r"(?i)situasi:?\s*\*\*([^*]+)\*\*")
STEP_REGEXES = {
    "Set induksi": re.compile(r"(?m)^\*\*Set induksi \(5 minit\):\*\* .+$"),
    "Aktiviti 1": re.compile(r"(?m)^\*\*Aktiviti 1 \(20 minit\) — [^\n]+$"),
    "Aktiviti 2": re.compile(r"(?m)^\*\*Aktiviti 2 \(20 minit\) — [^\n]+$"),
    "Pengukuhan/Pentaksiran PBD": re.compile(r"(?m)^\*\*Pengukuhan/Pentaksiran PBD \(10 minit\):\*\* .+$"),
    "Penutup": re.compile(r"(?m)^\*\*Penutup \(5 minit\):\*\* .+$"),
}


def one(pattern, source, description):
    result = list(pattern.finditer(source))
    if len(result) != 1:
        raise AssertionError(f"{description}: expected 1, got {len(result)}")
    return result[0]


def source_standard(line: str):
    parts = [x.strip() for x in line.split("|")]
    parsed = []
    for p in parts:
        m = re.fullmatch(r"(\d+\.\d+)\s*[—–-]\s*(.+?)\s*", p)
        if not m:
            raise AssertionError(f"Cannot parse SP: {p}")
        parsed.append((m[1], m[2].rstrip(".")))
    if not 1 <= len(parsed) <= 2:
        raise AssertionError(parsed)
    return parsed


def style_for(standards):
    codes = [code for code, _ in standards]
    if len(codes) == 2 and codes[0].endswith(".1") and codes[1].endswith(".2"):
        return "knowledge"
    assert len(codes) == 1, codes
    code = codes[0]
    return {".3": "reasoning", ".4": "emotion", ".5": "practice"}[code[-2:]]


def safe_scenario(s: str) -> str:
    return " ".join(s.strip().split()).rstrip(". ")


def new_steps(year: int, unit: int, scenario: str, standards, value: str):
    style = style_for(standards)
    topic = Y6_BOOK_CONTEXT[unit] if year == 6 else scenario[0].lower() + scenario[1:]
    codes = "; ".join(x[0] for x in standards)
    skill = standards[0][1].lower()
    # The in-class scenario is an educator adaptation; do not claim a visual
    # match to a textbook activity or require personal disclosures.
    intro = (
      f"Guru memaparkan kad kes: **{scenario}**. Murid meneliti siapa terlibat, "
      f"menyebut satu pilihan tindakan dan mengaitkannya dengan nilai **{value}**. "
      "Pengalaman peribadi tidak diperlukan."
    )
    if style == "knowledge":
        a, b = standards
        activity1 = (
          f"**Aktiviti 1 (20 minit) — Teliti situasi dan SP {a[0]}:** "
          f"Guru menggunakan dua variasi kes berkaitan **{topic}**. "
          f"Murid menghasilkan dua jawapan konkrit bagi tugasan **{a[1]}** "
          "dan menerangkan hubungannya dengan watak atau keperluan dalam situasi."
        )
        activity2 = (
          f"**Aktiviti 2 (20 minit) — Buktikan SP {b[0]}:** "
          f"Guru menyoal cara atau sebab pilihan dibuat. Murid menghasilkan kad respons "
          f"bagi **{b[1]}** dengan dua butiran khusus serta alasan yang sesuai dengan "
          f"kes **{scenario}**. Rakan menyemak ketepatan jawapan mengikut kata tugas SP."
        )
        pbd = (
          f"Guru menyemak kad individu: dua respons untuk SP {a[0]}, dua butiran dan "
          f"satu alasan tepat untuk SP {b[0]}. Murid membetulkan satu jawapan berdasarkan "
          "maklum balas; penilaian bukan berdasarkan hafalan semata-mata."
        )
    elif style == "reasoning":
        code, desc = standards[0]
        activity1 = (
          f"**Aktiviti 1 (20 minit) — Penaakulan SP {code}:** "
          f"Guru memperkenalkan dua hasil yang mungkin apabila **{scenario[0].lower()+scenario[1:]}**. "
          f"Murid menjalankan tugasan **{desc}** dengan mengenal pasti dua hubungan "
          "tindakan–sebab–kesan dan pihak yang menerima kesannya."
        )
        activity2 = (
          f"**Aktiviti 2 (20 minit) — Uji justifikasi:** "
          f"Guru membekalkan dua kad pilihan yang berbeza bagi **{topic}**. "
          "Murid memilih keputusan lebih wajar, membina peta sebab–kesan "
          "dan mempertahankannya dengan dua alasan. Rakan meminta satu pembaikan berasaskan SP."
        )
        pbd = (
          f"Guru menilai dua justifikasi individu yang menjawab SP {code}, "
          "kedua-duanya disokong hubungan sebab dan kesan yang munasabah. "
          "Murid membetulkan satu kaitan yang tidak tepat selepas ulasan guru."
        )
    elif style == "emotion":
        code, desc = standards[0]
        activity1 = (
          f"**Aktiviti 1 (20 minit) — Empati SP {code}:** "
          f"Guru memaparkan dua perspektif pihak terlibat dalam **{topic}**. "
          f"Murid melaksanakan tugasan **{desc}** menggunakan kad perasaan dan "
          "memilih respons yang berhemah tanpa mengaitkannya dengan keluarga sendiri."
        )
        activity2 = (
          f"**Aktiviti 2 (20 minit) — Dialog beralasan:** "
          f"Guru memberikan rangka ayat 'Saya berasa ... kerana ...'. "
          f"Murid membina dua dialog pendek yang berkaitan dengan kes **{scenario}**, "
          "membandingkan kesan kata-kata terhadap rakan dan menambah baik satu ayat."
        )
        pbd = (
          f"Guru menyemak dua perasaan yang bertepatan dengan SP {code} "
          "bersama sekurang-kurangnya satu alasan jelas dalam respons individu. "
          "Tiada markah berdasarkan pendedahan pengalaman atau pegangan peribadi."
        )
    else:
        code, desc = standards[0]
        activity1 = (
          f"**Aktiviti 1 (20 minit) — Tindakan SP {code}:** "
          f"Guru menyediakan lakonan ringkas daripada kes **{scenario}**. "
          f"Murid memperagakan dua langkah yang bersesuaian untuk **{desc}**, "
          "tanpa memerlukan wang, data peribadi atau aktiviti luar kelas."
        )
        activity2 = (
          f"**Aktiviti 2 (20 minit) — Simulasi dan penambahbaikan:** "
          f"Guru memandu pemerhati menggunakan senarai semak nilai **{value}**. "
          f"Murid menunjukkan satu perlakuan kedua apabila keadaan kes berubah, "
          "menerima komen rakan dan memperbaiki satu tindakan yang dapat dilihat."
        )
        pbd = (
          f"Guru merekod dua tindakan yang benar-benar diperagakan untuk SP {code}, "
          "satu sebab tindakan dan satu refleksi pembaikan. "
          "Simulasi di kelas tidak dianggap bukti amalan harian di luar sekolah."
        )
    return {
       "Set induksi": f"**Set induksi (5 minit):** {intro}",
       "Aktiviti 1": activity1,
       "Aktiviti 2": activity2,
       "Pengukuhan/Pentaksiran PBD": f"**Pengukuhan/Pentaksiran PBD (10 minit):** {pbd}",
       "Penutup": (
         f"**Penutup (5 minit):** Murid menyatakan satu keputusan atau perlakuan yang "
         f"menunjukkan nilai **{value}** dalam konteks **{topic}** serta sebab pilihan itu. "
         f"Guru merumuskan SP {codes} dan tindakan selamat yang boleh dipraktikkan."
       ),
    }, style


def transform(path: Path):
    old = path.read_text(encoding="utf-8")
    y = int(path.parent.name.removeprefix("year"))
    number = int(path.stem.removeprefix("sesi_"))
    match_unit = one(UNIT_REGEX, old, path.name + " unit")
    unit = int(match_unit[1])
    value = one(VALUE_REGEX, old, path.name + " nilai")[1].strip()
    standards = source_standard(one(SOURCE_REGEX, old, path.name + " SP")[1])
    intro = one(STEP_REGEXES["Set induksi"], old, path.name + " induction")[0]
    original_scenario = one(SCENE_REGEX, intro, path.name + " scene")[1]
    scenario = safe_scenario(original_scenario)
    assert len(scenario) >= 15 and 1 <= unit <= 14
    replacements, kind = new_steps(y, unit, scenario, standards, value)
    new = old
    for name in PHASES:
        match = one(STEP_REGEXES[name], new, path.name + " " + name)
        new = new[:match.start()] + replacements[name] + new[match.end():]
    assert "STATUS" in new and "STATUS" in old
    if y == 6:
        assert ("Padanan edisi Semakan 2017" in new or "Bukti aktiviti Semakan 2017" in new), path
        assert ("Batasan sumber" in new or "Batasan sumber:" in new or "Batasan sumber" in old), path
    for code, desc in standards:
        assert code in new and desc in new, (path, code)
    assert len(new) > 1800 and all(one(STEP_REGEXES[name], new, name) for name in PHASES)
    assert "siapa memerlukan apa" not in new, path
    # Record the evidence class accurately: teacher-developed based on SP and
    # an existing book unit, NOT individual visual verification of textbook.
    row = {
       "year": y, "session": number, "unit": unit, "sp": [x[0] for x in standards],
       "approach": kind, "scenario": scenario,
       "evidence_scope": "DSKP_SP_AND_TEACHER_DEVELOPED_CLASSROOM_SCENE_NOT_VISUAL_BOOK_ACTIVITY",
       "source_sha256_16": hashlib.sha256(old.encode()).hexdigest()[:16],
       "new_sha256_16": hashlib.sha256(new.encode()).hexdigest()[:16],
    }
    return old, new, row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    paths = sorted(SUPPLEMENT.glob("year*/sesi_*.md"))
    assert len(paths) == 270, len(paths)
    changes, ledger = [], []
    for path in paths:
        old, new, record = transform(path)
        assert old != new, path
        changes.append((path, new))
        ledger.append(record)
    assert Counter(x["year"] for x in ledger) == {2:54, 3:54, 4:54, 5:54, 6:54}
    assert len({(x["year"], x["session"]) for x in ledger}) == 270
    assert all(x["source_sha256_16"] != x["new_sha256_16"] for x in ledger)
    if args.apply:
        for path, new in changes:
            path.write_text(new, encoding="utf-8")
        AUDIT.write_text(json.dumps({
          "date":"2026-11-05", "scope":"Individual SP-aligned pedagogy edits, not 2021 textbook activity visual proof",
          "results":ledger,
          "final_ready":False,
          "visual_activity_approval":False,
          "telegram_teacher_end_to_end":False,
          "notes":["All 270 educator-developed supplementary lessons rewritten at phase level.",
                   "Official SP, source provenance, release status and original teaching metadata unchanged.",
                   "No user databases, quotas, payment or runtime changed."],
        }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
       "count":len(ledger), "years":dict(Counter(x["year"] for x in ledger)),
       "approaches":dict(Counter(x["approach"] for x in ledger)),
       "apply":args.apply, "semantic_only":True,
    }, ensure_ascii=False))


if __name__=="__main__":
    main()
