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
        self.assertIn('.sidebar-menu{display:flex;flex-direction:row;',self.html)
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
