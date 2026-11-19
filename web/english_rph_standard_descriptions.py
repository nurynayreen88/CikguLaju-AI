"""Display the DSKP descriptions of standards already assigned to an English lesson."""

from functools import lru_cache
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTIONS = ROOT / "rph_standalone/english/kssr_standard_descriptions.json"
SOW_INDEX = ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json"
CONTENT_CODE = re.compile(r"(?<![\d.])[1-5]\.\d(?!\d|\.\d)")
LEARNING_CODE = re.compile(r"(?<![\d.])[1-5]\.\d\.\d(?!\d|\.\d)")


@lru_cache(maxsize=1)
def _standards():
    return json.loads(DESCRIPTIONS.read_text(encoding="utf-8"))["years"]


@lru_cache(maxsize=1)
def _lessons():
    source = json.loads(SOW_INDEX.read_text(encoding="utf-8"))
    return source["lessons"] if source.get("version") == "2026-11-03-source-table-2-6" else {}


def describe_rows(year, rows, *, fixed_lesson=None):
    """Complete both roles by year and exact code, including the parent CS of each LS."""
    if type(year) is not int or not 2 <= year <= 6:
        return rows
    year_standards = _standards()[str(year)]
    sow = _lessons().get(f"{year}/{fixed_lesson}", {}) if fixed_lesson is not None else {}
    result = dict(rows)
    for role, sow_field in (("MAIN", "main_ls"), ("COMPLEMENTARY", "complementary_ls")):
        cs_field, ls_field = f"{role} CONTENT STANDARD", f"{role} LEARNING STANDARD"
        cs_value, ls_value = str(rows.get(cs_field) or ""), str(rows.get(ls_field) or "")
        cs = list(dict.fromkeys(CONTENT_CODE.findall(cs_value)))
        ls = list(dict.fromkeys(LEARNING_CODE.findall(ls_value) + LEARNING_CODE.findall(cs_value)))
        if not ls and sow.get("teacher_selected") is False and sow.get(sow_field):
            ls = [sow[sow_field]]
        parents = list(dict.fromkeys(code.rsplit(".", 1)[0] for code in ls))
        if cs and parents and set(cs) != set(parents):
            continue
        cs = cs or parents
        for field, codes, texts in ((cs_field, cs, year_standards["sk"]),
                                    (ls_field, ls, year_standards["sp"])):
            if codes and all(code in texts for code in codes):
                result[field] = "\n".join(f"{code} {texts[code]}" for code in codes)
    return result


def install(runtime):
    previous = runtime._rph_rows

    def rows_with_descriptions(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        if not isinstance(rows, dict) or not runtime._is_english_subject(state):
            return rows
        year_label = str(state.get("year") or state.get("year_label") or "").strip()
        year = re.fullmatch(r"(?:(?:Tahun|Year)\s+)?([2-6])(?:\s*\(SK\))?", year_label, re.I)
        return describe_rows(int(year[1]), rows, fixed_lesson=state.get("_web_english_standard_lesson")) if year else rows

    runtime._rph_rows = rows_with_descriptions
