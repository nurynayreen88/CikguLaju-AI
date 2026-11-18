"""KPM school closures and public holidays for the Web timetable."""

from web.school_days_2027 import FRI_SAT, STATE_LABELS

_ALL = frozenset(STATE_LABELS.values())
_GROUP_B = _ALL - FRI_SAT
_WILAYAH = frozenset(("Kuala Lumpur", "Putrajaya", "Labuan"))
_PENINSULA = _ALL - {"Sabah", "Sarawak", "Labuan"}
_THAIPUSAM = frozenset(("Kuala Lumpur", "Putrajaya", "Johor", "Negeri Sembilan", "Perak",
                       "Pulau Pinang", "Selangor"))
_NEW_YEAR = _ALL - {"Johor", "Kedah", "Kelantan", "Perlis", "Terengganu"}
_KELANTAN_TERENGGANU = frozenset(("Kelantan", "Terengganu"))
_AIDILADHA_STATE = frozenset(("Kedah", "Perlis"))
_ISRAK = frozenset(("Kedah", "Negeri Sembilan", "Perlis", "Terengganu"))
_KAAMATAN = frozenset(("Sabah", "Labuan"))
_DEEPAVALI = _ALL - {"Sarawak"}
_NUZUL_2026 = _WILAYAH | {"Kelantan", "Negeri Sembilan", "Pahang", "Perak", "Perlis",
                         "Sarawak", "Selangor", "Terengganu"}
_NUZUL_2027 = _WILAYAH | {"Kelantan", "Pahang", "Perak", "Perlis", "Pulau Pinang",
                         "Selangor", "Terengganu"}

# BKPP JPM, combined federal/state tables and subsequent notices.
# https://www.kabinet.gov.my/storage/2025/08/HKA-2026.pdf
# https://www.kabinet.gov.my/storage/2026/08/HKA_2027.pdf
# https://www.kabinet.gov.my/akta-dan-warta/
# The 2026 Kedah birthday moved to 5 July (state letter dated 6 May).
# The 2026 one-off state holidays use the respective state announcements.
# Rows with two entries distinguish the federal or state scope of the same holiday.
_PUBLIC_DAYS = {
    2026: (
        ("01-01", "Tahun Baharu", _NEW_YEAR, "negeri"),
        ("01-14", "Hari Keputeraan Yang di-Pertuan Besar Negeri Sembilan", {"Negeri Sembilan"}, "negeri"),
        ("01-17", "Israk dan Mikraj", _ISRAK, "negeri"),
        ("02-01", "Hari Wilayah Persekutuan", _WILAYAH, "negeri"),
        ("02-01", "Thaipusam", _THAIPUSAM, "negeri"),
        ("02-17", "Tahun Baharu Cina", _ALL, "umum"),
        ("02-18", "Tahun Baharu Cina (Hari Kedua)", _ALL - _KELANTAN_TERENGGANU, "umum"),
        ("02-18", "Tahun Baharu Cina (Hari Kedua)", _KELANTAN_TERENGGANU, "negeri"),
        ("02-19", "Awal Ramadan", {"Johor", "Kedah"}, "negeri"),
        ("02-20", "Hari Pengisytiharan Tarikh Kemerdekaan", {"Melaka"}, "negeri"),
        ("03-04", "Hari Ulang Tahun Pertabalan Sultan Terengganu", {"Terengganu"}, "negeri"),
        ("03-07", "Nuzul Al-Quran", _NUZUL_2026, "negeri"),
        ("03-20", "Cuti tambahan Aidilfitri", _PENINSULA | {"Labuan"}, "umum"),
        ("03-21", "Hari Raya Aidilfitri", _ALL, "umum"),
        ("03-22", "Hari Raya Aidilfitri (Hari Kedua)", _ALL, "umum"),
        ("03-23", "Hari Keputeraan Sultan Johor", {"Johor"}, "negeri"),
        ("03-23", "Hari Raya Aidilfitri (Hari Ketiga)", {"Melaka"}, "negeri"),
        ("03-30", "Hari Jadi Yang di-Pertua Negeri Sabah", {"Sabah"}, "negeri"),
        ("04-03", "Good Friday", {"Sabah", "Sarawak"}, "negeri"),
        ("04-26", "Hari Keputeraan Sultan Terengganu", {"Terengganu"}, "negeri"),
        ("05-01", "Hari Pekerja", _ALL, "umum"),
        ("05-17", "Hari Keputeraan Raja Perlis", {"Perlis"}, "negeri"),
        ("05-22", "Hari Hol Almarhum Sultan Ahmad Shah", {"Pahang"}, "negeri"),
        ("05-25", "Cuti Peristiwa Negeri Johor", {"Johor"}, "negeri"),
        ("05-26", "Hari Arafah", _KELANTAN_TERENGGANU, "negeri"),
        ("05-27", "Hari Raya Aidiladha", _ALL, "umum"),
        ("05-28", "Hari Raya Aidiladha (Hari Kedua)", _KELANTAN_TERENGGANU, "umum"),
        ("05-28", "Hari Raya Aidiladha (Hari Kedua)", _AIDILADHA_STATE, "negeri"),
        ("05-30", "Pesta Kaamatan", _KAAMATAN, "negeri"),
        ("05-31", "Pesta Kaamatan (Hari Kedua)", _KAAMATAN, "negeri"),
        ("05-31", "Hari Wesak", _ALL, "umum"),
        ("06-01", "Hari Keputeraan Rasmi Yang di-Pertuan Agong", _ALL, "umum"),
        ("06-01", "Hari Gawai Dayak", {"Sarawak"}, "negeri"),
        ("06-02", "Hari Gawai Dayak (Hari Kedua)", {"Sarawak"}, "negeri"),
        ("06-17", "Awal Muharam", _ALL, "umum"),
        ("07-05", "Hari Keputeraan Sultan Kedah", {"Kedah"}, "negeri"),
        ("07-07", "Hari Ulang Tahun Pengisytiharan Tapak Warisan Dunia", {"Pulau Pinang"}, "negeri"),
        ("07-11", "Hari Jadi Yang di-Pertua Negeri Pulau Pinang", {"Pulau Pinang"}, "negeri"),
        ("07-13", "Cuti Peristiwa Negeri Johor", {"Johor"}, "negeri"),
        ("07-21", "Hari Hol Almarhum Sultan Iskandar", {"Johor"}, "negeri"),
        ("07-22", "Hari Kemerdekaan Sarawak", {"Sarawak"}, "negeri"),
        ("07-31", "Hari Keputeraan Sultan Pahang", {"Pahang"}, "negeri"),
        ("08-03", "Cuti Peristiwa Negeri Sembilan", {"Negeri Sembilan"}, "negeri"),
        ("08-24", "Hari Jadi Yang di-Pertua Negeri Melaka", {"Melaka"}, "negeri"),
        ("08-25", "Maulidur Rasul", _ALL, "umum"),
        ("08-31", "Hari Kebangsaan", _ALL, "umum"),
        ("09-01", "Cuti Peristiwa Negeri Selangor", {"Selangor"}, "negeri"),
        ("09-16", "Hari Malaysia", _ALL, "umum"),
        ("09-29", "Hari Keputeraan Sultan Kelantan", {"Kelantan"}, "negeri"),
        ("09-30", "Hari Keputeraan Sultan Kelantan (Hari Kedua)", {"Kelantan"}, "negeri"),
        ("10-10", "Hari Jadi Yang di-Pertua Negeri Sarawak", {"Sarawak"}, "negeri"),
        ("10-25", "Jubli Perak Pemerintahan Sultan Selangor", {"Selangor"}, "negeri"),
        ("11-06", "Hari Keputeraan Sultan Perak", {"Perak"}, "negeri"),
        ("11-08", "Deepavali", _DEEPAVALI, "umum"),
        ("12-11", "Hari Keputeraan Sultan Selangor", {"Selangor"}, "negeri"),
        ("12-24", "Malam Krismas", {"Sabah"}, "negeri"),
        ("12-25", "Hari Krismas", _ALL, "umum"),
    ),
    2027: (
        ("01-01", "Tahun Baharu", _NEW_YEAR, "negeri"),
        ("01-06", "Israk dan Mikraj", _ISRAK, "negeri"),
        ("01-14", "Hari Keputeraan Yang di-Pertuan Besar Negeri Sembilan", {"Negeri Sembilan"}, "negeri"),
        ("01-22", "Thaipusam", _THAIPUSAM, "negeri"),
        ("02-01", "Hari Wilayah Persekutuan", _WILAYAH, "negeri"),
        ("02-06", "Tahun Baharu Cina", _ALL, "umum"),
        ("02-07", "Tahun Baharu Cina (Hari Kedua)", _ALL - _KELANTAN_TERENGGANU, "umum"),
        ("02-07", "Tahun Baharu Cina (Hari Kedua)", _KELANTAN_TERENGGANU, "negeri"),
        ("02-08", "Awal Ramadan", {"Johor", "Kedah"}, "negeri"),
        ("02-20", "Hari Pengisytiharan Tarikh Kemerdekaan", {"Melaka"}, "negeri"),
        ("02-24", "Nuzul Al-Quran", _NUZUL_2027, "negeri"),
        ("03-04", "Hari Ulang Tahun Pertabalan Sultan Terengganu", {"Terengganu"}, "negeri"),
        ("03-10", "Hari Raya Aidilfitri", _ALL, "umum"),
        ("03-11", "Hari Raya Aidilfitri (Hari Kedua)", _ALL, "umum"),
        ("03-12", "Hari Raya Aidilfitri (Hari Ketiga)", {"Melaka"}, "negeri"),
        ("03-23", "Hari Keputeraan Sultan Johor", {"Johor"}, "negeri"),
        ("03-26", "Good Friday", {"Sabah", "Sarawak"}, "negeri"),
        ("03-30", "Hari Jadi Yang di-Pertua Negeri Sabah", {"Sabah"}, "negeri"),
        ("04-26", "Hari Keputeraan Sultan Terengganu", {"Terengganu"}, "negeri"),
        ("05-01", "Hari Pekerja", _ALL, "umum"),
        ("05-16", "Hari Arafah", _KELANTAN_TERENGGANU, "negeri"),
        ("05-17", "Hari Raya Aidiladha", _ALL, "umum"),
        ("05-17", "Hari Keputeraan Raja Perlis", {"Perlis"}, "negeri"),
        ("05-18", "Hari Raya Aidiladha (Hari Kedua)", _KELANTAN_TERENGGANU, "umum"),
        ("05-18", "Hari Raya Aidiladha (Hari Kedua)", _AIDILADHA_STATE, "negeri"),
        ("05-20", "Hari Wesak", _ALL, "umum"),
        ("05-22", "Hari Hol Almarhum Sultan Ahmad Shah", {"Pahang"}, "negeri"),
        ("05-30", "Pesta Kaamatan", _KAAMATAN, "negeri"),
        ("05-31", "Pesta Kaamatan (Hari Kedua)", _KAAMATAN, "negeri"),
        ("06-01", "Hari Gawai Dayak", {"Sarawak"}, "negeri"),
        ("06-02", "Hari Gawai Dayak (Hari Kedua)", {"Sarawak"}, "negeri"),
        ("06-06", "Awal Muharam", _ALL, "umum"),
        ("06-07", "Hari Keputeraan Rasmi Yang di-Pertuan Agong", _ALL, "umum"),
        ("06-20", "Hari Keputeraan Sultan Kedah", {"Kedah"}, "negeri"),
        ("07-07", "Hari Ulang Tahun Pengisytiharan Tapak Warisan Dunia", {"Pulau Pinang"}, "negeri"),
        ("07-10", "Hari Jadi Yang di-Pertua Negeri Pulau Pinang", {"Pulau Pinang"}, "negeri"),
        ("07-11", "Hari Hol Almarhum Sultan Iskandar", {"Johor"}, "negeri"),
        ("07-22", "Hari Kemerdekaan Sarawak", {"Sarawak"}, "negeri"),
        ("07-30", "Hari Keputeraan Sultan Pahang", {"Pahang"}, "negeri"),
        ("08-15", "Maulidur Rasul", _ALL, "umum"),
        ("08-24", "Hari Jadi Yang di-Pertua Negeri Melaka", {"Melaka"}, "negeri"),
        ("08-31", "Hari Kebangsaan", _ALL, "umum"),
        ("09-16", "Hari Malaysia", _ALL, "umum"),
        ("09-29", "Hari Keputeraan Sultan Kelantan", {"Kelantan"}, "negeri"),
        ("09-30", "Hari Keputeraan Sultan Kelantan (Hari Kedua)", {"Kelantan"}, "negeri"),
        ("10-09", "Hari Jadi Yang di-Pertua Negeri Sarawak", {"Sarawak"}, "negeri"),
        ("10-28", "Deepavali", _DEEPAVALI, "umum"),
        ("11-05", "Hari Keputeraan Sultan Perak", {"Perak"}, "negeri"),
        ("12-11", "Hari Keputeraan Sultan Selangor", {"Selangor"}, "negeri"),
        ("12-24", "Malam Krismas", {"Sabah"}, "negeri"),
        ("12-25", "Hari Krismas", _ALL, "umum"),
        ("12-26", "Israk dan Mikraj", _ISRAK, "negeri"),
    ),
}

# Observed dates depend on the state, overlapping holidays and public-service
# notices. Spell them out instead of automatically replacing every weekend.
# JPA 8 January 2026: the two celebrations in Kuala Lumpur/Putrajaya share
# one observed public-service holiday: https://docs.jpa.gov.my/docs/akhbar/2026/siaran_media08012026.pdf
_OBSERVED_DAYS = {
    2026: (
        ("01-18", "Israk dan Mikraj", {"Terengganu"}),
        ("02-02", "Hari Wilayah Persekutuan dan Thaipusam", _WILAYAH - {"Labuan"}),
        ("02-02", "Hari Wilayah Persekutuan", {"Labuan"}),
        ("02-02", "Thaipusam", _THAIPUSAM - _WILAYAH),
        ("03-08", "Nuzul Al-Quran", _KELANTAN_TERENGGANU),
        ("03-23", "Hari Raya Aidilfitri", _GROUP_B - {"Johor", "Melaka"}),
        ("03-24", "Hari Raya Aidilfitri", {"Johor", "Melaka"}),
        ("05-03", "Hari Pekerja", {"Kedah"}),
        ("05-18", "Hari Keputeraan Raja Perlis", {"Perlis"}),
        ("06-02", "Hari Wesak", _GROUP_B - {"Sarawak"}),
        ("06-03", "Pesta Kaamatan", _KAAMATAN),
        ("06-03", "Hari Wesak", {"Sarawak"}),
        ("06-04", "Hari Gawai Dayak", {"Sarawak"}),
        ("10-26", "Jubli Perak Pemerintahan Sultan Selangor", {"Selangor"}),
        ("11-09", "Deepavali", _GROUP_B - {"Sarawak"}),
        ("12-27", "Hari Krismas", {"Kedah"}),
    ),
    2027: (
        ("02-08", "Tahun Baharu Cina", _GROUP_B - {"Johor"}),
        ("02-09", "Tahun Baharu Cina", {"Johor"}),
        ("05-02", "Hari Pekerja", _KELANTAN_TERENGGANU),
        ("05-19", "Hari Keputeraan Raja Perlis", {"Perlis"}),
        ("06-01", "Pesta Kaamatan", _KAAMATAN),
        ("06-08", "Awal Muharam", _GROUP_B),
        ("07-12", "Hari Hol Almarhum Sultan Iskandar", {"Johor"}),
        ("08-16", "Maulidur Rasul", _GROUP_B),
        ("12-26", "Hari Krismas", {"Kelantan"}),
        ("12-27", "Hari Krismas", {"Terengganu"}),
        ("12-27", "Israk dan Mikraj", {"Negeri Sembilan", "Perlis"}),
    ),
}

# KPM academic calendars, appendices A–C:
# https://www.moe.gov.my/kalendar-akademik-semasa
_TERM_BREAKS = {
    (2026, "A"): (("01-01", "01-10"), ("03-20", "03-28"), ("05-22", "06-06"),
                  ("08-28", "09-05"), ("12-04", "12-31")),
    (2026, "B"): (("01-01", "01-11"), ("03-21", "03-29"), ("05-23", "06-07"),
                  ("08-29", "09-06"), ("12-05", "12-31")),
    (2027, "A"): (("01-01", "01-03"), ("03-05", "03-13"), ("05-21", "06-05"),
                  ("08-27", "09-04"), ("12-03", "12-31")),
    (2027, "B"): (("01-01", "01-03"), ("03-06", "03-14"), ("05-22", "06-06"),
                  ("08-28", "09-05"), ("12-04", "12-31")),
}
_KPM_ADDITIONS = {
    2026: (
        (("02-15", "02-16", "02-19"), "Tahun Baharu Cina", FRI_SAT),
        (("02-16", "02-19", "02-20"), "Tahun Baharu Cina", _GROUP_B),
        # The 18 March closure was announced by KPM on 10 March 2026.
        (("03-18", "03-19"), "Hari Raya Aidilfitri", _ALL),
        (("03-20",), "Hari Raya Aidilfitri", _GROUP_B),
        (("11-09",), "Deepavali", FRI_SAT | {"Sarawak"}),
        (("11-10",), "Deepavali", _GROUP_B - {"Sarawak"}),
    ),
    2027: (
        (("02-05", "02-09", "02-10", "02-11", "02-12"), "Tahun Baharu Cina", _GROUP_B),
        (("02-08",), "Tahun Baharu Cina", _KELANTAN_TERENGGANU),
        (("02-09", "02-10", "02-11"), "Tahun Baharu Cina", FRI_SAT),
        (("03-14",), "Hari Raya Aidilfitri", FRI_SAT),
        (("05-16",), "Hari Raya Aidiladha", FRI_SAT),
        (("05-18",), "Hari Raya Aidiladha", _GROUP_B | {"Kedah"}),
        (("05-19",), "Hari Raya Aidiladha", _ALL),
        (("05-21",), "Wesak", _GROUP_B),
        (("10-27",), "Deepavali", _DEEPAVALI),
        (("10-28",), "Deepavali", {"Sarawak"}),
        (("10-29",), "Deepavali", _GROUP_B - {"Sarawak"}),
    ),
}


def calendar_available(state, year):
    return state in _ALL and year in _PUBLIC_DAYS


def is_weekend(state, target):
    return target.weekday() in ((4, 5) if state in FRI_SAT else (5, 6))


def school_closure(state, target):
    """Return a display label for a known closure in the school's state."""
    if state not in _ALL:
        return ""
    day = target.strftime("%m-%d")
    public = [f"Cuti {kind} · {name}" for when, name, states, kind in _PUBLIC_DAYS.get(target.year, ())
              if when == day and state in states]
    observed = [f"Cuti ganti · {name}" for when, name, states in _OBSERVED_DAYS.get(target.year, ())
                if when == day and state in states]
    if public or observed:
        return " / ".join(public + observed)
    if is_weekend(state, target):
        return "Hujung minggu"
    group = "A" if state in FRI_SAT else "B"
    if any(first <= day <= last for first, last in _TERM_BREAKS.get((target.year, group), ())):
        return "Cuti persekolahan KPM"
    for dates, name, states in _KPM_ADDITIONS.get(target.year, ()):
        if day in dates and state in states:
            return f"Cuti perayaan KPM · {name}"
    return ""


def calendar_notice(state, dates):
    if not state:
        return "Isi negeri sekolah di Profil & Akses untuk semakan cuti."
    if not all(calendar_available(state, day.year) for day in dates):
        return "Takwim cuti bagi tarikh ini belum tersedia sepenuhnya. Sahkan hari PdP dengan sekolah."
    return f"Semakan cuti berdasarkan negeri sekolah ({state}). Sahkan juga cuti setempat."
