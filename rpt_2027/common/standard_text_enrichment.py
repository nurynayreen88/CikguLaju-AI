"""Attach complete SK/SP statements from existing sourced DSKP crosswalks.

The original SK/SP codes remain untouched. A missing, unexpected, or ambiguous
code is a hard error: no guessed standard text and no status promotion.
Only Sejarah Years 4-6 and Pendidikan Moral Years 2-6 are covered here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _codes(field):
    parts = [s.strip() for s in re.split(r"\s*[/;,]\s*", field.strip()) if s.strip()]
    if not parts or len(parts) != len(set(parts)):
        raise ValueError("Missing or duplicate SK/SP source codes")
    return parts


def enrich_sejarah(year, records):
    """Map each Year 4-6 Sejarah SK and every ordinary/K citizenship SP."""
    if year not in (4, 5, 6):
        raise ValueError("Sejarah crosswalk absent for year")
    source = _read_json(ROOT / "curriculum" / "sejarah" /
                        f"y{year}_dskp_crosswalk_DRAF.json")
    if source.get("year") != year or source.get("status") != "DRAF":
        raise ValueError("Unexpected Sejarah DSKP source revision/status")
    catalog = {}
    for standard in source["standards"]:
        key = standard["sk"].strip()
        if key in catalog or not standard.get("title"):
            raise ValueError("Duplicated/empty Sejarah SK source")
        sub = {}
        for value in standard["sp"]:
            code, statement = value["code"].strip(), value["text"].strip()
            if code in sub or not statement:
                raise ValueError("Ambiguous Sejarah DSKP SP entry")
            sub[code] = statement
        catalog[key] = (standard["title"].strip(), sub)
    for row in records:
        sk = row["sk"].strip()
        if sk not in catalog:
            raise ValueError(f"Sejarah T{year} PdP {row['id']} SK {sk} absent from DSKP")
        title, sp_map = catalog[sk]
        lines = []
        for code in _codes(row["sp"]):
            if code not in sp_map:
                raise ValueError(f"Sejarah T{year} PdP {row['id']} SP {code} absent from SK {sk}")
            lines.append(f"{code} — {sp_map[code]}")
        row["sk_display"] = f"{sk} — {title}"
        row["sp_display"] = "\n".join(lines)
    return records


def enrich_moral(year, records):
    """Use unit+code jointly; many Moral units share the same SP suffix."""
    if year not in range(2, 7):
        raise ValueError("Moral crosswalk absent for year")
    source = _read_json(ROOT / "rpt_2027" / "pendidikan_moral" /
                        f"year{year}_crosswalk_DSKP.json")
    if source.get("year") != year or "DRAF" not in str(source.get("status", "")):
        raise ValueError("Unexpected Moral DSKP source revision/status")
    units = {}
    for item in source["units"]:
        n = int(item["unit"])
        if n in units or not item.get("title") or not item.get("sk"):
            raise ValueError("Duplicated/empty Moral unit source")
        standard = {}
        for value in item["sp"]:
            code, statement = value["code"].strip(), value["text"].strip()
            if code in standard or not statement:
                raise ValueError("Duplicate/empty Moral DSKP SP source")
            standard[code] = statement
        units[n] = (item["sk"].strip(), item["title"].strip(), standard)
    for row in records:
        match = re.match(r"^Unit\s+(\d+)\s*:", row["unit"])
        if not match or int(match.group(1)) not in units:
            raise ValueError(f"Moral T{year} PdP {row['id']} unit missing from DSKP")
        unit_no = int(match.group(1))
        sk, title, sp_map = units[unit_no]
        if row["sk"].strip() != sk:
            raise ValueError(f"Moral T{year} PdP {row['id']} mismatched SK for unit {unit_no}")
        lines = []
        for code in _codes(row["sp"]):
            if code not in sp_map:
                raise ValueError(f"Moral T{year} PdP {row['id']} SP {code} absent from unit {unit_no}")
            lines.append(f"{code} — {sp_map[code]}")
        row["sk_display"] = f"{sk} — {title}"
        row["sp_display"] = "\n".join(lines)
    return records
