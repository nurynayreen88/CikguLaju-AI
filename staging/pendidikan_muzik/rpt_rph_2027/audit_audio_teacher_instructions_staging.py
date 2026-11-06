"""Inventory audio/media-dependent teacher instructions in all 175 Music RPH.

Read-only staging QA. Audio numbers printed in a textbook are NOT MP3 files,
and no license / teacher access can be inferred from a reference to a recording.
The audit prints a concise summary and saves details to a local CI artifact.
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASE = re.compile(
    r"^\*\*(Set [Ii]nduksi|Aktiviti [12]\b[^*]*|Pengukuhan dan pentaksiran\b[^*]*|Penutup\b[^*]*)\*\*\s*(.*)"
)
MEDIA = re.compile(r"\b(?:audio|rakaman|trek|track|mp3|dvd|cd\s*\d+)\b", re.I)
PLAY = re.compile(
    r"\b(?:mainkan|memainkan|memasang|pasang|putarkan|memutarkan|"
    r"dengarkan|memperdengarkan|mendengar|dengar|menggunakan|gunakan)\b",
    re.I,
)
DIRECT_FILE = re.compile(r"(?:https?://\S+\.(?:mp3|wav|m4a)|\bAudio\s*\d+(?:\s*[-–]\s*\d+)?\b)", re.I)
REVIEW = re.compile(r"^(?:\s*Bahan|\s*Bukti rujukan|\s*Nota audit)", re.I)


def audit():
    records = []
    counts = {"rph": 0, "phase_media_mentions": 0, "possible_audio_playback_dependency": 0,
              "specific_track_in_phase": 0, "unsanctioned_file_link_in_phase": 0}
    for year in range(2, 7):
        manifest = json.loads((ROOT / f"year{year}" / "pdp_manifest.json").read_text(encoding="utf-8"))
        assert len(manifest["pdps"]) == 35, f"Missing manifest rows Year {year}"
        for pdp in range(1, 36):
            entry = manifest["pdps"][pdp - 1]
            ident = f"MZ-Y{year}-{pdp:02d}"
            assert entry["pdp_id"] == ident
            assert entry.get("source_book_audio_file_verified") is False, f"Audio unexpectedly enabled: {ident}"
            text = (ROOT / f"year{year}" / f"rph_pdp_{pdp:02d}.md").read_text(encoding="utf-8")
            counts["rph"] += 1
            for line in text.splitlines():
                m = PHASE.match(line)
                if not m or not MEDIA.search(m.group(2)):
                    continue
                detail = m.group(2).strip()
                playback = bool(PLAY.search(detail))
                direct = bool(DIRECT_FILE.search(detail))
                url = bool(re.search(r"https?://\S+\.(?:mp3|wav|m4a)", detail, re.I))
                records.append({
                    "pdp_id": ident, "phase": m.group(1), "excerpt": detail,
                    "playback_language": playback,
                    "specific_audio_reference": direct,
                    "direct_unverified_audio_url": url,
                })
                counts["phase_media_mentions"] += 1
                counts["possible_audio_playback_dependency"] += int(playback)
                counts["specific_track_in_phase"] += int(direct)
                counts["unsanctioned_file_link_in_phase"] += int(url)
    assert counts["rph"] == 175
    report = {
        "scope": "STAGING_TEACHER_INSTRUCTION_MEDIA_INVENTORY_ONLY",
        "counts": counts,
        "teacher_facing_media_mentions": records,
        "source_audio_files_verified": 0,
        "approved_for_live": False,
        "follow_up": "Inspect any highlighted teacher-facing instruction before claiming audio-free delivery; never fabricate playback links.",
    }
    dst = Path(os.getenv("MUSIC_MEDIA_AUDIT_REPORT", "/tmp/music_teacher_media_audit.json"))
    dst.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MUSIC_TEACHER_MEDIA_AUDIT_SUMMARY " + json.dumps(counts, ensure_ascii=False))
    for item in records[:30]:
        print("MEDIA_PHASE_REVIEW " + json.dumps(item, ensure_ascii=False))
    # Never permit direct unverified playable files within teacher instructions.
    if counts["unsanctioned_file_link_in_phase"] != 0:
        raise SystemExit("Found unverified direct audio links in teacher-facing PdP phases")
    return report


if __name__ == "__main__":
    audit()
