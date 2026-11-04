"""Read-only 160-Lesson Year4 legacy Telegram media-route cross-check.

Extract actual historical app.py dictionary from AST, not audit CSV claims.
Compare each routed media row with instructional CD/Track references in its
standalone RPH. Static agreement is NOT proof of playable/appropriate speech,
and disagreement is a QA candidate until checked against printed TB/SB.
No Flask/Telegram import, user DB, API calls or quota changes.
"""
import ast
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SOURCES = ROOT / "rph_standalone" / "english" / "year4"
OUT = ROOT / "output" / "english_y4_legacy_audio_route_audit_20261104.json"
ROUTE_VAR = "_EN4_AUDIO_ALL_V25259"
REF = re.compile(r"\b(?:Class\s*)?CD\s*([123])\s*(?:Track\s*|[-–]\s*)(\d{1,3})\b", re.I)


def _legacy_route_map():
    tree = ast.parse(APP.read_text(encoding="utf-8"), filename=str(APP))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == ROUTE_VAR
               for t in node.targets):
            data = ast.literal_eval(node.value)
            if not isinstance(data, dict):
                raise ValueError("Unexpected Year4 audio mapping value")
            return data
    raise RuntimeError("Historical Year4 audio map not found in actual app.py")


def _teacher_task_refs(source):
    # Exclude after-the-fact QA explanation; check the lesson header and
    # actual teaching procedure only. Audio metadata is kept separately.
    end = source.split("\n## Assessment and differentiation", 1)[0]
    end = end.split("\n**QA status:**", 1)[0]
    return sorted({f"CD{int(cd)} Track {int(track)}" for cd, track in REF.findall(end)})


def run():
    mapping = _legacy_route_map()
    lesson_rows = []
    statuses = Counter()
    for lesson in range(1, 161):
        p = SOURCES / f"lesson_{lesson:03d}.md"
        if not p.exists():
            raise FileNotFoundError(str(p))
        src = p.read_text(encoding="utf-8")
        refs = _teacher_task_refs(src)
        audios = mapping.get(lesson) or mapping.get(str(lesson)) or []
        findings = []
        for entry in audios:
            label = str(entry.get("audio_reference") or "").strip()
            fid = str(entry.get("storage_file_id") or "").strip()
            if not label or not fid or not entry.get("verified"):
                kind = "INCOMPLETE_LEGACY_ROUTE"
            elif not refs:
                kind = "NO_EXPLICIT_INSTRUCTIONAL_CD_REF"
            elif label in refs:
                kind = "INSTRUCTION_REFERENCE_MATCH_ONLY"
            else:
                m = REF.search(label)
                track = m.group(2) if m else None
                if track and any(REF.search(r) and REF.search(r).group(2) == track
                                 for r in refs):
                    kind = "POTENTIAL_WRONG_DISC"
                else:
                    kind = "POTENTIAL_WRONG_TRACK_OR_EXTRA"
            statuses[kind] += 1
            findings.append({"routed_ref": label, "legacy_storage_file_id": fid,
                             "status": kind, "declared_verified_flag": bool(entry.get("verified")),
                             "spoken_content_verified": False})
        lesson_rows.append({"lesson": lesson,
                            "source": str(p.relative_to(ROOT)),
                            "instructional_refs": refs,
                            "route_count": len(findings),
                            "routes": findings})
    l30 = lesson_rows[29]
    if not any(x["routed_ref"] == "CD2 Track 29" for x in l30["routes"]):
        raise AssertionError("Expected observed historical Lesson30 CD2 mismatch not found")
    if "CD1 Track 29" not in l30["instructional_refs"]:
        raise AssertionError("Lesson30 standalone RPH lost TB CD1 reference")
    entrypoint = (ROOT/"tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
    if "install_y4_l030_audio_guard(telegram_runtime)" not in entrypoint:
        raise AssertionError("Historical L30 wrong audio route is not fail-closed")

    report = {
        "date": "2026-11-04",
        "scope": "Legacy app.py Year4 media map vs standalone lesson reference only; no playback/content or actual user delivery claims.",
        "app_dict": ROUTE_VAR,
        "lessons_checked": len(lesson_rows),
        "routed_lessons": sum(bool(x["routes"]) for x in lesson_rows),
        "routed_files": sum(x["route_count"] for x in lesson_rows),
        "category_counts": dict(statuses),
        "known_l30": {"historic_route": l30["routes"], "rph_refs": l30["instructional_refs"],
                      "protection": "media hidden; stale sends blocked by deployed WSGI guard",
                      "audio_content_ready": False},
        "lessons": lesson_rows,
    }
    OUT.parent.mkdir(exist_ok=True, parents=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("ENGLISH_YEAR4_LEGACY_MEDIA_ROUTE_AUDIT",
          json.dumps({k: report[k] for k in ("lessons_checked","routed_lessons","routed_files",
                                             "category_counts")}, sort_keys=True))
    for row in lesson_rows:
        for audio in row["routes"]:
            if audio["status"].startswith("POTENTIAL_"):
                print("REVIEW", row["lesson"], audio["status"],
                      audio["routed_ref"], "vs", row["instructional_refs"])
    print("AUDIT_ONLY_NOT_FINAL_TEACHER_APPROVAL")


if __name__ == "__main__":
    run()
