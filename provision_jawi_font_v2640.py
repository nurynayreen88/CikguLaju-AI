from pathlib import Path
from urllib.request import urlretrieve
from fontTools.ttLib import TTFont

BASE=Path(__file__).resolve().parent
DEST=BASE/"assets"/"fonts"
DEST.mkdir(parents=True,exist_ok=True)

FILES={
"NotoNaskhArabic-Regular.ttf":
"https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Regular.ttf",
"NotoNaskhArabic-Bold.ttf":
"https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoNaskhArabic/hinted/ttf/NotoNaskhArabic-Bold.ttf",
}
sample="ابتجدرڤچڠکݢڽ"
req={ord(c) for c in sample}
for name,url in FILES.items():
    p=DEST/name
    if not p.exists() or p.stat().st_size<10000:
        urlretrieve(url,p)
    cmap=set()
    f=TTFont(str(p),lazy=True)
    for t in f["cmap"].tables: cmap.update(t.cmap.keys())
    missing=req-cmap
    if missing:
        raise SystemExit(f"{name}: missing "+",".join(f"U+{x:04X}" for x in sorted(missing)))
    print("READY",p)
