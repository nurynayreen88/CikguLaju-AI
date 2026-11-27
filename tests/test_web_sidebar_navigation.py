"""Regression: RPT has its own sidebar view without breaking RPH/Word or login."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records

ROOT=Path(__file__).resolve().parents[1]


class ViewStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack=[]
        self.parent={}
        self.ids={}
        self.view_controls={}
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if tag in {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}:
            return
        parent=next((name for name in reversed(self.stack) if name in {"view-rph","view-rpt","view-account","view-guide","workspace"}),None)
        name=data.get("id") or tag
        if "id" in data:
            self.ids[name]=self.ids.get(name,0)+1
            self.parent[name]=parent
        if "data-web-view" in data:
            self.view_controls[data["data-web-view"]]=data
        self.stack.append(name)
    def handle_endtag(self,tag):
        if not self.stack:
            return
        if self.stack[-1]==tag or self.stack[-1] in self.ids:
            self.stack.pop()
        else:
            self.stack.pop()


class WebSidebarTabsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/"web_v1_static_preview"/"index.html").read_text(encoding="utf-8")

    def test_four_actual_menu_tabs_and_single_logout(self):
        import re
        self.assertEqual(len(re.findall(r'\bid="logout"', self.html)),1)
        for name,view in (("rph","view-rph"),("rpt","view-rpt"),("account","view-account"),("guide","view-guide")):
            self.assertIn('data-web-view="'+name+'"',self.html)
            self.assertIn('aria-controls="'+view+'"',self.html)
            self.assertIn('id="'+view+'"',self.html)
        self.assertIn('class="app-sidebar"',self.html)
        self.assertIn('class="sidebar-menu"',self.html)

    def test_guide_is_home_in_desktop_and_mobile_navigation(self):
        import re
        menu=re.search(r'<nav class="sidebar-menu"[^>]*>(.*?)</nav>',
                       self.html,flags=re.S)
        self.assertIsNotNone(menu)
        choices=re.findall(r'data-web-view="([^"]+)"',menu.group(1))
        self.assertEqual(choices[:6],["guide","account","today","rph","rpt","payment"])
        self.assertEqual(len(choices),len(set(choices)))
        self.assertIn('data-web-view="account" aria-controls="view-account"',menu.group(1))
        self.assertIn('data-web-view="guide" aria-controls="view-guide" aria-current="page"',menu.group(1))
        self.assertEqual(menu.group(1).count('aria-current="page"'),1)
        self.assertIn('showWebView("guide");',self.html)
        self.assertIn('data-guide-view="today" aria-controls="view-today"',self.html)
        # Same markup is reused for mobile, no separate ordering is necessary.
        self.assertIn('.sidebar-menu{display:grid;grid-template-columns:',self.html)

    def test_curriculum_documents_separate_menu_and_source_filters(self):
        import re
        menu=re.search(r'<nav class="sidebar-menu"[^>]*>(.*?)</nav>',self.html,flags=re.S)
        choices=re.findall(r'data-web-view="([^"]+)"',menu.group(1))
        self.assertEqual(choices[:7],["guide","account","today","rph","rpt","payment","curriculum-docs"])
        self.assertIn('["curriculum-docs","view-curriculum-docs"]',self.html)
        self.assertIn('id="view-curriculum-docs" class="app-view" aria-labelledby="curriculum-docs-heading" hidden',self.html)
        for category in ("kp2027","kssr","dpk","pk"):
            self.assertIn('id="curriculum-docs-'+category+'" hidden',self.html)
        rows=re.findall(r'<li data-doc-year="([1-6])" data-doc-subject="([^"]+)"><a href="(https://(?:drive\.google\.com/file/d/[A-Za-z0-9_-]+/view(?:\?usp=sharing)?|asiemodel\.net/wp-content/uploads/2022/08/[^"]+\.pdf))"',self.html)
        self.assertEqual(len(rows),87)
        self.assertEqual(len({url for _,_,url in rows}),87)
        expected={(str(year),subject+" "+stream) for year in range(1,7)
                  for subject in ("Matematik","Sains")
                  for stream in ("SK","SJKC","SJKT","DLP")}
        for subject,years in {
            "Bahasa Melayu SK": range(1,7), "Bahasa Arab": range(1,7),
            "Bahasa Cina SK": range(1,7), "Bahasa Cina SJKC": range(1,7),
            "Bahasa Tamil SK": range(1,7), "Bahasa Tamil SJKT": (2,3,4,5,6),
            "Bahasa Iban": (3,4,5,6),
        }.items():
            expected.update((str(year),subject) for year in years)
        self.assertEqual({(year,subject) for year,subject,_ in rows},expected)
        pk_rows=re.findall(r'<li data-pk-year="([1-6])" data-pk-subject="([^"]+)"><a href="(https://[^"]+\.pdf)"',self.html)
        kp_section=self.html.split('<ul id="curriculum-kp2027-list">',1)[1].split("</ul>",1)[0]
        self.assertEqual(kp_section.count("<li>"),5)
        self.assertEqual(kp_section.count("PDF sumber luar"),3)
        self.assertEqual(kp_section.count("halaman sumber"),2)
        self.assertIn('https://bpk.moe.gov.my/kurikulum/kp2027',self.html)
        for name in ("Bahasa Melayu SK","Bahasa Melayu SJK","Matematik","Alam dan Manusia: Pembelajaran Bersepadu","Pendidikan Jasmani"):
            self.assertIn("DK "+name+" Tahun 1",kp_section)
        self.assertIn("Sumber penataran — edisi akhir belum disahkan",self.html)
        self.assertEqual(len(pk_rows),9)
        self.assertEqual(len({url for _,_,url in pk_rows}),9)
        self.assertEqual({(year,subject) for year,subject,_ in pk_rows},{
            ("1","Asas 3M"),("2","Pengurusan Kehidupan"),("3","Asas 3M"),
            ("3","Pengurusan Kehidupan"),("3","Pendidikan Seni Kreatif"),
            ("5","Pengurusan Kehidupan"),("5","Kemahiran Hidup Asas"),
            ("5","Pendidikan Sains, Sosial dan Alam Sekitar"),
            ("6","Pendidikan Sains, Sosial dan Alam Sekitar"),
        })
        self.assertIn('docsYear.addEventListener("change",filterCurriculumDocs)',self.html)
        self.assertIn('docsSubject.addEventListener("change",filterCurriculumDocs)',self.html)
        self.assertIn('#workspace #view-curriculum-docs{display:none!important}',self.html)

    def test_rpt_catalog_outside_rph_section(self):
        # Structural check using parsed nesting, not only search positions.
        class NodeParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack=[]
                self.closest={}
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if a.get("id"):
                    self.closest[a["id"]]=[x for x,y in self.stack if x]
                if tag not in {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}:
                    self.stack.append((a.get("id"),tag))
            def handle_endtag(self,tag):
                for i in range(len(self.stack)-1,-1,-1):
                    if self.stack[i][1]==tag:
                        del self.stack[i:]
                        break
        parsed=NodeParser()
        parsed.feed(self.html)
        self.assertIn("view-rpt",parsed.closest["rpt2027-panel"])
        self.assertNotIn("view-rph",parsed.closest["rpt2027-panel"])
        for name in ["year","subject","unit","lesson","rph-word","rph-pdf"]:
            self.assertIn("view-rph",parsed.closest[name],name)
            self.assertNotIn("view-rpt",parsed.closest[name],name)
        self.assertIn("view-account",parsed.closest["profile-access-summary"])
        self.assertIn("app-shell",self.html)

    def test_access_control_and_navigation_remain_independent(self):
        self.assertIn('data-web-view="rpt"',self.html)
        self.assertIn('function showWebView(name)',self.html)
        self.assertIn('button.classList.toggle("is-active",active)',self.html)
        self.assertIn('document.getElementById(id).hidden=key!==name;',self.html)
        self.assertIn('showWebView("rph");',self.html)
        self.assertIn('document.getElementById("profile-access-summary").textContent=',self.html)
        self.assertIn('fetch("/api/auth/telegram/session"',self.html)
        self.assertIn('fetch("/api/rpt/2027/catalog"',self.html)
        self.assertNotIn('id="rph-preview-panel"',self.html)
        self.assertIn('"/api/web/rph/word?"',self.html)
        self.assertIn('"/api/web/rph/pdf?"',self.html)
        self.assertNotIn('window.print()',self.html)

    def test_mobile_and_print_sidebar_not_in_document(self):
        self.assertIn('@media(max-width:760px)',self.html)
        self.assertIn('.sidebar-more{grid-column:1/-1}',self.html)
        self.assertIn('#workspace .app-sidebar,#workspace #view-rpt',self.html)
        self.assertIn('id="rph-download-actions"',self.html)
        self.assertIn('id="rph-word"',self.html)
        self.assertIn('id="rph-pdf"',self.html)

    @patch("web.unified_rph_web._account",return_value=(None,({"error":"Login required"},401)))
    def test_word_and_preview_unauthenticated_denied(self,*_):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        client=app.test_client()
        row=source_records(4,"ENGLISH")[0]
        args={"year":4,"subject":"ENGLISH","unit":row["unit"],"lesson":row["token"]}
        self.assertEqual(client.get("/api/web/rph/preview",query_string=args).status_code,401)
        self.assertEqual(client.get("/api/web/rph/word",query_string=args).status_code,401)


if __name__=="__main__":
    unittest.main()
