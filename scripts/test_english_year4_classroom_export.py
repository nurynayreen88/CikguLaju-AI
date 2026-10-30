"""Regression checks for staging-only Year 4 classroom export filtering."""
from smoke_english_year4_exports import classroom_lines, source_lines


def main():
    for lesson in range(1, 161):
        clean = classroom_lines(source_lines(lesson))
        assert clean and clean[0].startswith("# English Year 4"), lesson
        assert any(line.startswith("## ") and "minutes)" in line.lower() for line in clean), lesson
        assert not any(line.strip().lower().startswith("**status:**") for line in clean), lesson
        assert not any(line.strip().lower().startswith("**qa status:**") for line in clean), lesson
    print("PASS: 160 classroom exports retain teaching stages and omit status metadata")


if __name__ == "__main__":
    main()
