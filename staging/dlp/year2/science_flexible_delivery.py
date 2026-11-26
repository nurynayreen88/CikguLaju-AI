"""Topic-specific delivery guidance for the 34 scheduled half-hour Science Year 2 lessons.
Original activities, objectives and assessment remain intact. Allow continuation
where individual practical work or observation needs longer; do not skip evidence.
"""
SCIENCE_SHORT_PREPARATION = {
    "4": "Pre-sort counter sets and give each pair a printed table.",
    "5": "Set up individual trays with cotton wool, droppers and blunt tweezers.",
    "6": "Prepare used cups, rinse water and a drying rack at each table.",
    "7": "Label storage locations and lay out the three dry items.",
    "9": "Display the three picture choices together for a quick response.",
    "12": "Use one enlarged fictional chart and preprinted individual charts.",
    "13": "Prepare the height record and family chart on one response slip.",
    "14": "Hand out one set of animal picture cards per pair.",
    "16": "Use ready-printed nest and egg-cluster observations; compare side by side.",
    "17": "Provide the four illustrated birth records in a two-column format.",
    "20": "Pre-arrange the life-cycle pictures; allow oral reports alongside sketches.",
    "21": "Give pairs ready-sorted picture sets for food and shelter.",
    "26": "Provide dated observations and the consequence prompt on one sheet.",
    "27": "Set up the torch, mirror and card before pupils arrive.",
    "28": "Prepare paired viewing boxes and equivalent symbols before the lesson; run trials concurrently.",
    "32": "Set up the two demonstrations and reuse pupils' previous observation records.",
    "33": "Place identical component trays and printed circuit pictures on tables.",
    "34": "Prepare a working low-voltage circuit and four function cards per pair.",
    "40": "Prepare all five separation examples for brief teacher demonstrations instead of rotating groups.",
    "41": "Prepare three small mixtures and tools at each table so pairs can test concurrently.",
    "46": "Display the previous sieve and dissolving results side by side.",
    "47": "Give each pair one five-source picture set and a ready-drawn map.",
    "48": "Prepare the two tray setups and water in small cups before class.",
    "49": "Use two large ready-drawn landscape diagrams and a response slip.",
    "51": "Prepare the covered bowl and external ice pack early enough for droplets to be observable.",
    "52": "Prepare the tissue cup and water tray before class; demonstrate both trials.",
    "53": "Print the air-mixture diagram and two gas labels for each pair.",
    "54": "Place the fan and streamer at marked positions before the lesson.",
    "55": "Display the three daily-life pictures side by side.",
    "57": "Reuse the previous trapped-air and sailboat records; keep both demonstrations ready.",
    "58": "Lay out the building sets and their matching manuals beforehand.",
    "59": "Pre-sort mixed component trays and open manuals at the relevant panels.",
    "62": "Use a small preassembled model and labelled compartments; check each pupil's actual disassembly.",
    "63": "Keep the previously built models ready and provide a short observation slip."
}

def adapt_science_phases(lesson, number, minutes):
    if minutes != 30:
        return lesson["phases"]
    preparation = SCIENCE_SHORT_PREPARATION[number]
    phases = [list(p) for p in lesson["phases"]]
    assert len(phases) == 4
    # Internal indicative allocation only: the handout displays teacher time.
    # Individual evidence, not the stopwatch, determines completion.
    for p, duration in zip(phases, (3,15,9,3), strict=True):
        p[0] = p[0].split(" · ")[0] + f" · {duration} min"
    phases[1][1] = preparation + " " + phases[1][1]
    return phases
