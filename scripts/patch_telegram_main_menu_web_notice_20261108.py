"""Insert one visible, non-disruptive Web notice into the FINAL active Telegram menu().

The legacy app contains many versioned menu() overrides. We modify only the
last AST function definition. No callback routing, billing, credit or DB logic.
"""
from __future__ import annotations
import ast
from pathlib import Path

WEB_URL="https://cikgulaju-web.onrender.com/"
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app.py"

def patch_app(path=APP):
    path=Path(path)
    source=path.read_text(encoding="utf-8")
    assert "🌐 BUKA CIKGULAJU WEB" not in source, "Already applied"
    parsed=ast.parse(source)
    menus=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name=="menu"]
    assert len(menus)>=2,"Expected versioned menu overrides"
    active=menus[-1]
    block=source.splitlines(keepends=True)
    start=active.lineno-1;end=active.end_lineno
    original="".join(block[start:end])
    marker="        [{'text':'📅 RPT 2027','callback_data':'rpt2027_home'}],"
    assert original.count(marker)==1,"Final menu RPT button changed; stop"
    replacement=marker+"\n        [{'text':'🌐 BUKA CIKGULAJU WEB','url':"+repr(WEB_URL)+"}],"
    updated=original.replace(marker,replacement,1)
    copy_marker="        '👤 <b>PROFIL SAYA</b>"
    assert updated.count(copy_marker)==1,"Final menu profile text changed; stop"
    notice=(
        "        '🌐 <b>CIKGULAJU WEB SUDAH TERSEDIA</b>\\n'"
        "\n        'Sediakan RPH dan muat turun RPT 2027 melalui telefon atau komputer.\\n'"
        "\n        '🔗 https://cikgulaju-web.onrender.com/\\n'"
        "\n        'Log masuk menggunakan Telegram. Baki janaan RPH dikongsi antara Web dan bot; RPT memerlukan akses berbayar.\\n\\n'\n"
    )
    updated=updated.replace(copy_marker,notice+copy_marker,1)
    block[start:end]=[updated]
    result="".join(block)
    assert result!=source and len(result)>len(source)
    ast.parse(result)
    # Ensure no other menu or callback function is changed.
    parsed_new=ast.parse(result)
    new_menus=[n for n in parsed_new.body if isinstance(n,ast.FunctionDef) and n.name=="menu"]
    assert len(new_menus)==len(menus)
    assert all(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
               for a,b in zip(menus[:-1],new_menus[:-1]))
    assert source.count("def callback(")==result.count("def callback(")
    assert source.count("def menu(")==result.count("def menu(")
    path.write_text(result,encoding="utf-8")
    print("Final active menu patched; 1 Web link, 1 announcement; no other callbacks/menus touched.")

if __name__=="__main__":
    patch_app()
