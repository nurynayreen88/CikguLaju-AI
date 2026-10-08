"""Read-only PJPK RPH quality refinements for verified composer output.

Optional post-processing: never changes SK/SP, source mappings, or the database.
"""
import re

def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def refine_verified_pjpk_rph(data):
    """Return a refined copy of a verified RPH, or None for invalid input."""
    if not isinstance(data, dict) or data.get("source_verified") is not True:
        return None
    if data.get("subject") not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
        return None
    if not all(_clean(data.get(k)) for k in ("topic", "sk", "sp", "year")):
        return None
    activities = data.get("activities")
    if not isinstance(activities, (tuple, list)) or len(activities) != 4:
        return None
    if any(not isinstance(a, dict) or not _clean(a.get("heading")) or not _clean(a.get("description")) for a in activities):
        return None
    out = dict(data)
    topic = _clean(data["topic"])
    sp = _clean(data["sp"])
    if data["subject"] == "Pendidikan Jasmani":
        out["objective"] = f"Pada akhir PdP, murid dapat melakukan kemahiran berkaitan {topic} berdasarkan {sp}, dengan teknik dan langkah keselamatan yang betul."
        out["success_criteria"] = "Murid menunjukkan perlakuan kemahiran yang diperhatikan guru, mematuhi peraturan keselamatan dan membaiki teknik selepas maklum balas."
        out["assessment"] = "Pemerhatian perlakuan dan senarai semak teknik serta keselamatan."
    else:
        out["objective"] = f"Pada akhir PdP, murid dapat menjelaskan dan mengaplikasikan pembelajaran berkaitan {topic} berdasarkan {sp} dalam situasi yang sesuai."
        out["success_criteria"] = "Murid mengenal pasti tindakan yang sesuai, memberikan alasan dan menjawab soalan aplikasi berdasarkan situasi."
        out["assessment"] = "Soal jawab, respons situasi dan semakan alasan murid."
    return out
