"""Presentation-only PI Word identity. Preserve all lesson and teacher text."""
from collections import Counter
from io import BytesIO
from zipfile import ZipFile
from lxml import etree
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC="word/document.xml"
LABELS=("مات ڤلاجرن","تاهون / تيڠکتن")
def text(node):
    return "".join(n.text or "" for n in node.iter(W+"t"))
def compact_pi_identity(data):
    with ZipFile(BytesIO(data)) as z:
        root=etree.fromstring(z.read(DOC))
        body=root.find(W+"body")
        tables=body.findall(W+"tbl")
        if len(tables)!=4 or not any(text(p).strip()=="رنچڠن ڤڠاجرن هارين" for p in body.findall(W+"p")):
            return data
        table=tables[0]
        if table.find(W+"tblPr/"+W+"bidiVisual") is None:
            return data
        rows=table.findall(W+"tr")
        if len(rows)!=1:return data
        cells=rows[0].findall(W+"tc")
        if len(cells)!=2:return data
        lines=cells[0].findall(W+"p")
        if len(lines)!=3 or "کلس" not in text(cells[1]):return data
        if not text(lines[0]).startswith(LABELS[0]+"ڤنديديقن اسلام"):return data
        if not text(lines[1]).startswith(LABELS[1]+"تاهون "):return data
        removed=[]
        before=Counter(n.text or "" for n in root.iter(W+"t"))
        for i,label in enumerate(LABELS):
            p=lines[i]
            runs=p.findall(W+"r")
            split=next((j for j,r in enumerate(runs) if r.find(W+"tab") is not None),None)
            if split is None or "".join(text(r) for r in runs[:split])!=label:return data
            for r in runs[:split+1]:
                removed.extend(n.text or "" for n in r.iter(W+"t"))
                p.remove(r)
            for r in p.findall(W+"r"):
                pr=r.find(W+"rPr")
                if pr is None:
                    pr=etree.Element(W+"rPr");r.insert(0,pr)
                for tag in ("b","bCs"):
                    e=pr.find(W+tag)
                    if e is None:e=etree.SubElement(pr,W+tag)
                    e.set(W+"val","1" if i==0 else "0")
        # Only the two known labels were removed at this stage.
        after=Counter(n.text or "" for n in root.iter(W+"t"))
        assert before-after==Counter(removed) and not after-before
        # Centre the complete three-line identity vertically within the
        # existing right-hand panel. Preserve right-to-left alignment.
        props=cells[0].find(W+"tcPr")
        align=props.find(W+"vAlign")
        if align is None:align=etree.SubElement(props,W+"vAlign")
        align.set(W+"val","center")
        # Remove just the matched character span in the topic value runs.
        from web.rph_pi_topic_display_20261124 import duration_span
        topic=lines[2]
        nodes=list(topic.iter(W+"t"))
        full="".join(n.text or "" for n in nodes)
        span=duration_span(full)
        if span is not None:
            start,end=span
            offset=0
            for n in nodes:
                value=n.text or ""
                a=max(0,start-offset)
                b=min(len(value),end-offset)
                if a<b:n.text=value[:a]+value[b:]
                offset+=len(value)
            assert text(topic)==full[:start]+full[end:]
        out=BytesIO()
        with ZipFile(out,"w") as dest:
            for item in z.infolist():
                dest.writestr(item,etree.tostring(root,encoding="UTF-8",xml_declaration=True,standalone=True) if item.filename==DOC else z.read(item.filename))
        return out.getvalue()
