"""Display the checked DSKP descriptions for the selected Sains SK PdP."""

from functools import lru_cache
import json
from pathlib import Path
import re


@lru_cache(maxsize=1)
def _source():
    return json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))


def sequence_year(state):
    if state.get("subject") != "Sains":
        return None
    year = re.fullmatch(r"Tahun ([2-4])", str(state.get("year") or state.get("year_label") or ""))
    code = str(state.get("pdp_sequence_code") or "")
    if year and re.fullmatch(rf"(?:SCI-Y{year[1]}|ST{year[1]})-PDP-\d{{3}}", code):
        return year[1]
    return None


def describe_rows(state, rows):
    year = sequence_year(state)
    if not year:
        return rows
    source = _source()[year]
    fields = dict(rows)
    for key, target, group in (("cs", "STANDARD KANDUNGAN", "grouped_sk_codes"),
                               ("ls", "STANDARD PEMBELAJARAN", "grouped_sp_codes")):
        codes = tuple(dict.fromkeys(state.get(group) or ()))
        descriptions = source[key]
        if codes and all(descriptions.get(code) for code in codes):
            fields[target] = "; ".join(f"{code} {descriptions[code]}" for code in codes)
    return fields
