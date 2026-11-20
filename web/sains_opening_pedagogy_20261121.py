"""Evidence-anchored EMK, KBAT and PAK21 for verified Sains opening lessons.

These are teaching approaches inferred from the *existing* CikguLaju lesson
activities, not new SK/SP, new exercises, or claims of an official EMK list.
No activity, page, PBD evidence, reflection or remediation text is rewritten.
"""


def pedagogy_for_plan(plan):
    """Return two short teaching fields based on this plan's actual activities."""
    actions = " ".join((
        str(plan.guided), str(plan.independent), str(plan.assessment),
        str(plan.closure),
    )).casefold()
    topic = " ".join((str(plan.title), str(plan.objective))).casefold()
    materials = str(plan.materials).casefold()
    context = " ".join((actions, topic, materials))

    if any(word in context for word in ("kitar semula", "alam sekitar", "pencemaran")):
        emk = "Kelestarian alam sekitar dan tanggungjawab"
    elif any(word in context for word in ("selamat", "keselamatan", "peraturan", "membersihkan", "menyimpan")):
        emk = "Nilai murni: keselamatan dan tanggungjawab"
    elif any(word in context for word in ("merekod", "bacaan", "jadual", "mengukur", "catatan")):
        emk = "Nilai murni: ketelitian merekod pemerhatian"
    else:
        emk = "Nilai murni: sikap ingin tahu dan ketelitian"

    if any(word in actions for word in ("berpasangan", "pasangan", "kepada rakan")):
        pak21 = "Kolaborasi dan komunikasi berpasangan"
    elif any(word in actions for word in ("kumpulan", "membentang", "pembentangan")):
        pak21 = "Komunikasi dan perbincangan kumpulan"
    elif any(word in actions for word in ("bergilir", "giliran", "demonstrasi")):
        pak21 = "Komunikasi melalui demonstrasi bergilir"
    else:
        pak21 = "Komunikasi melalui respons dan dapatan murid"

    if any(word in actions for word in ("inferens", "sebab", "mengapa", "bukti", "hipotesis")):
        kbat = "Memberi sebab berdasarkan pemerhatian"
    elif any(word in actions for word in ("banding", "perbezaan", "membanding")):
        kbat = "Membandingkan hasil pemerhatian"
    elif any(word in actions for word in ("mengelas", "pengelasan", "mengelaskan")):
        kbat = "Mengelaskan maklumat berdasarkan ciri"
    elif any(word in actions for word in ("mengukur", "bacaan", "merekod")):
        kbat = "Menggunakan data untuk menerangkan dapatan"
    else:
        kbat = "Menerangkan dapatan daripada aktiviti"

    return {
        "EMK / NILAI": emk,
        "KBAT / PAK21": f"KBAT: {kbat}; PAK21: {pak21}",
    }
