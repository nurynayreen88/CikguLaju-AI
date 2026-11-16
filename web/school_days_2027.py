"""School day exclusions shared by Telegram and Web RPH Hari Ini for 2027."""

WEEKDAY = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")
FRI_SAT = frozenset(("Kedah", "Kelantan", "Terengganu"))
STATES = frozenset((
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Perak", "Perlis", "Pulau Pinang", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Putrajaya", "Labuan",
    "W.P. Kuala Lumpur", "W.P. Putrajaya", "W.P. Labuan",
))
STATE_LABELS = {state.casefold(): state.removeprefix("W.P. ") for state in STATES}


def normalize_state(value):
    return STATE_LABELS.get(value.strip().casefold()) if isinstance(value, str) else None


# KPM 2027 Lampiran C and the federal/state public holiday schedule. Term
# breaks fall outside the printed windows. Schools may add local closures.
COMMON_CLOSURES = frozenset((
    "02-08", "02-09", "02-10", "02-11", "05-17", "05-18", "05-19", "05-20",
    "06-07", "09-16", "10-28",
))
GROUP_A_CLOSURES = frozenset(("02-07", "03-14", "05-16", "06-06", "08-15", "10-27"))
GROUP_B_CLOSURES = frozenset(("02-05", "02-12", "05-21", "06-08", "08-16"))
STATE_CLOSURES = {
    "01-06": {"Kedah", "Negeri Sembilan", "Perlis", "Terengganu"},
    "01-14": {"Negeri Sembilan"},
    "01-22": {"Kuala Lumpur", "Putrajaya", "Johor", "Negeri Sembilan", "Perak", "Pulau Pinang", "Selangor"},
    "02-01": {"Kuala Lumpur", "Labuan", "Putrajaya"},
    "02-24": {"Kuala Lumpur", "Labuan", "Putrajaya", "Kelantan", "Pahang", "Perak", "Perlis", "Pulau Pinang", "Selangor", "Terengganu"},
    "03-04": {"Terengganu"},
    "03-23": {"Johor"},
    "03-26": {"Sabah", "Sarawak"},
    "03-30": {"Sabah"},
    "04-26": {"Terengganu"},
    "05-02": {"Kelantan", "Terengganu"},
    "06-20": {"Kedah"},
    "07-07": {"Pulau Pinang"},
    "07-12": {"Johor"},
    "07-22": {"Sarawak"},
    "07-30": {"Pahang"},
    "08-24": {"Melaka"},
    "09-29": {"Kelantan"},
    "09-30": {"Kelantan"},
    "11-05": {"Perak"},
}

def is_school_day(state, target):
    group_a = state in FRI_SAT
    day = target.strftime("%m-%d")
    weekend = (4, 5) if group_a else (5, 6)
    return not (target.weekday() in weekend
                or day in COMMON_CLOSURES
                or (group_a and day in GROUP_A_CLOSURES)
                or (not group_a and day in GROUP_B_CLOSURES)
                or state in STATE_CLOSURES.get(day, ())
                or (not group_a and state != "Sarawak" and day in ("10-27", "10-29")))
