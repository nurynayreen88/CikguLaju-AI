"""Build Year 3 standalone English RPH from verified Year 3 SOW JSON.

Input: data/english_y3_sow_master.json containing 'Tahun 3' records:
[lesson_number, skill_name, unit, main_sk, main_sp, complementary_sk, complementary_sp].
This script refuses missing/incomplete source mappings rather than fabricating SK/SP.
Run: python tools/build_english_y3_standalone.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/english_y3_sow_master.json"
DEST = ROOT / "rph_standalone" / "english" / "year3"


def build():
    if not SOURCE.is_file():
        raise FileNotFoundError("Verified Year 3 SOW mapping required: " + str(SOURCE))
    records = json.loads(SOURCE.read_text(encoding="utf-8"))["Tahun 3"]
    if len(records) != 160:
        raise ValueError("Exactly 160 verified Year 3 SOW lessons are required")
    numbers = [row[0] for row in records]
    if numbers != list(range(1, len(records) + 1)):
        raise ValueError("Year 3 lessons must be consecutive and start at 1")
    if any(len(row) != 7 or any(not str(x).strip() for x in row) for row in records):
        raise ValueError("Every Year 3 lesson requires its verified SK/SP mapping")
    # Do not overwrite any existing standalone RPH during generation.
    existing = [DEST / f"lesson_{number:03d}.md" for number in numbers]
    if any(path.exists() for path in existing):
        raise FileExistsError("Existing Year 3 RPH detected; refusing destructive regeneration")
    DEST.mkdir(parents=True, exist_ok=True)
    for number, skill, unit, main_sk, main_sp, comp_sk, comp_sp in records:
        skill_type = skill.split()[0].lower()
        plan = f"""# English Year 3 — Lesson {number}: {skill}

**Unit:** {unit}
**Main SK/SP:** {main_sk} / {main_sp}
**Complementary SK/SP:** {comp_sk} / {comp_sp}
**Objective:** Pupils demonstrate {skill_type} through a guided task related to {unit}.
**Materials:** Textbook, picture cards, word cards and pupil exercise books.

## Set Induction (5 minutes)
**Teacher:** Show a relevant picture from {unit}, elicit vocabulary and introduce today's learning target.
**Pupils:** Name familiar words and answer two short questions.

## Activity 1 — Teacher modelling (10 minutes)
**Teacher:** Demonstrate the {skill_type} task with an age-appropriate example and check understanding.
**Pupils:** Observe, listen and respond to the model.

## Activity 2 — Guided practice (25 minutes)
**Teacher:** Guide pair or group practice and provide corrective feedback.
**Pupils:** Practise the target skill and exchange responses with peers.

## Assessment / PBD (15 minutes)
**Teacher:** Check an individual response from each pupil against the lesson objective.
**Pupils:** Demonstrate understanding independently.

## Closure (5 minutes)
**Teacher:** Review key vocabulary and invite pupils to reflect.
**Pupils:** Share one thing they have learned.

**QA:** Preliminary standalone draft; verify specific Teacher's Book steps before publication.
"""
        (DEST / f"lesson_{number:03d}.md").write_text(plan, encoding="utf-8")
    print(f"Generated {len(records)} Year 3 RPH lessons")


if __name__ == "__main__":
    build()
