"""Profile cover must preserve original cover outside the three approved slots."""
import io
import json
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import fitz
from PIL import Image, ImageDraw, ImageChops
from docx import Document
from docx.shared import Cm
from web.rpt_native_word_cover import cover_png, add_word_cover, selected_layout, personalized_word

ROOT=Path("rpt_2027/web_2027_pdfs")
LOCK=json.loads((ROOT/"original_cover_layout_verified.json").read_text())
MANIFEST=json.loads((ROOT/"manifest.json").read_text())
KEYS=["bahasa_melayu:2","pendidikan_moral:2","pjpk:2","psv:2","muzik:2",
      "rbt:4","sejarah:4","sains:2","matematik:2","bahasa_arab:2","pendidikan_islam:2","english:2"]
def png():
    out=io.BytesIO()
    Image.new("RGB",(40,40),"#295c3c").save(out,format="PNG")
    return out.getvalue()
IDENTITY={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"CIKGU CONTOH","state":"","logo":png()}
def source(key):
    e=MANIFEST["files"][key]
    raw=(ROOT/e["path"]).read_bytes()
    assert sha256(raw).hexdigest()==e["sha256"]
    return raw

class NativeWordCover(unittest.TestCase):
    def test_twelve_subject_cover_graphics_and_profile_slots(self):
        for key in KEYS:
            with self.subTest(key=key):
                raw=source(key)
                layout=selected_layout(LOCK,key,sha256(raw).hexdigest())
                plain=cover_png(raw,LOCK,key)
                filled=cover_png(raw,LOCK,key,IDENTITY)
                with fitz.open(stream=raw,filetype="pdf") as original:
                    reference=Image.open(io.BytesIO(original[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png"))).convert("RGB")
                before=Image.open(io.BytesIO(plain)).convert("RGB")
                after=Image.open(io.BytesIO(filled)).convert("RGB")
                self.assertIsNone(ImageChops.difference(reference,before).getbbox())
                diff=ImageChops.difference(before,after)
                self.assertIsNotNone(diff.getbbox())
                for name in ("logo_interior_top_left","school_row_top_left","teacher_row_top_left"):
                    box=tuple(int(x*2) for x in layout[name])
                    self.assertIsNotNone(diff.crop(box).getbbox(),name)
                draw=ImageDraw.Draw(diff)
                for name in ("logo_interior_top_left","school_row_top_left","teacher_row_top_left"):
                    x0,y0,x1,y1=layout[name]
                    draw.rectangle((int(x0*2)-2,int(y0*2)-2,int(x1*2)+2,int(y1*2)+2),fill=(0,0,0))
                self.assertIsNone(diff.getbbox(),"Pixels outside approved cover slots changed")
    def test_paid_word_only_and_native_table_unchanged(self):
        key="bahasa_melayu:2";raw=source(key)
        doc=Document();sec=doc.sections[0]
        sec.page_width=Cm(29.7);sec.page_height=Cm(21)
        add_word_cover(doc,cover_png(raw,LOCK,key))
        table=doc.add_table(rows=2,cols=2);table.cell(1,1).text="PdP 001"
        out=io.BytesIO();doc.save(out);original=out.getvalue()
        with patch("web.rpt_school_cover.school_identity",return_value=IDENTITY) as resolve:
            with self.assertRaises(PermissionError):
                personalized_word(original,raw,LOCK,key,{"telegram_user_id":1,"free_generations_remaining":10},{})
            resolve.assert_not_called()
            result=personalized_word(original,raw,LOCK,key,{"telegram_user_id":1,"rakan_pembangun":True},{})
            resolve.assert_called_once_with({},1,allow_teacher_only=True)
        with ZipFile(io.BytesIO(original)) as a,ZipFile(io.BytesIO(result)) as b:
            self.assertEqual(a.read("word/document.xml"),b.read("word/document.xml"))
            media=[x for x in a.namelist() if x.startswith("word/media/")]
            self.assertEqual(len(media),1)
            self.assertNotEqual(a.read(media[0]),b.read(media[0]))
            self.assertEqual(b.read(media[0]),cover_png(raw,LOCK,key,IDENTITY))
        self.assertEqual(Document(io.BytesIO(result)).tables[0].cell(1,1).text,"PdP 001")
    def test_unrecognized_source_fails_closed(self):
        with self.assertRaises(ValueError):
            cover_png(b"not verified",LOCK,"bahasa_melayu:2")
if __name__=="__main__":unittest.main()
