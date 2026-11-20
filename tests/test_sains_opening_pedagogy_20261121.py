"""Contract checks for lesson-anchored support fields in existing Sains PdP.

No standards, page references, learning tasks, PBD or follow-up are rewritten.
"""
import pytest

from web.sains_y3_unit_awal import (
    LESSONS as YEAR3_OPENING, SP as YEAR3_SP, plan_rows, plan_text,
)
from web.sains_unit_awal import LESSONS as OTHER_OPENING, STANDARDS
from web.sains_opening_pedagogy_20261121 import pedagogy_for_plan


ALL_OPENING = tuple(OTHER_OPENING) + tuple(YEAR3_OPENING)


@pytest.mark.parametrize("plan", ALL_OPENING, ids=lambda plan: plan.code)
def test_supports_are_specific_and_original_curriculum_and_pbd_remain(plan):
    standards = YEAR3_SP if plan in YEAR3_OPENING else STANDARDS[plan.year]
    original = {"REFLEKSI": "Refleksi guru yang asal", "SESSION_MARKER": "sama"}
    result = plan_rows(original, plan, standards)
    assert result["REFLEKSI"] == original["REFLEKSI"]
    assert result["SESSION_MARKER"] == original["SESSION_MARKER"]
    assert result["STANDARD PEMBELAJARAN"].splitlines() == [
        f"{sp} {standards[sp]}" for sp in plan.standards
    ]
    assert result["OBJEKTIF PEMBELAJARAN"] == "Murid dapat " + plan.objective[0].lower() + plan.objective[1:]
    assert plan.guided in result["AKTIVITI UTAMA"]
    assert plan.independent in result["AKTIVITI UTAMA"]
    assert result["PENTAKSIRAN"] == plan.assessment
    assert result["PEMULIHAN / PENGAYAAN"] == plan.follow_up
    assert plan.pages in result["BAHAN BANTU MENGAJAR"]
    assert result["EMK / NILAI"].strip()
    assert result["KBAT / PAK21"].startswith("KBAT: ")
    assert "; PAK21: " in result["KBAT / PAK21"]
    source_text = plan_text(plan, standards)
    assert "EMK / NILAI: " + result["EMK / NILAI"] in source_text
    assert "KBAT / PAK21: " in source_text
    assert plan.guided in source_text
    assert plan.independent in source_text
    assert "PEMULIHAN / PENGAYAAN: " + plan.follow_up in source_text
    assert result["KBAT / PAK21"] != "Kemahiran Proses Sains"
    assert len(result["EMK / NILAI"]) <= 78
    assert len(result["KBAT / PAK21"]) <= 138


def test_pairwork_is_derived_from_actual_pupil_activity():
    grouped = next(plan for plan in ALL_OPENING if "berpasangan" in (
        plan.guided + plan.independent
    ).casefold())
    detail = pedagogy_for_plan(grouped)
    assert "berpasangan" in detail["KBAT / PAK21"].casefold()


def test_environment_topic_is_not_claimed_when_source_has_no_such_context():
    from web.sains_y3_unit_awal import Lesson
    plan = Lesson(
        199, ("1.1.3",), "Mengukur panjang", "7",
        "Mengukur panjang satu objek.", "Pembaris.",
        "Guru menunjukkan pembaris.", "Guru menerangkan penggunaan pembaris.",
        "Murid mengukur panjang jalur kad.", "Guru menyemak bacaan.",
        "Murid menerangkan bacaannya.", "Sediakan pembaris bertanda."
    )
    result = pedagogy_for_plan(plan)
    assert "Kelestarian alam sekitar" not in result["EMK / NILAI"]
    assert "KBAT:" in result["KBAT / PAK21"]
