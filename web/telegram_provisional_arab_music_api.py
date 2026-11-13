"""Private source-linked preview of Bahasa Arab and Pendidikan Muzik RPH.

These are DRAF materials for teacher review, NEVER official approved content.
Sources are immutable copies from distinct reviewed staging branches, co-located
with Telegram, not Web-side rewrites. No DB access, token leaks, AI, audio,
student data or quota mutation. All user-facing documents display DRAF.
"""
from __future__ import annotations
import csv
import hashlib
import io
import os
import re
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

from flask import Blueprint, Response, jsonify, request

from web.native_rph_telegram_api import MIMES, compact_web_word_notes
from web.rph_teacher_reflection import clean_reflection
from web.telegram_verified_rpt_rph_bridge import _authorization, _teacher_metadata

ROOT = Path(__file__).resolve().parents[1]
AR = ROOT / "rph_standalone" / "bahasa_arab"
MU = ROOT / "staging" / "pendidikan_muzik" / "rpt_rph_2027"
INDEX = ROOT / "rpt_2027" / "bahasa_arab"
SOURCE = "telegram-provisional-subjects-2027-v1"
MAX_FILE = 15 * 1024 * 1024
NUM = re.compile(r"(?:00[1-9]|0[1-9]\d|[1-2]\d\d|3\d\d)")
UNIT = re.compile(r"u(?:0[1-9]|[1-9][0-9])|x[a-f0-9]{12}")
EXPECTED = {2:60,3:60,4:58,5:60,6:60}
SUBJECTS = {"ARAB":"Bahasa Arab", "MUZIK":"Pendidikan Muzik"}


def _check(year, subject, unit=None, lesson=None):
    if type(year) is not int or year not in EXPECTED or subject not in SUBJECTS:
        raise ValueError("Unsupported draft subject/year")
    if unit is not None and (not isinstance(unit,str) or not UNIT.fullmatch(unit)):
        raise ValueError("Invalid draft unit")
    if lesson is not None and (not isinstance(lesson,str) or not NUM.fullmatch(lesson)):
        raise ValueError("Invalid draft PdP")
    return year


@lru_cache(maxsize=1)
def _arab_index():
    index_path = INDEX / "rpt_2027_KUMPULAN_A_INDEKS_PDP_DRAF.csv"
    with index_path.open(encoding="utf-8-sig", newline="") as f:
        data = list(csv.DictReader(f))
    with (INDEX / "unit_sequence_DRAF_20261105.csv").open(
            encoding="utf-8-sig", newline="") as f:
        units = {(int(row["tahun"]),int(row["unit"])):row["tajuk_arab"]
                 for row in csv.DictReader(f)}
    if len(units)!=20 or len(data)!=298:
        raise ValueError("Incomplete Arabic draft catalogue")
    result = {}
    for row in data:
        year = int(row["tahun"])
        pdp = int(row["pdp"])
        unit = int(row["unit"])
        if (year not in EXPECTED or not 1<=unit<=4
                or not 1<=pdp<=EXPECTED[year]
                or row["rph_staging"]!=f"rph_standalone/bahasa_arab/year{year}/lesson_{pdp:03d}.md"
                or row["ready"].strip().upper()!="FALSE"
                or row["kelulusan_guru"].strip().upper()!="FALSE"
                or not row["status_rpt"].startswith("DRAF")
                or (year,pdp) in result or (year,unit) not in units):
            raise ValueError("Unsafe Arabic draft source metadata")
        path = AR / f"year{year}" / f"lesson_{pdp:03d}.md"
        if path.is_symlink() or not path.is_file() or path.stat().st_size>80000:
            raise ValueError("Missing Arabic draft RPH")
        result[(year,pdp)] = dict(row, source_path=path, unit_name=units[(year,unit)])
    if any(sum(y==year for y,_ in result)!=count for year,count in EXPECTED.items()):
        raise ValueError("Arabic draft inventory count mismatch")
    return result


@lru_cache(maxsize=5)
def _music_index(year):
    import json
    _check(year,"MUZIK")
    file = MU / f"year{year}" / "pdp_manifest.json"
    if file.is_symlink():
        raise ValueError("Unsafe Music path")
    obj=json.loads(file.read_text("utf8"))
    rows=obj["pdps"]
    if len(rows)!=35 or "DRAF" not in obj.get("status",""):
        raise ValueError("Incomplete Music draft")
    if any(obj.get(k) is not False for k in
           ("textbook_verified","audio_verified","rph_word_pdf_verified")):
        raise ValueError("Music release flags are not draft")
    for n,row in enumerate(rows,1):
        if (row["pdp"]!=n or row["pdp_id"]!=f"MZ-Y{year}-{n:02d}"
                or not isinstance(row["unit"],str) or not row["unit"].strip()
                or not (MU/f"year{year}"/f"rph_pdp_{n:02d}.md").is_file()):
            raise ValueError("Music source identity mismatch")
    return rows


def _music_key(row):
    code=row.get("unit_number")
    name=row["unit"]
    if isinstance(code,int) and code>0:
        return f"u{code:02d}"
    return "x"+hashlib.sha256(name.encode("utf8")).hexdigest()[:12]


def _unit_rows(year, subject):
    _check(year,subject)
    if subject=="ARAB":
        rows=[(f"u{i:02d}", f"Unit {i}: {next(r['unit_name'] for (y,n),r in _arab_index().items() if y==year and int(r['unit'])==i)}")
              for i in range(1,5)]
    else:
        rows=[]
        for row in _music_index(year):
            code=_music_key(row)
            num=row.get("unit_number")
            label=(f"Unit {num}: " if isinstance(num,int) and num>0 else "")+row["unit"]
            if code not in {k for k,_ in rows}:
                rows.append((code,label))
    if not rows or len(set(k for k,_ in rows))!=len(rows):
        raise ValueError("Unavailable draft units")
    return [{"value":u,"label":label,"status":"DRAF"} for u,label in rows]


def _lesson_rows(year,subject,unit):
    _check(year,subject,unit)
    if unit not in {x["value"] for x in _unit_rows(year,subject)}:
        raise ValueError("Draft unit not found")
    rows=[]
    if subject=="ARAB":
        for (y,pdp),row in _arab_index().items():
            if y!=year or f"u{int(row['unit']):02d}"!=unit:
                continue
            focus=row["fokus"].strip()
            item={"value":f"{pdp:03d}","label":f"PdP {pdp:03d} — {focus} (DRAF)",
                  "status":"DRAF","formats":["word"]}
            # Source mapping is preliminary. Never call it visually verified.
            if row["halaman_buku"].strip():
                item["textbook_ref"]="Buku Teks m/s "+row["halaman_buku"]+" (rujukan DRAF)"
            rows.append(item)
    else:
        for row in _music_index(year):
            if _music_key(row)!=unit:
                continue
            pdp=row["pdp"]
            title=(row.get("focus_pdp") or row["unit"]).strip()
            item={"value":f"{pdp:03d}","label":f"PdP {pdp:03d} — {title} (DRAF)",
                  "status":"DRAF","formats":["word","pdf"]}
            if (row.get("page") and row.get("pdp_kind")!="CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI"):
                item["textbook_ref"]="Buku Teks m/s "+str(row["page"])+" (rujukan DRAF)"
            rows.append(item)
    if not rows:
        raise ValueError("No source-backed draft PdP")
    return rows


def _selected(year,subject,unit,lesson):
    _check(year,subject,unit,lesson)
    if lesson not in {x["value"] for x in _lesson_rows(year,subject,unit)}:
        raise ValueError("Stale draft PdP selection")
    n=int(lesson)
    if subject=="ARAB":
        from scripts.render_bahasa_arab_staging import fields,first,display_sk_sp
        row=_arab_index()[(year,n)]
        raw=row["source_path"].read_text("utf8")
        title,f=fields(raw)
        display_sk_sp(first(f,"DSKP SK/SP","Kod SK/SP","SK/SP cadangan"))
        if "DRAF" not in raw or len(raw)<650 or len(first(f,"Aktiviti 1"))<60:
            raise ValueError("Arabic draft content incomplete")
        return {"year":year,"subject":subject,"unit":unit,"lesson":n,
                "title":title,"source":raw,"fields":f,"formats":["word"],
                "source_path":row["source_path"]}
    from staging.pendidikan_muzik.rpt_rph_2027.music_native_route_candidate import load
    item=load(year,n,root=MU)
    if item is None:
        raise ValueError("Unverified Music draft source")
    return {"year":year,"subject":subject,"unit":unit,"lesson":n,
            "title":item["title"],"music":item,"formats":["word","pdf"]}


def _music_state(selected,teacher):
    year=selected["year"]
    layout=selected["music"]["preview"]["layout"]
    fields={r["label"]:r["value"] for r in layout["header"]}
    cls,dt,tm,pupils,day=_teacher_metadata(teacher,"MUZIK")
    sk=selected["music"]["sk"]
    sp=selected["music"]["sp"]
    state={"task":"rph","quick_material_flow":True,
           "year":f"Tahun {year}","year_label":f"Tahun {year}",
           "subject":"Pendidikan Muzik",
           "topic":"DRAF CADANGAN — "+selected["title"],
           "unit":selected["title"],"unit_title":selected["title"],
           "subtopic":"","lesson_no":str(selected["lesson"]),
           "pdp_no":selected["lesson"],
           "sk_code":sk[0],"sp_code":sp[0],
           "selected_sk_codes":list(sk),"grouped_sk_codes":list(sk),
           "selected_sp_codes":list(sp),"grouped_sp_codes":list(sp),
           "rph_class":cls,
           "rph_date":__import__("datetime").date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else "",
           "rph_day":day,"rph_time":tm,"rph_students":pupils,
           "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
           "variation_seed":"muzik-source-"+selected["music"]["digest"][:20]}
    sections={
        "STANDARD KANDUNGAN":fields["Standard Kandungan"],
        "STANDARD PEMBELAJARAN":fields["Standard Pembelajaran"],
        "OBJEKTIF PEMBELAJARAN":fields["OBJEKTIF PEMBELAJARAN"],
        "KRITERIA KEJAYAAN":fields["KRITERIA KEJAYAAN"],
        "PENGETAHUAN SEDIA ADA":fields["PENGETAHUAN SEDIA ADA"],
        "BAHAN BANTU MENGAJAR":fields["BAHAN BANTU MENGAJAR"],
        "EMK / NILAI":fields["EMK / NILAI"],
        "KBAT / PAK21":fields["KBAT / PAK21"],
        "PENTAKSIRAN":fields["PENTAKSIRAN"],
        "SET INDUKSI":layout["phases"][0]["activity"],
        "AKTIVITI UTAMA":layout["phases"][1]["activity"],
        "PENUTUP":layout["phases"][2]["activity"],
        "PEMULIHAN / PENGAYAAN":layout["footer"][0]["value"],
        "REFLEKSI":layout["footer"][1]["value"],
    }
    from staging.pendidikan_muzik.rpt_rph_2027.legacy_doc_text_safe_staging import (
        normalize_for_legacy_doc,
    )
    # Legacy Telegram clean_doc_text silently drops em/en dashes, which
    # changes textbook page ranges; normalize known punctuation BEFORE
    # native parsing and reject every unsupported glyph.
    text=normalize_for_legacy_doc(
        "\n".join(name+":\n"+str(v)+"\n" for name,v in sections.items()))
    return state,text


def _arab_word(selected,teacher,dest):
    from scripts.render_bahasa_arab_staging import render_one
    from docx import Document
    from docx.shared import Pt
    cls,dt,tm,pupils,day=_teacher_metadata(teacher,"ARAB")
    generated=render_one(selected["source"],dest)
    if not generated["valid_struct"] or not generated["arabic"]:
        raise ValueError("Arabic Word source failed quality guard")
    doc=Document(dest)
    if len(doc.tables)!=1 or not doc.paragraphs:
        raise ValueError("Arabic Word structure invalid")
    doc.paragraphs[0].add_run(" • DRAF UNTUK SEMAKAN GURU").bold=True
    reflection = clean_reflection(teacher.get("reflection", ""))
    for row in doc.tables[0].rows:
        caption = row.cells[0].text.strip()
        if caption=="Tarikh / Masa / Kelas":
            value=(
                "Tarikh: "+(__import__("datetime").date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else "___/___/_____")
                +"   Masa: "+(tm or "________")
                +"   Kelas: "+(cls or "________")
                +"   Murid: "+(pupils or "_____"))
            row.cells[1].text=value
        elif caption == "Refleksi" and reflection:
            row.cells[1].text = reflection
            reflection = ""
    if reflection:
        cells = doc.tables[0].add_row().cells
        cells[0].text = "Refleksi"
        cells[1].text = reflection
    doc.save(dest)
    return dest


def create_provisional_subjects_blueprint(runtime):
    if not callable(getattr(runtime,"create_word_file",None)) or not callable(getattr(runtime,"create_pdf_file",None)):
        raise TypeError("Native Telegram document generator not ready")
    bp=Blueprint("telegram_provisional_other_subjects_2027",__name__)

    @bp.after_request
    def private(resp):
        resp.headers["Cache-Control"]="no-store, private"
        resp.headers["Vary"]="Authorization"
        resp.headers["X-Content-Type-Options"]="nosniff"
        return resp

    @bp.before_request
    def auth():
        if not _authorization():
            return jsonify({"error":"Unauthorized"}),401

    def _query(expected):
        if set(request.args)!=expected or any(len(request.args.getlist(k))!=1 for k in expected):
            raise ValueError("Invalid request keys")
        year=int(request.args["year"]) if re.fullmatch(r"[2-6]",request.args["year"]) else -1
        subject=request.args["subject"]
        _check(year,subject,request.args.get("unit"),request.args.get("lesson"))
        return year,subject

    @bp.get("/internal/rph/v1/other-drafts/units")
    def units():
        try:
            year,subject=_query({"year","subject"})
            items=_unit_rows(year,subject)
        except (OSError,ValueError,KeyError,ImportError):
            return jsonify({"error":"Draft units unavailable"}),503
        return jsonify({"source":SOURCE,"status":"DRAF","items":items})

    @bp.get("/internal/rph/v1/other-drafts/lessons")
    def lessons():
        try:
            year,subject=_query({"year","subject","unit"})
            items=_lesson_rows(year,subject,request.args["unit"])
        except (OSError,ValueError,KeyError,ImportError):
            return jsonify({"error":"Draft lessons unavailable"}),503
        return jsonify({"source":SOURCE,"status":"DRAF","items":items})

    @bp.get("/internal/rph/v1/other-drafts/availability")
    def availability():
        try:
            year,subject=_query({"year","subject","unit","lesson"})
            selected=_selected(year,subject,request.args["unit"],request.args["lesson"])
        except (OSError,ValueError,KeyError,ImportError):
            return jsonify({"available":False}),404
        return jsonify({"available":True,"generator":"telegram-native",
                        "status":"DRAF","formats":selected["formats"]})

    @bp.get("/internal/rph/v1/other-drafts/audio-links")
    def audio_links():
        """Original Music source VIEW links only, matched to exact verified PdP."""
        try:
            year,subject=_query({"year","subject","unit","lesson"})
            if subject!="MUZIK":
                return jsonify({"error":"Music only"}),404
            _selected(year,subject,request.args["unit"],request.args["lesson"])
            from staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging import (
                audio_link_action,
            )
            source=audio_link_action(year,int(request.args["lesson"]))
            links=source.get("links",[])
            if not isinstance(links,list) or len(links)>21:
                raise ValueError("Ambiguous music links")
            items=[{"title":item["title"],"url":item["url"],
                    "track":item["track"]} for item in links]
        except (ValueError,TypeError,KeyError,OSError,ImportError):
            return jsonify({"error":"Music audio source not available"}),503
        return jsonify({"source":SOURCE,"status":"DRAF",
                        "available":bool(items),"links":items,
                        "notice":source["notice"],"download_available":False})

    @bp.post("/internal/rph/v1/other-drafts/render")
    def render():
        if (not request.is_json or request.content_length is None
                or request.content_length>7000):
            return jsonify({"error":"Invalid render request"}),400
        data=request.get_json(silent=True)
        if (not isinstance(data,dict) or set(data)!={"selection","teacher","format"}
                or not isinstance(data["selection"],dict)
                or set(data["selection"])!={"year","subject","unit","lesson"}
                or data["format"] not in MIMES):
            return jsonify({"error":"Invalid source selection"}),400
        src=data["selection"]
        try:
            selected=_selected(src["year"],src["subject"],src["unit"],src["lesson"])
            if data["format"] not in selected["formats"]:
                return jsonify({"error":"Draft format not yet verified"}),503
            # Never accept RPH text, SK/SP, digest, file path or author info
            # supplied by Web; only original Telegram-local staged sources.
            _teacher_metadata(data["teacher"],src["subject"])
        except (ValueError,TypeError,KeyError,OSError,ImportError):
            return jsonify({"error":"Draft source unavailable"}),404
        fmt=data["format"]
        unique="web"+uuid.uuid4().hex
        output=None
        try:
            if src["subject"]=="ARAB":
                output=Path(tempfile.gettempdir())/(unique+"_Bahasa_Arab_DRAF.docx")
                _arab_word(selected,data["teacher"],output)
            else:
                state,text=_music_state(selected,data["teacher"])
                parsed=runtime._rph_rows(state,text)
                source=selected["music"]["preview"]["layout"]
                core=source["phases"][1]["activity"]
                sp=selected["music"]["sp"]
                if not isinstance(parsed,dict) or not all(code in parsed.get("STANDARD PEMBELAJARAN","") for code in sp):
                    raise ValueError("Music SP lost in native renderer")
                from staging.pendidikan_muzik.rpt_rph_2027.legacy_doc_text_safe_staging import (
                    normalize_for_legacy_doc,
                )
                # Native RPH rows may collapse paragraph whitespace. Compare
                # all real activities after the same safe punctuation mapping.
                expected=" ".join(normalize_for_legacy_doc(core).split())
                actual=" ".join(str(parsed.get("AKTIVITI UTAMA","")).split())
                if not expected or expected not in actual:
                    raise ValueError("Music RPH source text lost")
                output=(runtime.create_word_file(state,text,unique) if fmt=="word"
                        else runtime.create_pdf_file(state,text,unique))
            path=Path(output).resolve(strict=True)
            if (path.parent!=Path(tempfile.gettempdir()).resolve()
                    or not path.name.startswith(unique+"_")
                    or not 1000<=path.stat().st_size<=MAX_FILE):
                raise ValueError("Unexpected native document")
            body=path.read_bytes()
            if fmt=="word":
                if src["subject"]=="MUZIK":
                    body=compact_web_word_notes(body)
                with ZipFile(io.BytesIO(body)) as z:
                    if z.testzip() or "word/document.xml" not in z.namelist():
                        raise ValueError("Invalid DOCX")
            elif not body.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF")
            resp=Response(body,mimetype=MIMES[fmt])
            resp.headers["Content-Disposition"]=(
                'attachment; filename="CikguLaju_'+src["subject"]+'_DRAF.'
                +("docx" if fmt=="word" else "pdf")+'"')
            return resp
        except (Exception,) as exc:
            print("Draft source render unavailable:",type(exc).__name__,flush=True)
            return jsonify({"error":"Draft document not available"}),503
        finally:
            if output is not None:
                try:
                    path=Path(output).resolve()
                    if path.parent==Path(tempfile.gettempdir()).resolve() and path.name.startswith(unique+"_"):
                        path.unlink(missing_ok=True)
                except (OSError,ValueError):
                    pass
    return bp
