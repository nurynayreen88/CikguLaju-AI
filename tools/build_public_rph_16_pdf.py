"""Build the public, owner-reviewed 16-page RPH sample PDF.

Run in GitHub Actions only; no teacher identity, quota, API or curriculum DB.
The earlier 12-example PDF is not overwritten.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web_v1_static_preview" / "Contoh_RPH_Semua_16.html"
OUTPUT = ROOT / "web_v1_static_preview" / "CikguLaju_Contoh_RPH_Semua_16.pdf"


def main() -> None:
    from weasyprint import HTML as HTMLRenderer
    import fitz

    markup = HTML.read_text(encoding="utf-8")
    assert len(re.findall(r'<section id="rph-contoh-\d+" class="page ', markup)) == 16
    assert 'class="page rtl"' in markup
    assert "Kembali ke log masuk" in markup
    assert "Cetak / Simpan PDF" in markup
    output = HTMLRenderer(filename=str(HTML), base_url=str(HTML.parent)).write_pdf()
    OUTPUT.write_bytes(output)

    with fitz.open(stream=output, filetype="pdf") as pdf:
        assert len(pdf) == 16, f"Unexpected pages {len(pdf)}"
        for index, page in enumerate(pdf, start=1):
            assert abs(page.rect.width - 595.28) < 2, (index, page.rect)
            assert abs(page.rect.height - 841.89) < 2, (index, page.rect)
            words = page.get_text("words")
            assert len(words) > 45, (index, len(words))
            for word in words:
                x0, y0, x1, y1 = word[:4]
                assert -2 <= x0 <= x1 <= page.rect.width + 2, (index, word)
                assert -2 <= y0 <= y1 <= page.rect.height + 2, (index, word)
            for draw in page.get_drawings():
                bounds = draw.get("rect")
                if bounds is not None and bounds.width > 2 and bounds.height > 2:
                    assert bounds.x0 >= -2 and bounds.y0 >= -2, (index, bounds)
                    assert bounds.x1 <= page.rect.width + 2, (index, bounds)
                    assert bounds.y1 <= page.rect.height + 2, (index, bounds)
        print("PUBLIC_16_RPH_PDF_PASS", len(pdf), "A4 pages", len(output), "bytes", flush=True)


if __name__ == "__main__":
    main()
