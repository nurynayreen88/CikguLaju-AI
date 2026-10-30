"""Regression checks for staging-only Year 4 classroom export filtering."""
import re
from smoke_english_year4_exports import classroom_lines, source_lines


def check_filter_boundaries():
    sample = [
        "# English Year 4 — Lesson 1",
        "**Duration:** 60 minutes",
        "## Activity 1 (20 minutes)",
        "**Teacher:** Explain the task.",
        "## Source mapping and QA",
        "INTERNAL ONLY",
        "## Closure (5 minutes)",
        "**Pupils:** Reflect on the task.",
        "**Status:** DRAFT",
    ]
    clean = classroom_lines(sample)
    assert "INTERNAL ONLY" not in clean
    assert "**Status:** DRAFT" not in clean
    assert "## Closure (5 minutes)" in clean
    assert "**Pupils:** Reflect on the task." in clean


def main():
    check_filter_boundaries()
    for lesson in range(1, 161):
        clean = classroom_lines(source_lines(lesson))
        assert clean and clean[0].startswith("# English Year 4"), lesson
        stage_minutes = [int(m.group(1)) for line in clean if line.startswith("## ") for m in [re.search(r"\\((\\d+) minutes\\)", line, flags=re.IGNORECASE)] if m]
        assert len(stage_minutes) >= 4, (lesson, stage_minutes)
        assert sum(stage_minutes) == 60, (lesson, stage_minutes)
        assert any(line.lower().startswith("## set induction") for line in clean), lesson
        assert any(line.lower().startswith("## closure") for line in clean), lesson
        assert any("pbd" in line.lower() for line in clean), lesson
        assert not any(line.strip().lower().startswith("**status:**") for line in clean), lesson
        assert not any(line.strip().lower().startswith("**qa status:**") for line in clean), lesson
        assert not any(line.strip().lower().startswith(("**source:**", "**sow:**", "**references:**")) for line in clean), lesson
        assert not any("not ready for release" in line.lower() for line in clean), lesson
        assert any("**duration:** 60 minutes" in line.lower() for line in clean), lesson
    print("PASS: 160 classroom exports retain teaching stages and omit status metadata")


if __name__ == "__main__":
    main()
