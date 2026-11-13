"""Reviewed KSSR Semakan 2017 English Year 1 plans for the Web renderer.

SOW SK Year 1, pp. 62–65, and repository Teacher's Book scan reviews L18–19.
https://padlet-uploads.storage.googleapis.com/214113651/91bb41eb266e86d4ccfe5ee4245ea5ac/Primary_Year_1_SK_Scheme_of_Work.pdf
Activities, differentiation and assessment are written for CikguLaju.
"""
from dataclasses import dataclass
from datetime import date


UNIT = "Unit 1 — At School"
STANDARD = {
    "1.2": "Understand meaning in familiar contexts",
    "1.2.1": "Identify the main idea of very simple spoken language with support",
    "1.2.2": "Identify specific details in very simple spoken language with support",
    "2.1": "Communicate simple information clearly",
    "2.1.5": "Name or describe objects using suitable vocabulary",
}


@dataclass(frozen=True)
class Plan:
    number: int
    skill: str
    page: int
    standards: tuple[str, str, str, str]
    objective: str
    induction: str
    listening: str
    speaking: str
    workbook: str
    assessment: str
    closure: str
    support: str

    @property
    def title(self):
        return f"Lesson {self.number:03d} — {self.skill}"

    @property
    def textbook_ref(self):
        return f"Student's Book m/s {self.page}"

    @property
    def materials(self):
        return (f"Super Minds 1 Student's Book p. {self.page}, "
                f"Workbook p. {self.page}, classroom objects and picture cards.")

    @property
    def topic(self):
        return f"{UNIT} · {self.title} (KSSR Semakan 2017)"

    def fields(self):
        main_cs, main_ls, comp_cs, comp_ls = self.standards
        return [
            {"label": "Topic", "value": self.topic},
            {"label": "Main CS", "value": f"{main_cs} {STANDARD[main_cs]}"},
            {"label": "Main LS", "value": f"{main_ls} {STANDARD[main_ls]}"},
            {"label": "Complementary CS", "value": f"{comp_cs} {STANDARD[comp_cs]}"},
            {"label": "Complementary LS", "value": f"{comp_ls} {STANDARD[comp_ls]}"},
            {"label": "Learning Objectives", "value": self.objective},
            {"label": "Success Criteria", "value": self.objective},
            {"label": "Teaching and Learning Materials", "value": self.materials},
            {"label": "Set Induction", "value": self.induction},
            {"label": "Activity 1 — Listening", "value": self.listening},
            {"label": "Activity 2 — Speaking", "value": self.speaking},
            {"label": "Activity 3 — Workbook", "value": self.workbook},
            {"label": "Assessment", "value": self.assessment},
            {"label": "Closure", "value": self.closure},
            {"label": "Remedial / Enrichment", "value": self.support},
        ]


PLANS = {
    18: Plan(
        18, "Listening 4", 10, ("1.2", "1.2.1", "2.1", "2.1.5"),
        "Identify the classroom as the setting of a short listening text and name three classroom objects.",
        "Teacher shows familiar objects. Pupils point to an object that matches a colour the teacher says.",
        "Teacher uses Student's Book p. 10 to introduce the listening task. Pupils listen for the setting and select the classroom picture, then listen again and point to objects they hear.",
        "Teacher models the chant with the objects. In pairs, pupils take turns holding up and naming three objects.",
        "Pupils complete Workbook p. 10 by matching words to pictures and colouring as instructed.",
        "Record each pupil's picture choice and three spoken object names. Ask the pupil to repeat one name if unclear.",
        "Teacher holds up one picture card. Each pupil tells a partner its name before leaving.",
        "Offer two picture choices and repeat key words. Invite confident pupils to name an additional object.",
    ),
    19: Plan(
        19, "Speaking 4", 11, ("2.1", "2.1.5", "1.2", "1.2.2"),
        "Name three classroom objects in short exchanges and identify two objects from spoken clues.",
        "Teacher reveals a picture card slowly. Pupils name the object once they recognise it.",
        "Teacher uses Student's Book p. 11 for the listening and numbering task. Pupils mark two object pictures they hear and compare their order with a partner.",
        "Teacher models 'What’s this?' and 'It’s a ruler.' Pairs take turns asking and naming objects. They also practise 'Is it a …?' with 'Yes, it is' or 'No, it isn’t'.",
        "Pupils complete the listening, writing and reading items in Workbook p. 11, then check with a partner.",
        "Check two listening responses. In a brief exchange, tally whether each pupil names three objects appropriately.",
        "Pairs choose one object and perform a final question-and-answer exchange for another pair.",
        "Provide picture cards and a sentence frame. Ask confident pupils to add a colour when describing an object.",
    ),
}


def install(runtime):
    """Keep reviewed fields after legacy English templates assemble native rows."""
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def rows(state, *args, **kwargs):
        number = state.get("_web_english_y1_kssr_lesson")
        if number not in PLANS:
            return previous(state, *args, **kwargs)
        plan = PLANS[number]
        main_cs, main_ls, comp_cs, comp_ls = plan.standards
        lesson_date = state.get("rph_date")
        return {
            "MATA PELAJARAN": "Bahasa Inggeris",
            "TAHUN/TINGKATAN": "Year 1",
            "TARIKH": date.fromisoformat(lesson_date).strftime("%d/%m/%Y") if lesson_date else "",
            "HARI": state.get("rph_day", ""),
            "MASA": state.get("rph_time", ""),
            "KELAS": state.get("rph_class", ""),
            "BILANGAN MURID": state.get("rph_students", ""),
            "TAJUK": plan.topic,
            "MAIN CONTENT STANDARD": f"{main_cs} {STANDARD[main_cs]}",
            "MAIN LEARNING STANDARD": f"{main_ls} {STANDARD[main_ls]}",
            "COMPLEMENTARY CONTENT STANDARD": f"{comp_cs} {STANDARD[comp_cs]}",
            "COMPLEMENTARY LEARNING STANDARD": f"{comp_ls} {STANDARD[comp_ls]}",
            "OBJEKTIF PEMBELAJARAN": plan.objective,
            "KRITERIA KEJAYAAN": plan.objective,
            "BAHAN BANTU MENGAJAR": plan.materials,
            "PENGETAHUAN SEDIA ADA": "Pupils recognise a few classroom objects.",
            "EMK / NILAI": "Language",
            "KBAT / PAK21": "Pair work",
            "SET INDUKSI": plan.induction,
            "AKTIVITI UTAMA": (
                f"Activity 1 – {plan.listening}\nActivity 2 – {plan.speaking}\nActivity 3 – {plan.workbook}"
            ),
            "PENTAKSIRAN": plan.assessment,
            "PENUTUP": plan.closure,
            "PEMULIHAN / PENGAYAAN": plan.support,
        }

    runtime._rph_rows = rows
    return True
