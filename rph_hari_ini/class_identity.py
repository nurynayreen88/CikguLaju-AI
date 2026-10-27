"""Stable class identity for RPH Hari Ini, independent of class display names.

Staging-only helpers. A trusted server must persist mappings, never infer a
new ID when a class is renamed. No production database writes.
"""
from dataclasses import dataclass
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ClassIdentity:
    teacher_id: int
    school_year: int
    class_id: str
    display_name: str


def resolve_class_identity(*, teacher_id: int, school_year: int,
                           class_name: str, registry: Mapping) -> ClassIdentity | None:
    if type(teacher_id) is not int or type(school_year) is not int:
        return None
    if not 2020 <= school_year <= 2100 or not isinstance(class_name, str):
        return None
    name = class_name.strip()
    if not name:
        return None
    # Registry must come from a trusted server-managed mapping. An unregistered
    # class is blocked rather than silently creating a new identity.
    matches = [
        (k, v) for k, v in registry.items()
        if isinstance(k, tuple) and len(k) == 3
        and k[0] == teacher_id and k[1] == school_year
        and isinstance(k[2], str) and k[2].strip().casefold() == name.casefold()
    ]
    if len(matches) != 1:
        return None
    stable_id = matches[0][1]
    try:
        stable_id = str(UUID(str(stable_id)))
    except (ValueError, TypeError, AttributeError):
        return None
    return ClassIdentity(teacher_id, school_year, stable_id, name)


def rename_class(*, teacher_id: int, school_year: int, old_name: str,
                 new_name: str, registry: Mapping) -> dict | None:
    """Return a proposed copy; caller must persist atomically after approval."""
    if not isinstance(old_name, str) or not old_name.strip():
        return None
    current = resolve_class_identity(teacher_id=teacher_id, school_year=school_year,
                                     class_name=old_name, registry=registry)
    if current is None or not isinstance(new_name, str) or not new_name.strip():
        return None
    new_key = (teacher_id, school_year, new_name.strip())
    if any(k[0] == teacher_id and k[1] == school_year
           and isinstance(k[2], str) and k[2].strip().casefold() == new_name.strip().casefold()
           for k in registry if isinstance(k, tuple) and len(k) == 3):
        return None
    result = dict(registry)
    old_key = next(k for k in result
                   if isinstance(k, tuple) and len(k) == 3
                   and k[0] == teacher_id and k[1] == school_year
                   and isinstance(k[2], str)
                   and k[2].strip().casefold() == old_name.strip().casefold())
    del result[old_key]
    result[new_key] = current.class_id
    return result
