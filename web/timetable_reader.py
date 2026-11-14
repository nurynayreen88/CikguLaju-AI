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
        if start < end:
            output.append((span, start, end))
    return output


def _class_key(value):
    return re.sub(r"[\W_]+", "", re.sub(r"^tahun\s*", "", value.casefold()))


def _subject_class(text, saved_classes):
    match = SUBJECT_PATTERN.search(text)
    if not match:
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
    subject = SUBJECTS[match[0].casefold()]
    name = (text[:match.start()] + " " + text[match.end():]).strip(" -/|:–—")
    name = " ".join(name.split())
    matching = [saved for saved in saved_classes if _class_key(saved) == _class_key(name)]
    if len(matching) == 1:
        return subject, matching[0]
    return subject, name if len(name) <= 40 and CLASS_PATTERN.fullmatch(name) else ""


def _read_grid(texts, saved_classes):
    labels = [(cell, DAY_LABELS[text.casefold().strip(" .:")]) for cell, text in texts
              if text.casefold().strip(" .:") in DAY_LABELS]
    if len({day for _, day in labels}) < 2:
        return [], 0
    x_centers = [(cell[0] + cell[2]) / 2 for cell, _ in labels]
    y_centers = [(cell[1] + cell[3]) / 2 for cell, _ in labels]
    day_axis = int(max(y_centers) - min(y_centers) > max(x_centers) - min(x_centers))
    time_axis = 1 - day_axis
    headers = _headers(texts, labels, time_axis, day_axis)
    if not headers:
        return [], 0
    entries, uncertain = [], 0
    for cell, text in texts:
        if (text.casefold().strip(" .:") in DAY_LABELS or NON_TEACHING.search(text)
                or not any(c.isalpha() for c in text)):
            continue
        matching_days = [day for day_cell, day in labels
                         if _intersects(_interval(cell, day_axis), _interval(day_cell, day_axis))]
        spans = [(start, end) for span, start, end in headers
                 if _intersects(_interval(cell, time_axis), span)]
        if len(matching_days) != 1:
            continue
        if not spans:
            # Count a teaching cell on the timetable band if its time heading
            # is missing. It must not disappear from the review summary.
            if _subject_class(text, saved_classes) != ("", ""):
                uncertain += 1
            continue
        if any(last_end != next_start for (_, last_end), (next_start, _) in zip(spans, spans[1:])):
            uncertain += 1
            continue
        subject, class_name = _subject_class(text, saved_classes)
        if not subject and not class_name:
            uncertain += 1
            continue
        entries.append(dict(day=matching_days[0], start=spans[0][0], end=spans[-1][1],
                            class_name=class_name, subject=subject))
    return entries, uncertain


def read_timetable(data, saved_classes):
    """Return review rows plus counts of unreadable cells and pages."""
    import fitz
    from PIL import Image

    results, uncertain, unreadable_pages = {}, 0, 0
    try:
        for image, words in _pages(data):
            cells = _grid(image)
            entries, missed = _read_grid(_cell_texts(cells, words), saved_classes)
            if (not entries or missed) and cells:
                ocr_entries, ocr_missed = _read_grid(_cell_texts(cells, _ocr_words(image)), saved_classes)
                if len(ocr_entries) > len(entries):
                    entries, missed = ocr_entries, ocr_missed
            uncertain += missed
            if not entries:
                unreadable_pages += 1
            for entry in entries:
                results[tuple(entry.values())] = entry
    except (fitz.FileDataError, Image.DecompressionBombError, OSError) as exc:
        raise UnreadableTimetable("Fail jadual tidak dapat dibuka. Cuba simpan semula fail.") from exc
    if len(results) > 80:
        raise UnreadableTimetable("Lebih daripada 80 waktu dikesan. Muat naik jadual untuk seorang guru.")
    if not results:
        raise UnreadableTimetable("Tiada waktu dapat dibaca. Gunakan jadual yang jelas dengan tajuk hari dan masa.")
    entries = sorted(results.values(), key=lambda row: (DAYS.index(row["day"]), row["start"]))
    return {"entries": entries, "uncertain": uncertain, "unreadable_pages": unreadable_pages}
