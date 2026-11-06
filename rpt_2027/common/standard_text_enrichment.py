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


def enrich_psv(year, records):
    """PSV 2-6: DSKP SK titles and every source-numbered SP statement.

    A DRAF extraction from original KPM DSKP PDFs; not a signed approval.
    """
    if year not in range(2, 7):
        raise ValueError("PSV DSKP mapping absent for year")
    source = _read_json(ROOT / "rpt_2027" / "psv" /
                        f"dskp_full_standard_texts_y{year}_20261107_DRAF.json")
    if (source.get("subject") != "PSV" or source.get("year") != year or
            source.get("status") != "DRAF_CROSSWALK_FULL_DSKP_TEXT"):
        raise ValueError("Unapproved PSV source mapping")
    sk_map, sp_map = source["sk"], source["sp"]
    for row in records:
        sk_codes = _codes(row["sk"])
        sp_codes = _codes(row["sp"])
        if any(code not in sk_map for code in sk_codes):
            raise ValueError(f"PSV T{year} PdP {row['id']} has unknown SK")
        if any(code not in sp_map for code in sp_codes):
            raise ValueError(f"PSV T{year} PdP {row['id']} has unknown SP")
        row["sk_display"] = "\n".join(f"{code} — {sk_map[code]}" for code in sk_codes)
        row["sp_display"] = "\n".join(f"{code} — {sp_map[code]}" for code in sp_codes)
    return records


def enrich_rbt(year, records):
    """RBT 4-6: original year-specific DSKP SK titles and full SP text."""
    if year not in (4, 5, 6):
        raise ValueError("RBT mapping absent for year")
    source = _read_json(ROOT / "rpt_2027" / "rbt" /
                        f"dskp_full_standard_texts_y{year}_20261107_DRAF.json")
    if (source.get("subject") != "RBT" or source.get("year") != year or
            source.get("status") != "DRAF_CROSSWALK_FULL_DSKP_TEXT"):
        raise ValueError("Unexpected RBT source mapping")
    sk_map, sp_map = source["sk"], source["sp"]
    for row in records:
        sk_codes = _codes(row["sk"])
        sp_codes = _codes(row["sp"])
        if any(code not in sk_map for code in sk_codes):
            raise ValueError(f"RBT T{year} PdP {row['id']} SK is absent from DSKP")
        if any(code not in sp_map for code in sp_codes):
            raise ValueError(f"RBT T{year} PdP {row['id']} SP is absent from DSKP")
        row["sk_display"] = "\n".join(f"{code} — {sk_map[code]}" for code in sk_codes)
        row["sp_display"] = "\n".join(f"{code} — {sp_map[code]}" for code in sp_codes)
    return records


def enrich_pjpk(year, records):
    """PJPK 2-6: keep SK/SP statements in *separate PJ and PK namespaces*.

    Codes overlap between physical education and health education; never
    search a flat dictionary or infer a component from the numeric code.
    """
    if year not in range(2, 7):
        raise ValueError("PJPK DSKP mapping absent for year")
    source = _read_json(ROOT / "rpt_2027" / "pjpk" /
                        f"dskp_full_standard_texts_y{year}_20261107_DRAF.json")
    if (source.get("subject") != "PJPK" or source.get("year") != year or
            source.get("status") != "DRAF_CROSSWALK_FULL_DSKP_TEXT"):
        raise ValueError("Unexpected PJPK source mapping")
    if set(source["components"]) != {"PJ", "PK"}:
        raise ValueError("PJPK mapping must have two distinct components")
    for row in records:
        original_id = row.get("display_id", "")
        match = re.fullmatch(r"(PJ|PK) PdP \d{3}", original_id)
        if not match:
            raise ValueError(f"PJPK T{year} missing original component identity")
        component = match.group(1)
        sk_map = source["components"][component]["sk"]
        sp_map = source["components"][component]["sp"]
        sk_codes = _codes(row["sk"])
        sp_codes = _codes(row["sp"])
        if any(code not in sk_map for code in sk_codes):
            raise ValueError(f"PJPK T{year} {original_id} unknown {component} SK")
        if any(code not in sp_map for code in sp_codes):
            raise ValueError(f"PJPK T{year} {original_id} unknown {component} SP")
        row["sk_display"] = "\n".join(f"{code} — {sk_map[code]}" for code in sk_codes)
        row["sp_display"] = "\n".join(f"{code} — {sp_map[code]}" for code in sp_codes)
    return records
