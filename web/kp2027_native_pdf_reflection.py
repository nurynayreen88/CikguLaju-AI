"""Rebuild KP2027 PDF reflection using the PDF's original embedded Noto Serif.

The original PDFs contain subsets of Noto Serif and PDF-specific 1-byte
character encodings. Generic PyMuPDF insert_textbox silently substitutes a
different face, creating the Times-Roman 8-pt mismatch reported by teachers.
This renderer retains the exact original /Font resources and 9-pt metrics,
removes old text before writing, and never changes SK/SP or activity rows.
"""
from __future__ import annotations
import re


def native_reflection_plan(document, page, candidates, row_top, row_bottom):
    fonts = page.get_fonts()
    regular = next((f for f in fonts if "NotoSerif-Regular" in f[3]), None)
    bold = next((f for f in fonts if "NotoSerif-Bold" in f[3]), None)
    if not regular or not bold:
        return None  # Other/older PDF templates use the verified fallback.

    def font_info(item):
        key = document.xref_get_key(item[0], "ToUnicode")
        if key[0] != "xref":
            raise ValueError("Peta aksara fon PDF asal tidak disahkan.")
        cmap = document.xref_stream(int(key[1].split()[0])).decode("latin-1")
        entries = re.findall(r"<([0-9A-Fa-f]{2})>\s*<([0-9A-Fa-f]{4})>", cmap)
        enc = {chr(int(ch, 16)): int(code, 16) for code, ch in entries}
        match = re.search(r"/Widths\s*\[([^]]+)\]", document.xref_object(item[0]), re.S)
        if not match or not enc:
            raise ValueError("Ukuran fon PDF asal tidak dapat disahkan.")
        widths = [int(v) for v in re.findall(r"\d+", match[1])]
        if not widths or any(i >= len(widths) for i in enc.values()):
            raise ValueError("Peta fon RPH tidak lengkap.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", item[4]):
            raise ValueError("Nama fon RPH tidak sah.")
        return enc, widths, item[4]

    normal_font, label_font = font_info(regular), font_info(bold)
    if set("Refleksi") - set(label_font[0]):
        raise ValueError("Fon asal tidak mengandungi label refleksi.")

    left = 155.6
    max_width = page.rect.width - 47.0 - left
    blank = " " * 8

    def text_width(value):
        mapping, widths, _ = normal_font
        return sum(widths[mapping[ch]] for ch in value) * 9.0 / 1000.0

    def wrap(value):
        lines = []
        for para in value.splitlines():
            line = ""
            for word in para.split():
                token = blank if word == "____" else word
                if set(token) - set(normal_font[0]) or text_width(token) > max_width:
                    return None
                trial = line + " " + token if line else token
                if text_width(trial) > max_width:
                    if line:
                        lines.append(line)
                    line = token
                else:
                    line = trial
            if line:
                lines.append(line)
        return lines

    height = row_bottom - row_top
    selected = None
    for sentence in candidates:
        lines = wrap(sentence)
        if not lines:
            continue
        needed = 12.3 + (len(lines) - 1) * 10.7
        if needed + 1.5 <= height:
            selected = lines
            break
    if selected is None:
        raise ValueError("Refleksi tidak muat pada fon asal 9 pt. Ringkaskan refleksi atau guna Word.")

    def text_op(font, x, baseline, value):
        mapping, _, resource = font
        raw = bytes(mapping[ch] for ch in value).hex().upper()
        return (f"BT\n/{resource} 9 Tf\n0 g\n"
                f"1 0 0 1 {x:.2f} {page.rect.height - baseline:.2f} Tm\n"
                f"<{raw}> Tj\nET\n").encode("ascii")

    result = bytearray(b"q\n")
    result.extend(text_op(label_font, 38.0, (row_top + row_bottom) / 2 + 4.7, "Refleksi"))
    full_height = 12.3 + (len(selected) - 1) * 10.7
    baseline = row_top + (height - full_height) / 2 + 9.7
    for i, line in enumerate(selected):
        y = baseline + i * 10.7
        result.extend(text_op(normal_font, left, y, line))
        offset = 0
        while True:
            pos = line.find(blank, offset)
            if pos < 0:
                break
            start = left + text_width(line[:pos])
            end = start + text_width(blank) - 2
            # Draw a blank for teacher-entered mastery counts. Never infer one.
            result.extend((f"0.55 w\n{start:.2f} {page.rect.height - y - 1.2:.2f} m\n"
                           f"{end:.2f} {page.rect.height - y - 1.2:.2f} l\nS\n").encode("ascii"))
            offset = pos + len(blank)
    result.extend(b"Q\n")
    return bytes(result)


def append_native_reflection(document, page, native_stream):
    """Append original-font text after real redaction of both cell contents."""
    old = page.get_contents()
    if not old:
        raise ValueError("Lapisan teks RPH asal tidak dapat disahkan.")
    new = document.get_new_xref()
    document.update_object(new, "<<>>")
    document.update_stream(new, native_stream)
    document.xref_set_key(page.xref, "Contents",
                          "[ " + " ".join(f"{n} 0 R" for n in [*old, new]) + " ]")
