"""Group verified Science choices by their textbook Unit.

Source tokens identify SK-level groups in some years. Keep every token so
a PdP still resolves through its original Telegram source.
"""
import re

from web.math_unit_groups import tagged_math_lessons

SCIENCE_UNIT_TITLES = {
    1: (
        "Kemahiran Saintifik", "Peraturan Bilik Sains",
        "Benda Hidup dan Benda Bukan Hidup", "Manusia", "Haiwan",
        "Tumbuhan", "Magnet", "Penyerapan", "Bumi", "Asas Binaan",
    ),
    2: (
        "Kemahiran Saintifik", "Peraturan Bilik Sains", "Manusia",
        "Haiwan", "Tumbuhan", "Terang dan Gelap", "Elektrik",
        "Campuran", "Bumi", "Teknologi",
    ),
    3: (
        "Kemahiran Saintifik", "Peraturan Bilik Sains", "Manusia",
        "Haiwan", "Tumbuh-tumbuhan", "Pengukuran", "Ketumpatan",
        "Asid dan Alkali", "Sistem Suria", "Mesin",
    ),
    4: (
        "Kemahiran Saintifik", "Manusia", "Haiwan", "Tumbuh-tumbuhan",
        "Sifat Cahaya", "Bunyi", "Tenaga", "Bahan", "Bumi", "Mesin",
    ),
    5: (
        "Kemahiran Saintifik", "Manusia", "Haiwan", "Tumbuh-tumbuhan",
        "Elektrik", "Haba", "Pengaratan", "Jirim", "Fasa Bulan dan Buruj", "Mesin",
    ),
    6: (
        "Kemahiran Saintifik", "Manusia", "Mikroorganisma",
        "Interaksi antara Hidupan", "Pemeliharaan dan Pemuliharaan",
        "Daya", "Kelajuan", "Teknologi Pengawetan Makanan", "Bahan Buangan",
        "Gerhana", "Galaksi", "Kestabilan dan Kekuatan", "Teknologi",
    ),
}
_PREFIX = re.compile(r"^\s*(\d{1,2})(?:\.\d+)?\s*[•·]")
_SUFFIX = re.compile(r"/\s*(\d{1,2})\.\d+(?=\s|$)")
_PRINTED = re.compile(r"^\s*Unit\s+(\d{1,2})\s*[:：]", re.I)
_PDP_NUMBER = re.compile(r"^PdP (\d+)\s*[•—]")


def _groups(year, raw):
    titles = SCIENCE_UNIT_TITLES[year]
    groups = {}
    for item in raw:
        label, token = item["label"], item["value"]
        numbers = {
            int(match[1])
            for pattern in (_PREFIX, _SUFFIX, _PRINTED)
            for match in pattern.finditer(label)
        }
        number = next(iter(numbers)) if len(numbers) == 1 else None
        if number is not None and 1 <= number <= len(titles):
            key = number
            label = f"Unit {number}: {titles[number - 1]}"
        else:
            key = token
        if key not in groups:
            groups[key] = (label, [])
        groups[key][1].append(token)
    return sorted(groups.items(), key=lambda item: item[0] if isinstance(item[0], int) else len(titles) + 1)


def grouped_science_units(year, raw):
    return [
        {"value": tokens[0], "label": label}
        for _, (label, tokens) in _groups(year, raw)
    ]


def matched_science_tokens(year, raw, selected):
    for _, (_, tokens) in _groups(year, raw):
        if selected in tokens:
            return tokens
    return []


def _lesson_order(row):
    number = _PDP_NUMBER.match(row["label"])
    return int(number[1]) if number else float("inf")


def tagged_science_lessons(raw_by_unit):
    return sorted(tagged_math_lessons(raw_by_unit), key=_lesson_order)
