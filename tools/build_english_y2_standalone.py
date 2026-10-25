"""Generate 160 Year 2 SOW-mapped English RPH drafts, never mark them TB-verified.

Run: python tools/build_english_y2_standalone.py
Does not alter Year 1, databases, or Telegram routes.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/english_y1y2_sow_master_320.json"
OUT = ROOT / "rph_standalone/english/year2"

ACTIVITIES = {
    "Listening": ("Listen and respond", "Present a short spoken example using vocabulary from the unit; model the task and replay the spoken text.", "Listen for the target words, point to the matching picture and answer a short comprehension question.", "Check each pupil's response to one spoken instruction or question."),
    "Speaking": ("Guided pair speaking", "Model a short exchange using the unit vocabulary, then organise pairs to practise and change roles.", "Practise the exchange with a partner, taking turns to ask and answer.", "Listen to each pupil produce one intelligible response."),
    "Reading": ("Read and identify", "Introduce key words from the unit, demonstrate how to read a short age-appropriate text and guide comprehension.", "Read or follow the short text and identify two relevant details.", "Ask pupils to locate one piece of information in the text."),
    "Writing": ("Guided writing", "Model a sentence using vocabulary from the unit, guide spelling and spacing, and provide a short independent task.", "Complete a guided sentence, then check spelling and punctuation.", "Check one completed sentence against the model."),
    "Language Arts": ("Creative language response", "Introduce a simple chant, rhyme or language game linked to the unit and model participation.", "Participate in the language activity and demonstrate one expression from the unit.", "Observe each pupil's participation and use of one target expression."),
}

def render(row):
    number, lesson, unit, main_sk, main_sp, comp_sk, comp_sp = row
    skill = next((s for s in ACTIVITIES if lesson.startswith(s)), "Speaking")
    activity, teacher, pupils, assessment = ACTIVITIES[skill]
    return f"""# English Year 2 — Lesson {number}: {lesson}

**Unit:** {unit}
**Main SK/SP (SOW mapping):** {main_sk} / {main_sp}
**Complementary SK/SP (SOW mapping):** {comp_sk} / {comp_sp}
**Learning objective (draft):** By the end of the lesson, pupils can demonstrate a {skill.lower()} response related to {unit}.
**Teaching materials:** Age-appropriate pictures, word cards and classroom resources; exact textbook pages require Teacher's Book verification.
**Source status:** SOW_MAPPED_ONLY — not Teacher's Book verified.

## Set Induction
**Teacher:** Introduce the topic {unit} with a familiar picture and two oral prompts.
**Pupils:** Recall and share one word or expression linked to the topic.

## Activity 1 — {activity}
**Teacher:** {teacher}
**Pupils:** {pupils}

## Activity 2 — Guided practice
**Teacher:** Support pupils needing additional modelling and ask confident pupils to extend one response.
**Pupils:** Practise again, correct errors after feedback and share one answer.

## Assessment / PBD
**Teacher:** {assessment}
**Evidence:** Record observable individual performance and provide immediate feedback.

## Closure
**Teacher:** Recap the key language and invite two pupils to demonstrate.
**Pupils:** State or demonstrate one thing learned.

**QA status:** CONTENT DRAFT — requires lesson-specific Teacher's Book steps, materials and one-page A4 review before end-user activation.
"""

def build():
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))["Tahun 2"]
    assert len(rows) == 160 and [int(r[0]) for r in rows] == list(range(1, 161))
    OUT.mkdir(parents=True, exist_ok=True)
    for row in rows:
        target = OUT / f"lesson_{int(row[0]):03d}.md"
        if target.exists():
            continue
        target.write_text(render(row), encoding="utf-8")
    print("Year 2: 160 lesson draft files present")

if __name__ == "__main__":
    build()
