"""Read-only, lossless Web grouping of Telegram Mathematics Unit choices.

Telegram can expose distinct opaque tokens whose labels share one printed Unit
number. Render that numbered Unit once; never merge or rewrite the Telegram
tokens themselves. All PdP retain their original source Unit for generation.
"""
from collections import OrderedDict
import re

_UNIT_NUMBER = re.compile(
    r"^\s*(?:Unit|U)\s*0*([1-9][0-9]{0,2})(?=\b|[\s:：.\-–—•])", re.I)
_DOT_NUMBER = re.compile(r"^\s*([1-9][0-9]{0,2})(?:\.0)?\s*[•·]\s*")
_CLEAN_PREFIX = re.compile(
    r"^\s*(?:Unit|U)\s*0*[1-9][0-9]{0,2}\s*[:：.\-–—•]?\s*", re.I)


def _number(label):
    match = _UNIT_NUMBER.match(label) or _DOT_NUMBER.match(label)
    return int(match[1]) if match else None


def _identity(item):
    label = " ".join(item["label"].split())
    number = _number(label)
    return ("number", number) if number is not None else ("text", label.casefold())


def _display_label(entries, identity):
    if identity[0] != "number":
        return entries[0]["label"]
    number = identity[1]
    titles = []
    seen = set()
    for entry in entries:
        text = " ".join(entry["label"].split())
        if _DOT_NUMBER.match(text):
            text = _DOT_NUMBER.sub("", text)
        else:
            text = _CLEAN_PREFIX.sub("", text)
        text = text.strip(" :：-–—•")
        if text and text.casefold() not in seen:
            titles.append(text)
            seen.add(text.casefold())
    # Distinct printed subheadings stay visible without introducing Unit 1 twice.
    suffix = " / ".join(titles)
    return (f"Unit {number}: {suffix}" if suffix else f"Unit {number}")[:280]


def grouped_math_units(raw):
    """Return one visible item per year-scoped Unit; keep original first token."""
    groups = OrderedDict()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str):
            raise ValueError("Untrusted Mathematics Unit")
        if not isinstance(item.get("value"), str) or not item["value"]:
            raise ValueError("Untrusted Mathematics Unit token")
        groups.setdefault(_identity(item), []).append(item)
    return [
        {"value": items[0]["value"], "label": _display_label(items, identity)}
        for identity, items in groups.items()
    ]


def matched_math_tokens(raw, selected):
    """Expand exactly one source-backed visible unit into every original token."""
    if not isinstance(selected, str):
        return []
    groups = OrderedDict()
    for item in raw:
        groups.setdefault(_identity(item), []).append(item["value"])
    for tokens in groups.values():
        if selected in tokens:
            return list(dict.fromkeys(tokens))
    return []


def tagged_math_lessons(raw_by_unit):
    """Retain original lesson identity and provenance, even if labels repeat."""
    result = []
    seen = set()
    for source_token, rows in raw_by_unit:
        for row in rows:
            key = (source_token, row["value"])
            if key in seen:
                raise ValueError("Duplicate PdP identity within source Unit")
            seen.add(key)
            result.append({**row, "origin_unit": source_token})
    return result
