"""PJPK v26.69 standalone RPH text composer for verified PdP.

Safe staging fallback for preview and QA. No database writes, no invented SK/SP.
The existing app PDF formatter remains the owner of PDF output.
"""
from pjpk_activity_adapter_v2666 import prepare_pjpk_rph
from pjpk_rph_quality_v2672 import refine_verified_pjpk_rph

def compose_verified_pjpk_rph(selection, connect):
    """Return structured one-page-friendly content, or None if not verified."""
    result = prepare_pjpk_rph(selection, connect)
    if not isinstance(result, dict) or not result.get("_pjpk_activity_verified_v2666"):
        return None
    phases = result.get("_pjpk_activity_phases_v2666")
    if not phases or len(phases) != 4:
        return None
    topic = result.get("topic") or result.get("topic_title")
    subject = result.get("subject") or result.get("subject_name")
    year = result.get("year_label") or result.get("year")
    sk_code, sk_text = result.get("sk_code"), result.get("sk_text")
    sp_code, sp_text = result.get("sp_code"), result.get("sp_text")
    if not all((topic, subject, year, sk_code, sk_text, sp_code, sp_text)):
        return None
    composed = {
        "subject": subject,
        "year": year,
        "topic": topic,
        "sk": f"{sk_code} {sk_text}",
        "sp": f"{sp_code} {sp_text}",
        "objective": f"Pada akhir PdP, murid dapat menunjukkan penguasaan: {sp_text}.",
        "success_criteria": f"Murid dapat melaksanakan atau menjelaskan {sp_text} melalui aktiviti dan pentaksiran yang ditetapkan.",
        "activities": [{"heading": heading, "description": description} for heading, description in phases],
        "assessment": "Pemerhatian dan senarai semak kemahiran" if subject == "Pendidikan Jasmani" else "Soal jawab dan respons situasi",
        "reflection": "____ / ____ murid mencapai objektif. Tindakan susulan: __________________.",
        "source_verified": True,
    }
    return refine_verified_pjpk_rph(composed)

def render_verified_pjpk_text(selection, connect):
    data = compose_verified_pjpk_rph(selection, connect)
    if data is None:
        return None
    lines = [
        f"RPH {data['subject']} | {data['year']}",
        f"Tajuk: {data['topic']}",
        f"SK: {data['sk']}",
        f"SP: {data['sp']}",
        f"Objektif: {data['objective']}",
        f"Kriteria Kejayaan: {data['success_criteria']}",
    ]
    for phase in data["activities"]:
        lines.extend((phase["heading"], phase["description"]))
    lines.extend((f"Pentaksiran: {data['assessment']}", f"Refleksi: {data['reflection']}"))
    return "\n".join(lines)
