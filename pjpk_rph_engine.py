"""Non-destructive offline PJPK RPH renderer. Preview is NEVER a production RPH."""
import csv
import sqlite3
from pathlib import Path
from pjpk_private_menu import ensure_menu_view

with (Path(__file__).resolve().parent / "COLLISION_QUARANTINE_10.csv").open(encoding="utf-8-sig", newline="") as _source:
    QUARANTINE = {int(row["entry_id"]) for row in csv.DictReader(_source)}
if len(QUARANTINE) != 10:
    raise RuntimeError("Fail closed: PJPK collision quarantine invalid")

def generate(db_path, entry_id, mode="preview", duration_minutes=30):
    if mode not in ("preview", "production"):
        raise ValueError("mode must be preview or production")
    if not isinstance(duration_minutes, int) or not 10 <= duration_minutes <= 120:
        raise ValueError("Invalid duration")
    if int(entry_id) in QUARANTINE:
        raise ValueError("Duplicate topic/SP quarantined; no PJPK preview permitted")
    with sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        ensure_menu_view(c)
        g = c.execute("SELECT * FROM pjpk_v47_generator_gate WHERE entry_id=?", (entry_id,)).fetchone()
        if g is None:
            raise ValueError("Unknown PJPK entry")
        menu = c.execute("SELECT entry_status FROM pjpk_v26_30_candidate_menu WHERE entry_id=?", (entry_id,)).fetchone()
        if not menu or menu["entry_status"] in ("ANCHOR_NOT_PDP", "SOURCE_CONFLICT_BLOCKED"):
            raise ValueError("PJPK entry blocked: anchor or source conflict; no RPH preview permitted")
        kind = c.execute("SELECT record_kind FROM pjpk_v53_entry_classification WHERE entry_id=?", (entry_id,)).fetchone()
        source_guard = c.execute("SELECT source_kind FROM pjpk_v59_source_kind_guard WHERE entry_id=?", (entry_id,)).fetchone()
        if source_guard and source_guard["source_kind"] == "TEXTBOOK_UNIT_ANCHOR":
            raise ValueError("Textbook unit anchor is not independently mapped to a PdP; generation prohibited")
        if kind and kind["record_kind"] == "TEXTBOOK_UNIT_ANCHOR":
            raise ValueError("Unit anchor is not a mapped PdP; RPH generation prohibited")
        if mode == "production" and not g["ready"]:
            raise ValueError("PJPK belum disahkan: " + g["reason"])
        e = c.execute("SELECT * FROM rpt_entries WHERE id=?", (entry_id,)).fetchone()
        if e is None:
            raise ValueError("Unknown RPT entry")
        links = [dict(x) for x in c.execute(
            'SELECT standard_type,standard_code,standard_text FROM rpt_entry_standards '
            'WHERE rpt_entry_id=? ORDER BY CASE standard_type WHEN "SK" THEN 0 ELSE 1 END,sequence_no',
            (entry_id,)
        )]
        if mode == "preview":
            for x in links:
                if x["standard_text"] or x["standard_type"] != "SP":
                    continue
                repair = c.execute(
                    "SELECT source_text,status FROM pjpk_v52_source_backed_repair WHERE entry_id=? AND standard_code=?",
                    (entry_id, x["standard_code"])
                ).fetchone()
                if repair and repair["status"] == "RPT_TEXT_FOUND_DSKP_CODE_NOT_FOUND":
                    x["standard_text"] = repair["source_text"] + " [TEKS RPT SAHAJA; KOD BELUM DISAHKAN DSKP]"
        if mode == "preview":
            correction = c.execute(
                "SELECT old_code,proposed_code,verified_sp_text,status FROM pjpk_v55_source_correction WHERE entry_id=?",
                (entry_id,)
            ).fetchone()
            if correction:
                for x in links:
                    if x["standard_type"] == "SP" and x["standard_code"] == correction["old_code"]:
                        x["standard_code"] = correction["proposed_code"]
                        x["standard_text"] = correction["verified_sp_text"] + " [CADANGAN PEMBETULAN DISOKONG DSKP/RPT; PAUTAN ASAL KEKAL]"
        scope_note = None
        if mode == "preview":
            scope = c.execute(
                "SELECT approved_sp_codes,source_note,status FROM pjpk_v62_slot_preview_scope WHERE entry_id=?",
                (entry_id,)
            ).fetchone()
            if scope and scope["status"] == "PREVIEW_ONLY":
                selected = {v.strip() for v in scope["approved_sp_codes"].split(",")}
                existing = {x["standard_code"] for x in links if x["standard_type"] == "SP"}
                if not selected or not selected.issubset(existing):
                    raise ValueError("Invalid proposed SP preview scope; fail closed")
                excluded = sorted(existing - selected)
                links = [x for x in links if x["standard_type"] != "SP" or x["standard_code"] in selected]
                scope_note = (
                    "SKOP PRATONTON CADANGAN RPT 2026 SAHAJA; bukan pembetulan pautan DB. "
                    "SP legacy dikecualikan daripada draf ini: "
                    + (", ".join(excluded) if excluded else "tiada")
                    + ". Semakan halaman RPT asal masih diperlukan."
                )
        # A numerically identical SP from another subject must never validate a PK entry.
        if e["year_label"] == "Tahun 5" and e["subject"] == "Pendidikan Kesihatan":
            for x in links:
                if x["standard_type"] == "SP" and x["standard_code"] in ("9.1.1", "9.1.2", "9.1.3"):
                    staged = c.execute(
                        "SELECT sp_text,source_subject,production_status FROM pjpk_v67_pk_t5_verified_source_staging WHERE sp_code=?",
                        (x["standard_code"],)
                    ).fetchone()
                    if not staged or staged["source_subject"] != "Pendidikan Kesihatan" or x["standard_text"].strip() != staged["sp_text"].strip():
                        raise ValueError("Cross-subject or unverified PK T5 9.1 SP text; fail closed")
                    raise ValueError("PK T5 9.1 DSKP staged but RPT PdP mapping is not verified; fail closed")
        if not links or any(not (x["standard_code"] or "").strip() or not (x["standard_text"] or "").strip() for x in links):
            raise ValueError("Missing standard code/text; cannot render")
        page = c.execute("SELECT textbook_page,match_status FROM pjpk_v40_page_sp_crosswalk WHERE entry_id=?", (entry_id,)).fetchone()
        component = g["component"]
        if component == "PJ":
            phases = [
                "Set induksi: Guru memperkenalkan kemahiran dan mengingatkan aspek keselamatan berdasarkan tajuk PdP.",
                "Aktiviti 1 – Demonstrasi: Guru menunjukkan kemahiran mengikut fokus SP yang tertera; murid memerhati dan menyebut petunjuk lakuan.",
                "Aktiviti 2 – Latihan berperingkat: Murid melaksanakan kemahiran secara individu/pasangan/kumpulan dengan pemerhatian dan maklum balas guru.",
                "Pengukuhan/penilaian: Murid menunjukkan semula kemahiran; guru menilai berdasarkan SP yang dipilih.",
                "Penutup: Regangan ringan, rumusan kemahiran dan keselamatan."
            ]
        else:
            phases = [
                "Set induksi: Guru mengemukakan situasi berkaitan tajuk Pendidikan Kesihatan.",
                "Aktiviti 1 – Penerokaan: Murid mengenal pasti fakta dan istilah daripada bahan yang disahkan mengikut SP.",
                "Aktiviti 2 – Aplikasi: Murid membincangkan situasi dan menjelaskan tindakan yang sesuai berdasarkan SP.",
                "Pengukuhan/penilaian: Murid memberi respons kepada situasi baharu; guru menyemak kefahaman berdasarkan SP.",
                "Penutup: Murid merumuskan amalan kesihatan yang dipelajari."
            ]
        lines = [
            "DRAF SEMAKAN — BUKAN RPH PRODUKSI" if mode == "preview" else "RPH PJPK",
            "Tahun: " + str(e["year_label"]),
            "Subjek: " + str(e["subject"]),
            "Unit: " + str(e["unit_title"] or "Belum direkodkan"),
            "Tajuk: " + str(e["topic"] or "Belum direkodkan"),
            "Tempoh: " + str(duration_minutes) + " minit",
            "Standard daripada DB (status pengesahan: " + ("READY" if g["ready"] else "BELUM READY") + "):"
        ]
        if scope_note:
            lines.append(scope_note)
        lines.extend(x["standard_type"] + " " + x["standard_code"] + " — " + x["standard_text"] for x in links)
        # Cross-check RPT SP wording against directly transcribed DSKP evidence.
        # This is read-only and does not promote the production gate.
        if mode == "preview":
            try:
                from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text
                evidence = load_evidence(Path(__file__).resolve().parent)
                lines.append("Semakan silang DSKP (sumber langsung; status RPH kekal draf):")
                for item in links:
                    if item["standard_type"] != "SP":
                        continue
                    result = reconcile_sp_text(
                        e["year_label"], e["subject"], item["standard_code"],
                        item["standard_text"], evidence
                    )
                    code = item["standard_code"]
                    if result["status"] == "NO_DIRECT_DSKP_TEXT":
                        lines.append("DSKP " + code + ": teks langsung belum dipadankan untuk tahun/subjek ini.")
                    elif result["status"] == "CONFLICT_REVIEW":
                        lines.append("DSKP " + code + ": KONFLIK TEKS SUMBER — perlu semakan; teks tidak dipilih.")
                    else:
                        lines.append(
                            "DSKP " + code + " [" + result["status"] + "] — "
                            + result["dskp_text"] + " (Sumber: " + result["source_document"] + ")"
                        )
            except (OSError, ValueError, EOFError) as exc:
                lines.append("Semakan silang DSKP tidak tersedia; kekal DRAF. Sebab: " + str(exc))
        first_sp = next((x for x in links if x["standard_type"] == "SP"), None)
        if first_sp:
            lines.append("Objektif (draf berasaskan SP, semakan guru wajib): Pada akhir PdP, murid dapat " + first_sp["standard_text"].rstrip(".") + ".")
        else:
            lines.append("Objektif belum dapat dibina: tiada pautan SP.")
        if e["activity_note"]:
            lines.append("Nota aktiviti sumber RPT: " + e["activity_note"])
        # Specific activities are permitted only where their source-linked mapping is recorded.
        t3 = c.execute("SELECT * FROM pjpk_v64_t3_specific_activity WHERE entry_id=?", (entry_id,)).fetchone()
        if t3:
            current = {x["standard_code"] for x in links if x["standard_type"] == "SP"}
            basis = {x.strip() for x in t3["sp_basis"].split(",")}
            if current != basis:
                raise ValueError("T3 activity/SP mismatch; fail closed")
            phases[1] = "Aktiviti 1 – " + t3["activity_1"]
            phases[2] = "Aktiviti 2 – " + t3["activity_2"]
            phases[3] = "Pengukuhan/penilaian: " + t3["assessment"]
            lines.append("DRAF AKTIVITI KHUSUS T3; SEMAKAN EDITORIAL WAJIB. SP: " + t3["sp_basis"])
        pk5 = c.execute("SELECT * FROM pjpk_v70_pk_t5_specific_activity WHERE entry_id=?", (entry_id,)).fetchone()
        if pk5:
            if e["year_label"] != "Tahun 5" or e["subject"] != "Pendidikan Kesihatan":
                raise ValueError("PK T5 activity subject/year mismatch; fail closed")
            current = {x["standard_code"] for x in links if x["standard_type"] == "SP"}
            basis = {x.strip() for x in pk5["sp_basis"].split(",")}
            if current != basis:
                raise ValueError("PK T5 activity/SP mismatch; fail closed")
            phases[1] = "Aktiviti 1 – " + pk5["activity_1"]
            phases[2] = "Aktiviti 2 – " + pk5["activity_2"]
            phases[3] = "Pengukuhan/penilaian: " + pk5["assessment"]
            lines.append("DRAF AKTIVITI KHUSUS PK T5; SEMAKAN EDITORIAL WAJIB. SP: " + pk5["sp_basis"])
        specific = c.execute(
            "SELECT activity_1,activity_2,assessment,source_note FROM pjpk_v57_specific_activity WHERE entry_id=?",
            (entry_id,)
        ).fetchone()
        if specific and not t3 and not pk5:
            phases[1] = "Aktiviti 1 – " + specific["activity_1"]
            phases[2] = "Aktiviti 2 – " + specific["activity_2"]
            phases[3] = "Pengukuhan/penilaian: " + specific["assessment"]
            lines.append("Asas aktiviti khusus: " + specific["source_note"])
        elif not t3 and not pk5:
            draft = c.execute("SELECT * FROM pjpk_v58_sp_activity_drafts WHERE entry_id=?", (entry_id,)).fetchone()
            if draft and not scope_note:
                phases[1] = "Aktiviti 1 – " + draft["activity_1"]
                phases[2] = "Aktiviti 2 – " + draft["activity_2"]
                phases[3] = "Pengukuhan/penilaian: " + draft["assessment"]
                lines.append("DRAF AKTIVITI BERASASKAN TEKS SP (" + draft["sp_basis"] + "); SEMAKAN EDITORIAL WAJIB. Bukan petikan buku teks/RPT.")
            else:
                lines.append("AMARAN KUALITI: aktiviti masih templat umum; semakan editorial wajib. Skop SP cadangan memerlukan aktiviti baharu yang disemak.")
        lines.extend(phases)
        if e["assessment_note"]:
            lines.append("Nota pentaksiran sumber RPT: " + e["assessment_note"])
        if page:
            lines.append("Rujukan buku teks (padanan perlu semakan): m/s " + str(page["textbook_page"]) + " [" + page["match_status"] + "]")
        if entry_id == 2279 and mode == "preview":
            proposal = c.execute("SELECT standard_code,standard_text FROM pjpk_v49_verified_additive_link WHERE entry_id=?", (entry_id,)).fetchone()
            if proposal:
                lines.append("SP tambahan disokong tiga sumber (BELUM ditulis pada pautan asal): " + proposal["standard_code"] + " — " + proposal["standard_text"])
        lines.append("Status: " + ("LULUS GATE" if g["ready"] else "DISEKAT DARIPADA PRODUKSI — " + g["reason"]))
        return "\n\n".join(lines)
