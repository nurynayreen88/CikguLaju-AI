"""Batch RPH Tahun 5 PJ: topic-specific editable drafts, never READY.

All SK/SP and topics are read from the staged source snapshot. Suggested
activities are teaching designs, NOT verified quotations from textbook.
"""
import re
from rpt_pj_2027_year5_source_snapshot import RECORDS

def _extract(source, label, next_label=None):
    pattern = r"\\b" + label + r"\\s+(.+?)" + (r"\\s*\\|\\s*" if next_label is None else r"\\s*\\|\\s*"+next_label)
    m = re.search(pattern, source, re.I)
    return m.group(1).strip() if m else ""

def _lesson_plan(title):
    t = title.upper()
    if any(k in t for k in ("IMBANG", "BINAAN", "TERBALIK")):
        return ("Tunjuk kedudukan tapak sokongan dan imbangan aras rendah.",
                "Latihan berpasangan di atas tikar: kawal pusat graviti, kekalkan posisi dan bertukar peranan dengan pengawasan.",
                "Pemerhatian kestabilan badan, keselamatan sokongan dan komunikasi pasangan.")
    if any(k in t for k in ("LOMBOL", "HAMBUR", "LOMPAT", "GULING", "GAYUT", "AYUN")):
        return ("Guru menunjukkan fasa mula, perlakuan dan pendaratan/penamatan selamat.",
                "Murid berlatih progresi kemahiran menggunakan alat rendah dan tikar; guru membetulkan teknik secara individu.",
                "Senarai semak koordinasi, kawalan badan dan pendaratan/penamatan terkawal.")
    if any(k in t for k in ("LAUTAN", "KE SANA", "KE SINI")):
        return ("Guru memperkenalkan rangsangan pergerakan kreatif bertema lautan.",
                "Murid membina rangkaian gerak mengikut aras, arah, tempo dan ruang dalam kumpulan kecil.",
                "Persembahan ringkas dinilai dari kesinambungan dan kepelbagaian pergerakan.")
    if any(k in t for k in ("SERONOK", "KELECEK", "TAKEL", "JARING", "VOLI", "SMESY", "REJAM", "LIBAS", "SIAPA HANDAL")):
        return ("Demonstrasi ruang permainan, peranan dan peraturan keselamatan.",
                "Permainan kecil: berlatih hantaran/serangan/pertahanan mengikut kemahiran tajuk; tukar peranan selepas pusingan.",
                "Guru memerhati keputusan taktikal, teknik asas dan kerjasama.")
    if any(k in t for k in ("BALING", "PUKUL", "TANGKAP", "LONTAR", "LEMPAR")):
        return ("Tunjuk genggaman, kedudukan badan dan zon selamat peralatan.",
                "Stesen latihan sasaran dan pasangan: lakukan perlakuan tajuk secara terkawal dan catat ketepatan.",
                "Semak teknik, ketepatan serta disiplin keselamatan peralatan.")
    if any(k in t for k in ("LARI", "PECUT", "HALANGAN")):
        return ("Guru menunjukkan pemanasan dan teknik larian.",
                "Murid berlatih permulaan, rentak langkah dan laluan larian secara bergilir tanpa pertembungan.",
                "Pemerhatian postur, rentak dan pematuhan zon larian.")
    if any(k in t for k in ("IKATAN", "SIMPULAN", "KAYU", "TIMANG")):
        return ("Guru memperkenalkan bahan dan peraturan permainan warisan.",
                "Murid berlatih kemahiran permainan warisan dalam kumpulan, bergilir mengendalikan bahan dengan selamat.",
                "Murid menerangkan langkah permainan dan menunjukkan kemahiran dengan betul.")
    if any(k in t for k in ("CERGAS", "SIHAT", "SANTAI")):
        return ("Guru bertanya kaitan aktiviti fizikal dan kesihatan.",
                "Murid melakukan aktiviti kecergasan sederhana dan memantau respons badan mengikut kemampuan.",
                "Murid mencatat pemerhatian dan menyatakan cara aktiviti fizikal membantu kesihatan.")
    return ("Guru memperkenalkan kemahiran berdasarkan tajuk.",
            "Murid melaksanakan aktiviti berpandu dan latihan bertahap mengikut kemahiran.",
            "Guru menilai perlakuan melalui pemerhatian dan maklum balas.")

def build_year5_rph_batch():
    result = []
    for record in RECORDS:
        source = record["source"]
        chunks = [x.strip() for x in source.split("|")]
        title = chunks[1] if len(chunks) > 1 else ""
        sk = next((x[3:].strip() for x in chunks if x.startswith("SK ")), "")
        sp = next((x[3:].strip() for x in chunks if x.startswith("SP ")), "")
        page = next((x[4:].strip() for x in chunks if x.startswith("M/S ")), "BELUM DISAHKAN")
        if not title or not sk or not sp:
            raise ValueError("Incomplete source mapping for PdP %s" % record["pdp"])
        intro, practice, assessment = _lesson_plan(title)
        result.append({
            "tahun": 5, "pdp": record["pdp"], "tajuk": title,
            "sk": sk, "sp": sp, "muka_surat": page,
            "status": "DRAF — BELUM DISAHKAN",
            "objektif_cadangan": "Murid dapat menunjukkan kemahiran utama tajuk dengan kawalan dan langkah keselamatan.",
            "set_induksi": intro,
            "aktiviti_utama": practice,
            "pengukuhan_penilaian": assessment,
            "penutup": "Murid melakukan penyejukan badan dan menyatakan satu perkara dipelajari.",
            "bbm_cadangan": "Peralatan PJ sesuai kemahiran, penanda ruang dan senarai semak guru.",
            "refleksi": "___/___ murid mencapai objektif; tindakan susulan: __________.",
            "sumber_pemetaan": source,
        })
    if len(result) != 33 or {r["pdp"] for r in result} != set(range(1,34)):
        raise ValueError("Expected exactly 33 unique Year 5 drafts")
    return result
