"""Read printed timetable grids into editable teaching slots using local OCR."""
import re
from collections import defaultdict
from functools import lru_cache
from io import BytesIO

from web.timetable_upload import DAYS, UnreadableTimetable, upload_mime

DAY_LABELS = {
    name.casefold(): day
    for day, names in zip(DAYS, (
        ("Isnin", "Isn", "Monday", "Mon"),
        ("Selasa", "Sel", "Tuesday", "Tue"),
        ("Rabu", "Rab", "Wednesday", "Wed"),
        ("Khamis", "Kha", "Khm", "Thursday", "Thu"),
        ("Jumaat", "Jum", "Jumat", "Friday", "Fri"),
        ("Sabtu", "Sab", "Saturday", "Sat"),
        ("Ahad", "Ahd", "Sunday", "Sun"),
    ))
    for name in names
}
SHORT_DAYS = dict(zip("isrkj", DAYS))
SUBJECTS = {
    "BM": "Bahasa Melayu", "BI": "English", "BA": "Bahasa Arab",
    "EN": "English", "ENG": "English", "Bahasa Inggeris": "English",
    "MT": "Matematik", "MM": "Matematik", "Mathematics": "Matematik",
    "MATH": "Matematik", "SN": "Sains", "SC": "Sains", "Science": "Sains",
    "PI": "Pendidikan Islam", "PAI": "Pendidikan Islam",
    "PM": "Pendidikan Moral", "PSV": "Pendidikan Seni Visual",
    "MZ": "Pendidikan Muzik", "MUZIK": "Pendidikan Muzik",
    "PJ": "Pendidikan Jasmani", "PK": "Pendidikan Kesihatan",
    "PJPK": "PJPK", "RBT": "Reka Bentuk dan Teknologi",
    "SJ": "Sejarah", "SEJ": "Sejarah", "Sejarah": "Sejarah",
    "Sains DLP": "Sains DLP", "Science DLP": "Sains DLP",
    "Matematik DLP": "Matematik DLP", "Mathematics DLP": "Matematik DLP",
}
SUBJECTS = {key.casefold(): value for key, value in {
    **{name: name for name in SUBJECTS.values()}, **SUBJECTS
}.items()}
SUBJECT_PATTERN = re.compile(
    r"(?<!\w)(?:" + "|".join(map(re.escape, sorted(SUBJECTS, key=len, reverse=True)))
    + r")(?!\w)", re.I,
)
TIME_PATTERN = re.compile(r"(?<!\d)([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)(?!\d)"
                          r"\s*(a\.?m\.?|p\.?m\.?|pagi|petang|tengah\s+hari)?", re.I)
CLASS_PATTERN = re.compile(r"(?:Tahun\s*)?[1-6]\s*[A-Za-z][\w .'-]{0,34}", re.I)
TIME_OCR = re.compile(r"(?<!\w)[0-9Il]{1,2}[:.][0-9Oo]{2}(?!\w)")
TIME_OCR_DIGITS = str.maketrans("IlOo", "1100")
COMPACT_CLASS = re.compile(r"([1-6Il])\s*([A-Za-z])", re.I)
SUBJECT_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}")
NON_TEACHING = re.compile(
    r"^(?:masa rehat|rehat|recess|perhimpunan|assembly|kokurikulum|free period)\b", re.I)


MAX_PAGES = 3
MAX_PIXELS = 18_000_000


def _pages(data):
    from PIL import Image, ImageOps
    mime = upload_mime(data)
    if mime == "application/pdf":
        import fitz
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass or not 0 < len(doc) <= MAX_PAGES:
                raise UnreadableTimetable("Gunakan PDF tanpa kata laluan, maksimum 3 halaman.")
            for page in doc:
                zoom = min(4, 2200 / max(page.rect.width, page.rect.height))
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                transform = page.rotation_matrix * matrix
                words = []
                for x0, y0, x1, y1, word, *_ in page.get_text("words"):
                    box = fitz.Rect(x0, y0, x1, y1) * transform
                    words.append((box.x0, box.y0, box.x1, box.y1, word))
                yield Image.frombytes("RGB", (pix.width, pix.height), pix.samples), words
        return
    with Image.open(BytesIO(data)) as source:
        if source.width * source.height > MAX_PIXELS or getattr(source, "n_frames", 1) != 1:
            raise UnreadableTimetable("Gunakan satu gambar jadual yang lebih kecil.")
        img = ImageOps.exif_transpose(source)
        img.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        yield img.convert("RGB"), []


@lru_cache(maxsize=1)
def _ocr_engine():
    from ocrust import Ocr
    return Ocr(threads=2, tables=False, word_boxes=True, preprocess=False,
               fix_orientation=False, drop_score=0.48, max_pixels=MAX_PIXELS)


def _ocr_words(image):
    doc = _ocr_engine().scan(image)
    return [
        (word.box.x0, word.box.y0, word.box.x1, word.box.y1, word.text)
        for page in doc.pages for block in page.blocks for line in block.lines
        for word in line.words
    ]


def _grid(image):
    # Extract ruled cell boundaries first, retaining wide merged teaching cells.
    import cv2
    import numpy as np

    gray = np.asarray(image.convert("L"))
    height, width = gray.shape
    ink = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 31, 13)
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                                  cv2.getStructuringElement(cv2.MORPH_RECT, (max(18, width // 38), 1)))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                                cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(14, height // 38))))
    ruled = cv2.bitwise_or(horizontal, vertical)
    ruled = cv2.morphologyEx(ruled, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8))
    _, _, stats, _ = cv2.connectedComponentsWithStats(255 - ruled, connectivity=4)
    cells = []
    for x, y, w, h, area in stats[1:]:
        if (0 < x < x + w < width and 0 < y < y + h < height
                and w >= 24 and h >= 17 and 0.8 * w * h <= area < 0.65 * width * height):
            cells.append((int(x), int(y), int(x + w), int(y + h)))
    return sorted(cells, key=lambda cell: (cell[1], cell[0]))[:400]


def _text(words):
    # Keep words on the same printed line in left-to-right order.
    lines = []
    for word in sorted(words, key=lambda item: (item[1] + item[3]) / 2):
        center = (word[1] + word[3]) / 2
        if not lines or abs(lines[-1][0] - center) > max(3, (word[3] - word[1]) * 0.48):
            lines.append((center, []))
        lines[-1][1].append(word)
    return " ".join(word[4] for _, line in lines for word in sorted(line))


def _cell_texts(cells, words):
    grouped = defaultdict(list)
    for word in words:
        x0, y0, x1, y1, _ = word
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        for index, (left, top, right, bottom) in enumerate(cells):
            if left <= x <= right and top <= y <= bottom:
                grouped[index].append(word)
                break
    return [(cells[index], _text(items)) for index, items in grouped.items()]


def _times(text):
    text = TIME_OCR.sub(lambda match: match[0].translate(TIME_OCR_DIGITS), text)
    values = []
    for hh, mm, label in TIME_PATTERN.findall(text):
        hour = int(hh)
        label = label.casefold().replace(".", "").strip()
        if label in ("pm", "petang", "tengah hari") and hour < 12:
            hour += 12
        elif label in ("am", "pagi") and hour == 12:
            hour = 0
        values.append(f"{hour:02d}:{mm}")
    return values


def _interval(cell, axis):
    return cell[axis], cell[axis + 2]


def _intersects(first, second):
    overlap = min(first[1], second[1]) - max(first[0], second[0])
    return overlap > min(first[1] - first[0], second[1] - second[0]) * 0.45


def _day_labels(texts):
    labels = [(cell, DAY_LABELS[text.casefold().strip(" .:")]) for cell, text in texts
              if text.casefold().strip(" .:") in DAY_LABELS]
    if len({day for _, day in labels}) >= 2:
        x = [(cell[0] + cell[2]) / 2 for cell, _ in labels]
        y = [(cell[1] + cell[3]) / 2 for cell, _ in labels]
        return labels, int(max(y) - min(y) > max(x) - min(x)), False

    # Interpret single letters only in a coherent day band, where a lone
    # letter in the teaching grid (including vertical REHAT) cannot be a day.
    short = [(cell, SHORT_DAYS[text.casefold().strip(" .:")]) for cell, text in texts
             if text.casefold().strip(" .:") in SHORT_DAYS]
    candidates = []
    for axis in (0, 1):
        for anchor, _ in short:
            lane = [(cell, day) for cell, day in short
                    if _intersects(_interval(cell, 1 - axis), _interval(anchor, 1 - axis))]
            lane.sort(key=lambda pair: pair[0][axis])
            days = [DAYS.index(day) for _, day in lane]
            if len(days) >= 3 and days == sorted(set(days)):
                candidates.append((lane, axis))
    if candidates:
        lane, axis = max(candidates, key=lambda candidate: len(candidate[0]))
        return lane, axis, True
    return [], 1, False


def _headers(texts, labels, time_axis, day_axis):
    # Choose the time-header band with the most readable periods.
    bands = []
    for cell, text in texts:
        times = _times(text)
        if not 1 <= len(times) <= 2:
            continue
        band = _interval(cell, day_axis)
        if any(_intersects(band, _interval(day_cell, day_axis)) for day_cell, _ in labels):
            continue
        entry = (_interval(cell, time_axis), times)
        for anchor, entries in bands:
            if _intersects(band, anchor):
                entries.append(entry)
                break
        else:
            bands.append((band, [entry]))
    if not bands:
        return []
    _, header = max(bands, key=lambda band: len(band[1]))
    header.sort()
    output = []
    for index, (span, times) in enumerate(header):
        start = times[0]
        end = times[1] if len(times) == 2 else (
            header[index + 1][1][0] if index + 1 < len(header) else "")
        if "12:00" <= start < "13:00" and "01:00" <= end < "07:00":
            end = f"{int(end[:2]) + 12:02d}{end[2:]}"
        if output and output[-1][2] >= "13:00" and "01:00" <= start < end < "07:00":
            afternoon = f"{int(start[:2]) + 12:02d}{start[2:]}"
            if output[-1][2] == afternoon:
                start = afternoon
                end = f"{int(end[:2]) + 12:02d}{end[2:]}"
        if start < end:
            output.append((span, start, end))
    return output


def _class_key(value):
    return re.sub(r"[\W_]+", "", re.sub(r"^tahun\s*", "", value.casefold()))


def _subject_class(text, saved_classes, compact=False):
    match = SUBJECT_PATTERN.search(text)
    if match:
        subject = SUBJECTS[match[0].casefold()]
        name = (text[:match.start()] + " " + text[match.end():]).strip(" -/|:–—")
    else:
        code, _, name = text.partition(" ")
        # Preserve printed local codes until the teacher selects a subject.
        subject = code if compact and SUBJECT_CODE.fullmatch(code) and COMPACT_CLASS.fullmatch(name) else ""
    if not subject:
        # Keep a readable custom subject if the class already exists in the profile.
        for name in sorted(saved_classes, key=len, reverse=True):
            found = re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.I)
            if found:
                custom = (text[:found.start()] + " " + text[found.end():]).strip(" -/|:–—")
                custom = " ".join(custom.split())
                if len(custom) <= 60 and re.fullmatch(r"[\w .\-/()&,]+", custom):
                    return custom, name
                return "", name
        return "", ""
    name = " ".join(name.split())
    if compact and (short_class := COMPACT_CLASS.fullmatch(name)):
        year, suffix = short_class.groups()
        name = ("1" if not year.isdigit() else year) + suffix.upper()
    matching = [saved for saved in saved_classes if _class_key(saved) == _class_key(name)]
    if len(matching) == 1:
        return subject, matching[0]
    return subject, name if len(name) <= 40 and CLASS_PATTERN.fullmatch(name) else ""


def _break_cells(texts, labels, day_axis):
    label_cells = {cell for cell, _ in labels}
    letters = [(cell, text.upper()) for cell, text in texts
               if len(text) == 1 and text.upper() in "REHAT" and cell not in label_cells]
    for anchor, _ in letters:
        lane = [(cell, letter) for cell, letter in letters
                if _intersects(_interval(cell, 1 - day_axis), _interval(anchor, 1 - day_axis))]
        lane.sort(key=lambda pair: pair[0][day_axis])
        if "".join(letter for _, letter in lane) == "REHAT":
            return {cell for cell, _ in lane}
    return set()


def _teaching_cells(cells, labels, headers, day_axis):
    return [cell for cell in cells
            if not any(_intersects(_interval(cell, 1 - day_axis), _interval(label, 1 - day_axis))
                       for label, _ in labels)
            and any(_intersects(_interval(cell, day_axis), _interval(label, day_axis))
                    for label, _ in labels)
            and any(_intersects(_interval(cell, 1 - day_axis), span) for span, _, _ in headers)]


def _cell_lines(gray, cell):
    import cv2
    import numpy as np

    x0, y0, x1, y1 = cell
    margin = max(3, min(8, min(x1 - x0, y1 - y0) // 12))
    tile = gray[y0 + margin:y1 - margin, x0 + margin:x1 - margin]
    tile = cv2.GaussianBlur(tile, (3, 3), 0)
    background = np.bincount(tile.ravel(), minlength=256).argmax()
    if background < 50:
        return []
    ink = (tile < 0.70 * background).astype("uint8")
    _, labels, stats, _ = cv2.connectedComponentsWithStats(ink)
    clean = np.zeros_like(ink)
    for index, (_, _, width, height, area) in enumerate(stats[1:], start=1):
        if width >= 2 and 3 <= height < 0.7 * len(tile) and area >= 10:
            clean[labels == index] = 1
    boundaries = np.flatnonzero(np.diff(np.r_[False, clean.sum(axis=1) > 1, False]))
    lines = []
    for top, bottom in zip(boundaries[::2], boundaries[1::2]):
        if bottom - top >= 7:
            _, columns = np.nonzero(clean[top:bottom])
            line = tile[top:bottom, columns.min():columns.max() + 1]
            lines.append(cv2.normalize(line, None, 0, 255, cv2.NORM_MINMAX))
    return lines


def _ocr_cell_lines(image, cells):
    """Read subject and class lines separately after removing borders and color."""
    import cv2
    import numpy as np
    from PIL import Image

    gray = np.asarray(image.convert("L"))
    pieces = []
    for cell in cells:
        lines = _cell_lines(gray, cell)
        if len(lines) == 2:
            pieces.extend((cell, index, line) for index, line in enumerate(lines))

    # OCR a sheet of isolated lines in one call per batch.
    columns, tile_width, tile_height = 7, 165, 100
    recovered = defaultdict(list)
    for offset in range(0, len(pieces), 70):
        batch = pieces[offset:offset + 70]
        height = ((len(batch) + columns - 1) // columns) * tile_height
        sheet = np.full((height, columns * tile_width), 255, dtype=np.uint8)
        for index, (_, _, line) in enumerate(batch):
            scale = min(1.6, (tile_width - 30) / line.shape[1], (tile_height - 35) / line.shape[0])
            width, height = (max(1, round(size * scale)) for size in reversed(line.shape))
            resized = cv2.resize(line, (width, height), interpolation=cv2.INTER_CUBIC)
            y, x = (index // columns) * tile_height + 20, (index % columns) * tile_width + 15
            sheet[y:y + height, x:x + width] = resized
        for word in _ocr_words(Image.fromarray(sheet)):
            x0, y0, x1, y1, _ = word
            col = int((x0 + x1) / 2) // tile_width
            row = int((y0 + y1) / 2) // tile_height
            index = row * columns + col
            if index < len(batch):
                cell, line, _ = batch[index]
                recovered[cell, line].append(word)
    return {cell: " ".join(_text(recovered[cell, line]) for line in (0, 1))
            for cell, _, _ in pieces if recovered[cell, 0] and recovered[cell, 1]}


def _recover_compact_texts(image, cells, texts, saved_classes):
    labels, day_axis, compact = _day_labels(texts)
    if not compact:
        return texts
    headers = _headers(texts, labels, 1 - day_axis, day_axis)
    original = dict(texts)
    if len(labels) == 4 and headers:
        # A lone I can be dropped by OCR. Recover one missing day only when
        # a labelled header and all five weekday cells agree with the layout.
        anchor, _ = labels[0]
        lane = sorted((cell for cell in cells
                       if _intersects(_interval(cell, 1 - day_axis), _interval(anchor, 1 - day_axis))),
                      key=lambda cell: cell[day_axis])
        if len(lane) == 6 and re.search(r"\b(?:hari|day)\b", original.get(lane[0], ""), re.I):
            expected = list(zip(lane[1:], DAYS[:5], SHORT_DAYS))
            present = set(labels)
            missing = [(cell, short) for cell, day, short in expected if (cell, day) not in present]
            if len(missing) == 1:
                cell, short = missing[0]
                if len(original.get(cell, "")) <= 1:
                    original[cell] = short
                    labels, _, _ = _day_labels(list(original.items()))
    teaching = _teaching_cells(cells, labels, headers, day_axis)
    skipped = _break_cells(list(original.items()), labels, day_axis)
    candidates = [cell for cell in teaching if cell not in skipped
                  and not NON_TEACHING.search(original.get(cell, ""))]
    recovered = _ocr_cell_lines(image, candidates)
    for cell, text in recovered.items():
        before = _subject_class(original.get(cell, ""), saved_classes, compact=True)
        after = _subject_class(text, saved_classes, compact=True)
        if all(after) and not all(before):
            original[cell] = text
        elif cell not in original:
            # Retain detected but ambiguous text so review counts include it.
            original[cell] = text
    return list(original.items())


def _read_grid(texts, saved_classes):
    labels, day_axis, compact = _day_labels(texts)
    if not labels:
        return [], []
    time_axis = 1 - day_axis
    headers = _headers(texts, labels, time_axis, day_axis)
    if not headers:
        return [], []
    skipped = {cell for cell, _ in labels} | _break_cells(texts, labels, day_axis)
    entries, uncertain = [], []
    for cell, text in texts:
        if (cell in skipped or NON_TEACHING.search(text)
                or not any(c.isalpha() for c in text)):
            continue
        matching_days = [day for day_cell, day in labels
                         if _intersects(_interval(cell, day_axis), _interval(day_cell, day_axis))]
        spans = [(start, end) for span, start, end in headers
                 if _intersects(_interval(cell, time_axis), span)]
        if len(matching_days) != 1:
            continue
        day = matching_days[0]
        subject, class_name = _subject_class(text, saved_classes, compact)
        time_unclear = not spans or any(
            last_end != next_start for (_, last_end), (next_start, _) in zip(spans, spans[1:])
        )
        if time_unclear:
            if subject or class_name:
                uncertain.append(dict(day=day, start="", end="", reason="time"))
            continue
        start, end = spans[0][0], spans[-1][1]
        if not subject and not class_name:
            uncertain.append(dict(day=day, start=start, end=end, reason="details"))
            continue
        if not subject or not class_name:
            uncertain.append(dict(day=day, start=start, end=end, reason="review"))
        entries.append(dict(day=day, start=start, end=end,
                            class_name=class_name, subject=subject))
    return entries, uncertain


def _merge_adjacent(entries):
    merged = []
    for row in entries:
        if (merged and row["class_name"] and row["subject"] and merged[-1]["end"] == row["start"]
                and all(merged[-1][key] == row[key] for key in ("day", "class_name", "subject"))):
            merged[-1] = {**merged[-1], "end": row["end"]}
        else:
            merged.append(row)
    return merged


def read_timetable(data, saved_classes):
    """Return review rows plus counts of unreadable cells and pages."""
    import fitz
    from PIL import Image

    results, uncertain, unreadable_pages = {}, [], 0
    try:
        for page, (image, words) in enumerate(_pages(data), start=1):
            cells = _grid(image)
            entries, missed = _read_grid(_cell_texts(cells, words), saved_classes)
            if (not entries or missed) and cells:
                texts = _cell_texts(cells, _ocr_words(image))
                texts = _recover_compact_texts(image, cells, texts, saved_classes)
                ocr_entries, ocr_missed = _read_grid(texts, saved_classes)
                if (len(ocr_entries), -len(ocr_missed)) > (len(entries), -len(missed)):
                    entries, missed = ocr_entries, ocr_missed
            uncertain.extend(dict(cell, page=page) for cell in missed)
            if not entries:
                unreadable_pages += 1
            for entry in entries:
                results[tuple(entry.values())] = entry
    except (fitz.FileDataError, Image.DecompressionBombError, OSError) as exc:
        raise UnreadableTimetable("Fail jadual tidak dapat dibuka. Cuba simpan semula fail.") from exc
    if not results:
        raise UnreadableTimetable(
            "Tiada waktu dapat dibaca. Cuba gambar yang lebih rapat pada jadual, "
            "atau tekan + Tambah Waktu untuk isi slot secara manual."
        )
    entries = sorted(results.values(), key=lambda row: (DAYS.index(row["day"]), row["start"]))
    entries = _merge_adjacent(entries)
    if len(entries) > 80:
        raise UnreadableTimetable("Lebih daripada 80 waktu dikesan. Muat naik jadual untuk seorang guru.")
    uncertain.sort(key=lambda row: (row["page"], DAYS.index(row["day"]), row["start"]))
    return {"entries": entries, "uncertain": len(uncertain), "unreadable_pages": unreadable_pages,
            "unclear_cells": uncertain[:80]}
