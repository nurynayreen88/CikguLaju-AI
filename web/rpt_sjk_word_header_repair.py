"""Non-destructive BM SJK Word header repair for the four audited originals."""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
from lxml import etree

PINS={
3:"43db5847d1a952c3c49dc88be436125b1dab446d6ea156aec5c3dae12f8976d7",
4:"eb19caf57d22da89fbda39c774127a19751fe90490d646a887c525f8032a34fc",
5:"10e4628873114c55189a44074fe9d0e009cddb179a19d0486679eda2564ad307",
6:"37b7d7144a962994f0817f5f9c97b09cbd0dd686461d77c0dbf9e426497f6f7d"}
NS={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W="{"+NS["w"]+"}"
MAIN=("PdP","Unit dan tajuk","SK dan SP","Rujukan","Fokus PdP")
VALUE=("PdP","Tajuk","SP Bahasa Melayu","Nilai teras","Cadangan aktiviti")
COUNTS={
3:{MAIN:16,("PdP","Tajuk","Hasil pembelajaran","Buku Aktiviti Murid","Aktiviti"):2,VALUE:1},
**{year:{MAIN:16,("PdP","Tajuk BAM","Aktiviti dan tempoh","Rujukan dan HP","Padanan aktiviti Bahasa Melayu"):3,VALUE:1,("PdP","Tajuk alternatif","SK dan SP","Rujukan","Fokus PdP"):1} for year in (4,5,6)}
}
def repair(year,raw):
    if sha256(raw).hexdigest()!=PINS.get(year):
        raise ValueError("BM SJK source fingerprint changed")
    from collections import Counter
    counts=Counter()
    out=BytesIO()
    with ZipFile(BytesIO(raw)) as src, ZipFile(out,"w") as dst:
        for item in src.infolist():
            data=src.read(item)
            if item.filename=="word/document.xml":
                root=etree.fromstring(data)
                for table in root.xpath("./w:body/w:tbl",namespaces=NS):
                    row=table.find(W+"tr")
                    if row is None:continue
                    sig=tuple("".join(c.xpath(".//w:t/text()",namespaces=NS)).strip() for c in row.findall(W+"tc"))
                    if sig not in COUNTS[year]:continue
                    counts[sig]+=1
                    props=row.find(W+"trPr")
                    if props is None:
                        props=etree.Element(W+"trPr");row.insert(0,props)
                    if props.find(W+"tblHeader") is not None:raise ValueError("Unexpected existing header")
                    etree.SubElement(props,W+"tblHeader")
                if counts!=COUNTS[year]:raise ValueError(f"BM SJK header inventory changed: {counts}")
                data=etree.tostring(root,encoding="UTF-8",xml_declaration=True,standalone=True)
            dst.writestr(item,data)
    return out.getvalue()
