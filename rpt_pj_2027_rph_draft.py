"""Draft-only PJ RPH builder from verified RPT rows; no database writes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class RPH:
    negeri: str
    tahun: int
    pdp: int
    tarikh: str
    tajuk: str
    sk: str
    sp: str
    muka_surat: str
    status: str
    set_induksi: str
    aktiviti_utama: str
    pengukuhan_penilaian: str
    penutup: str

def build_draft(row: dict) -> RPH:
    """Convert a single approved RPT mapping into an editable, non-generic scaffold."""
    required = ("Negeri", "Tahun", "PdP", "Tarikh", "Tajuk", "SK", "SP")
    missing = [key for key in required if not str(row.get(key, "")).strip()]
    if missing:
        raise ValueError("RPT belum lengkap: " + ", ".join(missing))
    year = int(row["Tahun"])
    pdp = int(row["PdP"])
    if year not in (4, 5, 6) or pdp not in range(1, (33 if year == 5 else 34) + 1):
        raise ValueError("Tahun atau PdP tidak sah")
    date.fromisoformat(str(row["Tarikh"]))
    tajuk = str(row["Tajuk"]).strip()
    page = str(row.get("M/S", "BELUM DISAHKAN")).strip() or "BELUM DISAHKAN"
    return RPH(
        negeri=str(row["Negeri"]).strip(), tahun=year, pdp=pdp,
        tarikh=str(row["Tarikh"]), tajuk=tajuk,
        sk=str(row["SK"]).strip(), sp=str(row["SP"]).strip(),
        muka_surat=page, status="DRAF — SEMAK GURU",
        set_induksi=f"Guru menunjukkan situasi/pergerakan berkaitan {tajuk}; murid menerangkan pemerhatian dan aspek keselamatan.",
        aktiviti_utama=f"1. Guru mendemonstrasi kemahiran {tajuk} secara berperingkat. 2. Murid berlatih dalam kumpulan kecil dengan bimbingan dan langkah keselamatan. 3. Guru memberi maklum balas mengikut SP.",
        pengukuhan_penilaian="Murid menunjukkan semula kemahiran; guru merekod pemerhatian berdasarkan SP dan memberi pemulihan/pengayaan.",
        penutup="Murid membuat regangan, menyatakan kemahiran dipelajari dan mengemas peralatan bersama guru.",
    )
