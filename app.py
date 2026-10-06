"""
CikguLaju Jadual Saya — Stage 4
Zero Gemini confirmation/save layer.

This module is deliberately separate from app.py until parser QA is complete.
It defines the production UX contract and non-destructive persistence model.
"""

CONFIRM_BUTTONS = [
    ("✅ Simpan Jadual", "tt_confirm_save"),
    ("✏️ Betulkan", "tt_edit"),
    ("🔄 Baca Semula", "tt_reparse"),
    ("❌ Batal", "tt_cancel"),
]

def confirmation_summary(entries):
    lines=["📅 <b>Jadual berjaya dibaca</b>",""]
    for e in entries:
        subject=e.get("subject") or "⚠️ Subjek belum pasti"
        klass=e.get("class_name") or "⚠️ Kelas belum pasti"
        lines.append(
            f"{e['day_name']} {e['start_time']}–{e['end_time']} · "
            f"{subject} · {klass}"
        )
    lines += ["","Semak dahulu. Jadual hanya disimpan selepas cikgu tekan ✅ Simpan Jadual."]
    return "\n".join(lines)

def should_require_confirmation(entry):
    return (
        not entry.get("subject")
        or not entry.get("class_name")
        or float(entry.get("confidence") or 0) < 0.80
    )

def activate_new_timetable(conn, telegram_user_id, timetable_id):
    # Non-destructive: preserve history; only switch active version.
    conn.execute(
        "UPDATE user_timetables SET is_active=0 WHERE telegram_user_id=? AND id<>?",
        (str(telegram_user_id), int(timetable_id))
    )
    conn.execute(
        "UPDATE user_timetables SET is_active=1 WHERE id=?",
        (int(timetable_id),)
    )
    conn.commit()


# ===== Stage 5: RPH HARI INI resolver =====
DAY_MAP = {
    0:"Isnin", 1:"Selasa", 2:"Rabu", 3:"Khamis",
    4:"Jumaat", 5:"Sabtu", 6:"Ahad"
}

def _minutes(hhmm):
    h,m=map(int,hhmm.split(":"))
    return h*60+m

def active_timetable_id(conn, telegram_user_id):
    row=conn.execute(
        """SELECT id FROM user_timetables
           WHERE telegram_user_id=? AND is_active=1
           ORDER BY version DESC,id DESC LIMIT 1""",
        (str(telegram_user_id),)
    ).fetchone()
    return row[0] if row else None

def lessons_for_day(conn, telegram_user_id, day_name):
    tid=active_timetable_id(conn,telegram_user_id)
    if not tid:
        return []
    rows=conn.execute(
        """SELECT id,day_name,start_time,end_time,subject,class_name,
                  confidence,needs_confirmation
           FROM user_timetable_entries
           WHERE timetable_id=? AND day_name=?
           ORDER BY start_time""",
        (tid,day_name)
    ).fetchall()
    keys=("entry_id","day_name","start_time","end_time","subject",
          "class_name","confidence","needs_confirmation")
    return [dict(zip(keys,r)) for r in rows]

def resolve_rph_today(conn, telegram_user_id, now=None):
    """No AI call. Uses confirmed timetable + local date/time only."""
    now=now or datetime.datetime.now()
    day=DAY_MAP[now.weekday()]
    lessons=lessons_for_day(conn,telegram_user_id,day)
    if not lessons:
        return {"status":"no_lesson","day":day,"lessons":[]}

    current=now.hour*60+now.minute
    for e in lessons:
        if _minutes(e["start_time"]) <= current < _minutes(e["end_time"]):
            return {"status":"current","day":day,"lesson":e,"lessons":lessons}

    upcoming=[e for e in lessons if _minutes(e["start_time"])>current]
    if upcoming:
        return {"status":"next","day":day,"lesson":upcoming[0],"lessons":lessons}
    return {"status":"finished","day":day,"lessons":lessons}

def rph_today_message(result):
    status=result["status"]
    day=result["day"]
    if status in ("current","next"):
        e=result["lesson"]
        lead="📍 Kelas sekarang" if status=="current" else "⏭️ Kelas seterusnya"
        subject=e.get("subject") or "Subjek belum disahkan"
        klass=e.get("class_name") or "Kelas belum disahkan"
        return (
            f"⚡ <b>RPH HARI INI · {day}</b>\n\n"
            f"{lead}\n"
            f"🕐 {e['start_time']}–{e['end_time']}\n"
            f"📚 {subject}\n"
            f"👥 {klass}\n\n"
            "Pilih PdP untuk terus jana RPH."
        )
    if status=="finished":
        return f"✅ Semua kelas dalam jadual {day} telah selesai."
    return f"📭 Tiada kelas ditemui dalam jadual untuk {day}."

RPH_TODAY_BUTTONS = [
    ("⚡ Jana RPH", "rph_today_generate"),
    ("📚 Pilih PdP Lain", "rph_today_other_pdp"),
    ("📅 Jadual Saya", "timetable_menu"),
]
# ===== End Stage 5 =====


# ===== Stage 6: timetable -> verified CikguLaju curriculum context =====
import re as _tt_re

SUBJECT_CANONICAL = {
 "BI":"Bahasa Inggeris","BAHASA INGGERIS":"Bahasa Inggeris","ENGLISH":"Bahasa Inggeris",
 "BM":"Bahasa Melayu","BAHASA MELAYU":"Bahasa Melayu",
 "MT":"Matematik","MAT":"Matematik","MATEMATIK":"Matematik",
 "SN":"Sains","SAINS":"Sains",
 "PI":"Pendidikan Islam","PAI":"Pendidikan Islam","PENDIDIKAN ISLAM":"Pendidikan Islam",
 "PM":"Pendidikan Moral","PENDIDIKAN MORAL":"Pendidikan Moral",
}

def normalize_subject(label):
    s=_tt_re.sub(r'\s+',' ',str(label or '').strip()).upper()
    return SUBJECT_CANONICAL.get(s)

def infer_grade_from_class(class_name):
    s=_tt_re.sub(r'\s+',' ',str(class_name or '').strip())
    m=_tt_re.search(r'\bTingkatan\s*([1-5])\b',s,_tt_re.I)
    if m: return f"Tingkatan {m.group(1)}"
    m=_tt_re.search(r'\bTahun\s*([1-6])\b',s,_tt_re.I)
    if m: return f"Tahun {m.group(1)}"
    m=_tt_re.match(r'^\s*([1-6])\b',s)
    if m: return f"Tahun {m.group(1)}"
    return None

def curriculum_context_from_timetable(entry):
    subject=normalize_subject(entry.get("subject"))
    grade=infer_grade_from_class(entry.get("class_name"))
    missing=[]
    if not subject: missing.append("subject")
    if not grade: missing.append("grade")
    return {"subject":subject,"grade":grade,"class_name":entry.get("class_name"),
            "ready_for_pdp_lookup":not missing,"missing":missing}

def prepare_rph_today_pdp_lookup(entry):
    ctx=curriculum_context_from_timetable(entry)
    if not ctx["ready_for_pdp_lookup"]:
        return {"status":"needs_confirmation","context":ctx}
    return {"status":"lookup_verified_curriculum","context":ctx}

RPH_TODAY_CONTEXT_BUTTONS=[
 ("📖 Pilih PdP","rph_today_verified_pdp"),
 ("✏️ Betulkan Kelas/Subjek","rph_today_fix_context"),
 ("⬅️ Kembali","rph_today_back"),
]
# ===== End Stage 6 =====


# ===== Stage 7: smart PdP ranking — verified rows only =====
# This layer NEVER creates a PdP. It only ranks rows returned by the existing
# verified CikguLaju curriculum/RPT/SOW database.

def _week_distance(row, target_week):
    wf=row.get("week_from")
    wt=row.get("week_to")
    try:
        wf=int(wf) if wf is not None else None
        wt=int(wt) if wt is not None else wf
    except Exception:
        return 999
    if wf is None: return 999
    if wf <= target_week <= (wt if wt is not None else wf): return 0
    if target_week < wf: return wf-target_week
    return target_week-(wt if wt is not None else wf)

def rank_verified_pdp_rows(rows, target_week=None, last_sequence=None, limit=6):
    """
    rows: VERIFIED rows already fetched for exact grade + subject.
    Ranking preference:
      1) RPT/SOW week match, when verified week fields exist;
      2) next sequence after user's last generated PdP;
      3) stable sequence order.
    No row is synthesized.
    """
    rows=[dict(r) for r in rows if r]
    def seq(r):
        try: return int(r.get("sequence_no"))
        except Exception: return 10**9
    def key(r):
        wd=_week_distance(r,target_week) if target_week is not None else 999
        s=seq(r)
        if last_sequence is None:
            progress=0
        else:
            progress=0 if s>int(last_sequence) else 1
        return (wd,progress,s)
    ranked=sorted(rows,key=key)
    return ranked[:max(1,int(limit))]

def smart_pdp_menu_text(context, ranked_rows):
    grade=context.get("grade") or "—"
    subject=context.get("subject") or "—"
    lines=[
        "⚡ <b>RPH HARI INI</b>",
        f"🎓 {grade}",
        f"📚 {subject}",
        "",
        "PdP yang paling relevan diletakkan di atas:",
    ]
    for i,r in enumerate(ranked_rows,1):
        n=r.get("sequence_no")
        title=(r.get("title") or r.get("topic") or r.get("lesson_title") or "").strip()
        label=f"PdP {n}" if n not in (None,"") else "PdP"
        if title: label+=f" · {title}"
        lines.append(f"{i}. {label}")
    lines += ["","Cikgu masih boleh pilih PdP lain."]
    return "\n".join(lines)

def smart_pdp_buttons(ranked_rows):
    buttons=[]
    for r in ranked_rows:
        row_id=r.get("id") or r.get("pdp_id") or r.get("sequence_no")
        n=r.get("sequence_no")
        title=(r.get("title") or r.get("topic") or r.get("lesson_title") or "").strip()
        label=f"⚡ PdP {n}" if n not in (None,"") else "⚡ PdP"
        if title:
            short=title if len(title)<=28 else title[:27]+"…"
            label+=f" · {short}"
        buttons.append((label,f"rph_today_pdp|{row_id}"))
    buttons.append(("📚 Lihat Semua PdP","rph_today_all_pdp"))
    buttons.append(("⬅️ Kembali","rph_today_back"))
    return buttons

CIKGULAJU_TIMETABLE_STAGE7="SMART_PDP_RANKING_VERIFIED_ROWS_ONLY"
# ===== End Stage 7 =====


# ===== Stage 8: one-tap daily RPH orchestration =====
# Still separate from main app.py. No Gemini used for timetable/suggestion logic.

def build_rph_today_action(conn, telegram_user_id, verified_pdp_fetcher,
                           target_week=None, last_sequence=None, now=None):
    """
    verified_pdp_fetcher(grade, subject) must return rows from the EXISTING
    verified CikguLaju curriculum DB only.
    """
    resolved=resolve_rph_today(conn,telegram_user_id,now=now)
    if resolved["status"] not in ("current","next"):
        return {"status":resolved["status"],"message":rph_today_message(resolved)}

    entry=resolved["lesson"]
    bridge=prepare_rph_today_pdp_lookup(entry)
    if bridge["status"]!="lookup_verified_curriculum":
        return {
            "status":"needs_confirmation",
            "message":"⚠️ Kelas/subjek perlu disahkan dahulu.",
            "entry":entry
        }

    ctx=bridge["context"]
    rows=list(verified_pdp_fetcher(ctx["grade"],ctx["subject"]) or [])
    if not rows:
        return {
            "status":"no_verified_pdp",
            "message":"⚠️ Tiada PdP verified ditemui untuk pilihan ini.",
            "context":ctx
        }

    ranked=rank_verified_pdp_rows(
        rows,target_week=target_week,last_sequence=last_sequence,limit=5
    )
    return {
        "status":"ready",
        "context":ctx,
        "entry":entry,
        "ranked_pdp":ranked,
        "message":smart_pdp_menu_text(ctx,ranked),
        "buttons":smart_pdp_buttons(ranked)
    }

def select_verified_pdp_for_rph(selected_id, verified_rows):
    """
    Security/QA gate: callback id must exist in the verified rows that were
    actually offered. Prevents fabricated/arbitrary PdP ids.
    """
    sid=str(selected_id)
    for row in verified_rows:
        rid=row.get("id") or row.get("pdp_id") or row.get("sequence_no")
        if str(rid)==sid:
            return dict(row)
    return None

def minimal_home_buttons(has_confirmed_timetable=True):
    buttons=[]
    if has_confirmed_timetable:
        buttons.append(("⚡ RPH HARI INI","rph_today"))
    buttons += [
        ("📚 PILIH RPH LAIN","rph_manual"),
        ("📅 JADUAL SAYA","timetable_menu"),
        ("⚙️ TETAPAN","settings"),
    ]
    return buttons

def after_pdp_selected_payload(entry, context, pdp):
    """
    Payload bridge for the EXISTING RPH generator.
    Does not replace or rewrite the current RPH engine.
    """
    return {
        "source":"rph_today",
        "class_name":entry.get("class_name"),
        "grade":context.get("grade"),
        "subject":context.get("subject"),
        "pdp_id":pdp.get("id") or pdp.get("pdp_id"),
        "sequence_no":pdp.get("sequence_no"),
        "verified_pdp":True,
    }

CIKGULAJU_TIMETABLE_STAGE8="ONE_TAP_DAILY_RPH_ORCHESTRATION"
# ===== End Stage 8 =====

# ===== Stage 9: first manual, then suggest next verified PdP =====
PROGRESS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_rph_progress (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_user_id TEXT NOT NULL, grade TEXT NOT NULL, subject TEXT NOT NULL,
 class_name TEXT, last_pdp_id TEXT, last_sequence_no INTEGER,
 generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(telegram_user_id,grade,subject,class_name)
);
CREATE INDEX IF NOT EXISTS idx_rph_progress_user
ON user_rph_progress(telegram_user_id,grade,subject,class_name);
"""
def _ensure_progress_schema(conn):
    conn.executescript(PROGRESS_SCHEMA_SQL)

def save_generated_rph_progress(conn, telegram_user_id, context, pdp):
    seq=pdp.get("sequence_no")
    if seq is None: return False
    _ensure_progress_schema(conn)
    conn.execute("""INSERT INTO user_rph_progress
      (telegram_user_id,grade,subject,class_name,last_pdp_id,last_sequence_no,generated_at)
      VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)
      ON CONFLICT(telegram_user_id,grade,subject,class_name) DO UPDATE SET
      last_pdp_id=excluded.last_pdp_id,last_sequence_no=excluded.last_sequence_no,
      generated_at=CURRENT_TIMESTAMP""",
      (str(telegram_user_id),context.get("grade"),context.get("subject"),
       context.get("class_name"),str(pdp.get("id") or pdp.get("pdp_id") or ""),int(seq)))
    conn.commit(); return True

def get_last_rph_progress(conn, telegram_user_id, grade, subject, class_name=None):
    _ensure_progress_schema(conn)
    if class_name:
        row=conn.execute("""SELECT last_pdp_id,last_sequence_no,generated_at
          FROM user_rph_progress WHERE telegram_user_id=? AND grade=? AND subject=?
          AND class_name=? LIMIT 1""",(str(telegram_user_id),grade,subject,class_name)).fetchone()
    else:
        row=conn.execute("""SELECT last_pdp_id,last_sequence_no,generated_at
          FROM user_rph_progress WHERE telegram_user_id=? AND grade=? AND subject=?
          ORDER BY generated_at DESC LIMIT 1""",(str(telegram_user_id),grade,subject)).fetchone()
    return None if not row else {"last_pdp_id":row[0],"last_sequence_no":row[1],"generated_at":row[2]}

def next_verified_pdp(verified_rows,last_sequence_no):
    if last_sequence_no is None: return None
    c=[]
    for r in verified_rows:
        try: seq=int(r.get("sequence_no"))
        except Exception: continue
        if seq>int(last_sequence_no): c.append((seq,dict(r)))
    return None if not c else sorted(c,key=lambda x:x[0])[0][1]

def manual_or_next_suggestion(conn,telegram_user_id,context,verified_rows):
    p=get_last_rph_progress(conn,telegram_user_id,context.get("grade"),
                            context.get("subject"),context.get("class_name"))
    if not p:
        return {"mode":"manual_first_time","suggested_pdp":None,
                "message":"📚 Pilih PdP untuk RPH pertama."}
    nxt=next_verified_pdp(verified_rows,p["last_sequence_no"])
    if not nxt:
        return {"mode":"manual_no_next","suggested_pdp":None,
                "message":"📚 Pilih PdP secara manual."}
    return {"mode":"suggest_next","previous_sequence":p["last_sequence_no"],
            "suggested_pdp":nxt,
            "message":f"✨ RPH terakhir: PdP {p['last_sequence_no']}\nCadangan seterusnya: PdP {nxt.get('sequence_no')}",
            "buttons":[(f"⚡ Jana PdP {nxt.get('sequence_no')}",
                        f"rph_today_pdp|{nxt.get('id') or nxt.get('pdp_id') or nxt.get('sequence_no')}"),
                       ("📚 Pilih PdP Lain","rph_today_all_pdp")]}
CIKGULAJU_TIMETABLE_STAGE9="FIRST_MANUAL_THEN_NEXT_VERIFIED_PDP"
# ===== End Stage 9 =====


# ===== Stage 10: DAILY RPH DASHBOARD =====
# Goal: prepare all teaching slots for today in a few taps.
# Uses schedule + saved RPH progress + verified curriculum rows only.

def build_daily_rph_dashboard(conn, telegram_user_id, verified_fetcher, day_name,
                              target_week=None):
    lessons=lessons_for_day(conn,telegram_user_id,day_name)
    teaching=[e for e in lessons if e.get("subject") and e.get("class_name")]
    result=[]
    # Virtual progress prevents duplicate suggestion when same class/subject occurs twice today.
    virtual_last={}

    for e in teaching:
        ctx=curriculum_context_from_timetable(e)
        if not ctx["ready_for_pdp_lookup"]:
            result.append({"entry":e,"context":ctx,"mode":"needs_confirmation"})
            continue

        rows=list(verified_fetcher(ctx["grade"],ctx["subject"]) or [])
        key=(ctx["grade"],ctx["subject"],ctx["class_name"])
        progress=get_last_rph_progress(conn,telegram_user_id,*key)

        last_seq=virtual_last.get(key)
        if last_seq is None and progress:
            last_seq=progress["last_sequence_no"]

        if last_seq is None:
            result.append({
                "entry":e,"context":ctx,"mode":"manual_first_time",
                "suggested_pdp":None
            })
            continue

        nxt=next_verified_pdp(rows,last_seq)
        if not nxt:
            result.append({
                "entry":e,"context":ctx,"mode":"manual_no_next",
                "suggested_pdp":None
            })
            continue

        virtual_last[key]=nxt.get("sequence_no")
        result.append({
            "entry":e,"context":ctx,"mode":"suggest_next",
            "previous_sequence":last_seq,"suggested_pdp":nxt
        })
    return result

def daily_dashboard_message(day_name, items):
    lines=[f"⚡ <b>RPH HARI INI · {day_name}</b>",""]
    for item in items:
        e=item["entry"]; ctx=item["context"]
        head=f"🕐 {e['start_time']}–{e['end_time']} · {ctx.get('subject') or 'Subjek?'} · {ctx.get('class_name') or 'Kelas?'}"
        lines.append(head)
        if item["mode"]=="suggest_next":
            p=item["suggested_pdp"]
            lines.append(f"   ✨ Cadangan: PdP {p.get('sequence_no')}")
        elif item["mode"]=="manual_first_time":
            lines.append("   🆕 Pilih PdP pertama")
        else:
            lines.append("   ⚠️ Semak / pilih PdP")
    lines += ["","Pilih cadangan atau ubah mana-mana PdP sebelum jana."]
    return "\n".join(lines)

def daily_dashboard_buttons(items):
    buttons=[]
    for i,item in enumerate(items):
        e=item["entry"]
        if item["mode"]=="suggest_next":
            p=item["suggested_pdp"]
            rid=p.get("id") or p.get("pdp_id") or p.get("sequence_no")
            buttons.append((f"⚡ {e['start_time']} · PdP {p.get('sequence_no')}",
                            f"daily_rph_pick|{i}|{rid}"))
        else:
            buttons.append((f"📚 {e['start_time']} · Pilih PdP",
                            f"daily_rph_manual|{i}"))
    # Batch action appears only after every teaching slot has a selected/confirmed PdP.
    buttons += [
        ("✅ Semak Pilihan Hari Ini","daily_rph_review"),
        ("📚 Pilih RPH Lain","rph_manual"),
        ("📅 Jadual Saya","timetable_menu"),
    ]
    return buttons

def can_generate_daily_batch(items):
    return bool(items) and all(
        x.get("mode")=="suggest_next" and x.get("suggested_pdp")
        for x in items
    )

CIKGULAJU_TIMETABLE_STAGE10="DAILY_RPH_DASHBOARD_FEW_TAPS"
# ===== End Stage 10 =====
